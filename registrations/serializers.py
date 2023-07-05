from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers
from .models import DomainWhitelist, Recovery
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.db import transaction

from rest_framework import serializers

from .models import DomainWhitelist, Pending
from .utils import (
    create_inactive_user,
    set_user_profile,
    is_valid_domain,
    send_notification_create
)


class DomainWhitelistSerializer(serializers.ModelSerializer):
    class Meta:
        model = DomainWhitelist
        fields = '__all__'


class ChangePasswordSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    new_password = serializers.CharField()
    token = serializers.CharField()

    def validate_password(self, password):
        user = self.context['request'].user
        if not user.check_password(password):
            raise serializers.ValidationError('Invalid Old Password')
        return password

    def validate_new_password(self, new_password):
        validate_password(new_password)
        return new_password

    def validate_token(self, token):
        user = self.context['request'].user
        recovery = Recovery.objects.filter(user=user).first()
        if recovery is None:
            raise serializers.ValidationError("Could not authenticate")

        if recovery.token != token:
            return serializers.ValidationError("Could not authenticate")
        recovery.delete()

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()


class RegistrationSerializer(serializers.Serializer):
    # required fields
    email = serializers.CharField()
    password = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    country = serializers.IntegerField()
    organization_type = serializers.CharField()
    organization = serializers.CharField()
    justification = serializers.CharField()
    city = serializers.CharField()

    # optional fields
    department = serializers.CharField(required=False)
    position = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)

    def validate_email(self, email) -> str:
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('A user with that email address already exists.')
        return email


    def validate(self, attrs):
        username = attrs['email']
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError(
                {
                    'username' : 'That username is taken, please choose a different one.'
                }
            )
        if ' ' in username:
            raise serializers.ValidationError(
                {
                    'username' : 'Username can not contain spaces, please choose a different one.'
                }
            )
        return attrs

    def save(self):
        # using email as username for user registration
        username = self.validated_data['email']
        first_name = self.validated_data['first_name']
        last_name = self.validated_data['last_name']
        email = self.validated_data['email']
        password = self.validated_data['password']
        country = self.validated_data['country']
        organization = self.validated_data['organization']
        organization_type = self.validated_data['organization_type']
        city = self.validated_data['city']
        justification = self.validated_data['justification']

        department = self.validated_data.get('department')
        position = self.validated_data.get('position')
        phone_number = self.validated_data.get('phone_number')

        is_staff = is_valid_domain(email)

        # Create the User object
        try:
            user = create_inactive_user(username, first_name, last_name, email, password)
        except Exception:
            raise serializers.ValidationError('Could not create user.')

        try:
            set_user_profile(
                user,
                country,
                organization_type,
                organization,
                city,
                department,
                position,
                phone_number
            )
        except Exception:
            User.objects.filter(username=username).delete()
            return serializers.ValidationError('Could not create user profile.')

        pending = Pending.objects.create(
            user=user,
            justification=justification,
            token=get_random_string(length=32)
        )
        if not is_staff:
            pending.admin_token_1 = get_random_string(length=32)
        pending.save()

        # send notification
        transaction.on_commit(
            lambda: send_notification_create.delay(
                pending.token,
                username,
                is_staff,
                email
            )
        )
