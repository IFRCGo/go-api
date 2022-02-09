from django.db import transaction
from django.utils.translation import ugettext

from rest_framework import serializers

from enumfields.drf.serializers import EnumSupportSerializerMixin
from .utils import send_email_when_informal_update_created

from api.serializers import (
    UserNameSerializer,
    DisasterTypeSerializer,
    CountrySerializer,
    MiniDistrictSerializer,
)
from informal_update.models import (
    InformalReferences,
    InformalUpdate,
    InformalCountryDistrict,
    InformalGraphicMap,
    InformalAction,
    InformalActionsTaken
)

from main.writable_nested_serializers import (
    NestedCreateMixin,
    NestedUpdateMixin
)


class InformalGraphicMapSerializer(serializers.ModelSerializer):
    created_by_details = UserNameSerializer(source='created_by', read_only=True)
    file = serializers.FileField(required=False)

    class Meta:
        model = InformalGraphicMap
        fields = '__all__'
        read_only_fields = ('created_by',)

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class InformalActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InformalAction
        fields = ('name', 'id', 'organizations', 'category', 'tooltip_text', 'client_id')


class InformalActionsTakenSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer
):
    action_details = InformalActionSerializer(source='actions', many=True, required=False, read_only=True)
    organization_display = serializers.CharField(source='get_organization_display', read_only=True)

    class Meta:
        model = InformalActionsTaken
        fields = ('organization', 'organization_display', 'actions', 'action_details', 'summary', 'id', 'client_id')
        read_only_fields = ('informal_update',)


class InformalReferencesSerializer(
    serializers.ModelSerializer
):
    document_details = InformalGraphicMapSerializer(source='document', read_only=True)

    class Meta:
        model = InformalReferences
        fields = '__all__'


class InformalCountryDistrictSerializer(serializers.ModelSerializer):
    country_details = CountrySerializer(source='country', read_only=True)
    district_details = MiniDistrictSerializer(source='district', read_only=True)

    class Meta:
        model = InformalCountryDistrict
        fields = ('id', 'country', 'district', 'country_details', 'district_details', 'client_id')
        read_only_fields = ('informal_update',)

    def validate(self, data):
        district = data['district']
        if district and district.country != data['country']:
            raise serializers.ValidationError({
                'district': ugettext('Different districts found for given country')
            })
        return data


class InformalUpdateSerializer(
    EnumSupportSerializerMixin,
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer,
):
    country_district = InformalCountryDistrictSerializer(source='informalcountrydistrict_set', many=True, required=False)
    references = InformalReferencesSerializer(many=True, required=False)
    actions_taken = InformalActionsTakenSerializer(source='actions_taken_informal', many=True, required=False)
    created_by_details = UserNameSerializer(source='created_by', read_only=True)
    hazard_type_details = DisasterTypeSerializer(source='hazard_type', read_only=True)
    share_with_display = serializers.CharField(source='get_share_with_display', read_only=True)
    map_files = InformalGraphicMapSerializer(source='map', many=True, required=False)
    graphics_files = InformalGraphicMapSerializer(source='graphics', many=True, required=False)

    class Meta:
        model = InformalUpdate
        fields = '__all__'

    def validate_country_district(self, attrs):
        if len(attrs) > 10:
            raise serializers.ValidationError("Number of countries selected should be less than 10")

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        informal_update = super().create(validated_data)
        transaction.on_commit(lambda: send_email_when_informal_update_created(informal_update))
        return informal_update

    def update(self, instance, validated_data):
        validated_data['modified_by'] = self.context['request'].user
        return super().update(instance, validated_data)
