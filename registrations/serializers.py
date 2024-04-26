from datetime import timedelta
from django.contrib.auth.password_validation import validate_password
from django.conf import settings

from rest_framework import serializers
from .models import DomainWhitelist, Recovery, UserExternalToken
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.db import transaction

from rest_framework import serializers

from .models import DomainWhitelist, Pending
from .utils import (
    is_valid_domain,
    jwt_encode_handler
)
from registrations.tasks import send_notification_create

from api.models import Country


class DomainWhitelistSerializer(serializers.ModelSerializer):
    class Meta:
        model = DomainWhitelist
        fields = '__all__'


class ChangeRecoverPasswordSerializer(serializers.Serializer):
    username = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField()

    def validate_new_password(self, new_password):
        validate_password(new_password)
        return new_password

    def validate(self, data):
        username = data['username']
        token = data['token']
        data['user'] = user = User.objects.filter(username__iexact=username).first()

        recovery = Recovery.objects.filter(user=user).first()
        if recovery is None:
            raise serializers.ValidationError("Could not authenticate")

        if recovery.token != token:
            return serializers.ValidationError("Could not authenticate")
        recovery.delete()
        return data

    def save(self):
        self.is_valid(raise_exception=True)
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate_old_password(self, password):
        user = self.context['request'].user
        if not user.check_password(password):
            raise serializers.ValidationError('Invalid Old Password')
        return password

    def validate_new_password(self, password):
        validate_password(password)
        return password

    def save(self):
        self.is_valid(raise_exception=True)
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
    city = serializers.CharField(max_length=255, write_only=True)

    # optional fields
    department = serializers.CharField(required=False, max_length=255, write_only=True)
    position = serializers.CharField(required=False, max_length=255, write_only=True)
    phone_number = serializers.CharField(required=False, max_length=255, write_only=True)
    justification = serializers.CharField(max_length=255, write_only=True, required=False)

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

        justification = self.validated_data.get('justification')
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

class UserExternalTokenSerializer(serializers.ModelSerializer):
    token = serializers.CharField(read_only=True)
    expire_timestamp = serializers.DateTimeField(required=False)
    class Meta:
        model = UserExternalToken
        fields = ['title', 'token', 'expire_timestamp']

    def validate_expire_timestamp(self, date):
        now = timezone.now()
        if date < now:
            raise serializers.ValidationError('Expire timestamp must be in the future.')
        elif date > now + timedelta(days=settings.JWT_EXPIRE_TIMESTAMP_DAYS):
            raise serializers.ValidationError(f'Expire timestamp must be less than {settings.JWT_EXPIRE_TIMESTAMP_DAYS} days.')
        return date

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user

        # @Note: Not in use for now
        # if not user.profile.accepted_montandon_license_terms:
        #     raise serializers.ValidationError('User must accept Montandon license terms.')

        if not validated_data.get('expire_timestamp'):
            validated_data['expire_timestamp'] = timezone.now() + timedelta(days=settings.JWT_EXPIRE_TIMESTAMP_DAYS)
        
        # Check if private and public key exists
        if not(settings.JWT_PRIVATE_KEY and settings.JWT_PUBLIC_KEY):
            raise serializers.ValidationError('Please contact system adminstrators to configurate private and public key.')

        instance = super().create(validated_data)
        validated_data["token"] = jwt_encode_handler(instance.get_payload())
        return validated_data
    

    def update(self, instance, validated_data):
        raise serializers.ValidationError("Update is not allowed")
