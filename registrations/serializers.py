from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers
from .models import DomainWhitelist, Recovery
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.db import transaction

from rest_framework import serializers

from .models import DomainWhitelist, Pending
from .utils import (
    is_valid_domain,
    send_notification_create
)
from api.models import Country


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
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=255, write_only=True)
    first_name = serializers.CharField(max_length=255, write_only=True)
    last_name = serializers.CharField(max_length=255, write_only=True)
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), write_only=True)
    organization_type = serializers.CharField(max_length=255, write_only=True)
    organization = serializers.CharField(max_length=255, write_only=True)
    justification = serializers.CharField(max_length=255, write_only=True)
    city = serializers.CharField(max_length=255, write_only=True)

    # optional fields
    department = serializers.CharField(required=False, max_length=255, write_only=True)
    position = serializers.CharField(required=False, max_length=255, write_only=True)
    phone_number = serializers.CharField(required=False, max_length=255, write_only=True)

    def validate_email(self, email) -> str:
        if User.objects.filter(username__iexact=email).exists():
            raise serializers.ValidationError('A user with that email address already exists.')
        return email

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
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password,
                is_active=False
            )
        except Exception:
            raise serializers.ValidationError('Could not create user.')

        try:
            user.profile.country = country
            user.profile.org_type = organization_type
            user.profile.org = organization
            user.profile.city = city
            user.profile.department = department
            user.profile.position = position
            user.profile.phone_number = phone_number
            user.profile.save()
        except Exception:
            raise serializers.ValidationError('Could not create user profile.')

        pending = Pending(
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
