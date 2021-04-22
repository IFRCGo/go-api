from rest_framework import serializers
from enumfields.drf.serializers import EnumSupportSerializerMixin

from api.serializers import MiniEventSerializer, ListEventSerializer, MiniCountrySerializer
from lang.serializers import ModelSerializer

from .models import SurgeAlert, Subscription
from deployments.serializers import MolnixTagSerializer


class SurgeAlertSerializer(EnumSupportSerializerMixin, ModelSerializer):
    event = ListEventSerializer()
    atype_display = serializers.CharField(source='get_atype_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    molnix_tags = MolnixTagSerializer(many=True, read_only=True)

    class Meta:
        model = SurgeAlert
        fields = (
            'operation', 'message', 'deployment_needed', 'is_private', 'event', 'created_at', 'id',
            'atype', 'atype_display', 'category', 'category_display', 'molnix_id', 'molnix_tags',
            'opens', 'closes', 'start', 'end', 'is_active',
        )


class UnauthenticatedSurgeAlertSerializer(EnumSupportSerializerMixin, ModelSerializer):
    event = MiniEventSerializer()
    atype_display = serializers.CharField(source='get_atype_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = SurgeAlert
        fields = (
            'operation', 'deployment_needed', 'is_private', 'event', 'created_at', 'id',
            'atype', 'atype_display', 'category', 'category_display', 'is_active',
        )


class SubscriptionSerializer(EnumSupportSerializerMixin, ModelSerializer):
    country = MiniCountrySerializer()
    event = MiniEventSerializer()
    stype_display = serializers.CharField(source='get_stype_display', read_only=True)
    rtype_display = serializers.CharField(source='get_rtype_display', read_only=True)

    class Meta:
        model = Subscription
        fields = (
            'user', 'country', 'region', 'event', 'dtype', 'lookup_id',
            'stype', 'stype_display', 'rtype', 'rtype_display',
        )
