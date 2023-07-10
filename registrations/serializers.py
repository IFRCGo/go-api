from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers
from .models import DomainWhitelist, Recovery


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
