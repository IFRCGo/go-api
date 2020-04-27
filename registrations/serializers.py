from django.contrib.auth.models import User, Group
from rest_framework import serializers
from .models import DomainWhitelist


class DomainWhitelistSerializer(serializers.ModelSerializer):
    class Meta:
        model = DomainWhitelist
        fields = '__all__'
