from rest_framework import serializers
from api.serializers import MiniEventSerializer, ListEventSerializer, MiniCountrySerializer
from lang.serializers import ModelSerializer

from .models import SurgeAlert, Subscription


class SurgeAlertSerializer(ModelSerializer):
    event = ListEventSerializer()

    class Meta:
        model = SurgeAlert
        fields = ('atype', 'category', 'operation', 'message', 'deployment_needed', 'is_private', 'event', 'created_at', 'id',)


class UnauthenticatedSurgeAlertSerializer(serializers.ModelSerializer):
    event = MiniEventSerializer()

    class Meta:
        model = SurgeAlert
        fields = ('atype', 'category', 'operation', 'deployment_needed', 'is_private', 'event', 'created_at', 'id',)


class SubscriptionSerializer(serializers.ModelSerializer):
    country = MiniCountrySerializer()
    event = MiniEventSerializer()

    class Meta:
        model = Subscription
        fields = ('user', 'stype', 'rtype', 'country', 'region', 'event', 'dtype', 'lookup_id',)
