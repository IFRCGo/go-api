from django.utils.translation import ugettext

from rest_framework import serializers

from enumfields.drf.serializers import EnumSupportSerializerMixin

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
    InformalActionsTaken,
    ReferenceUrls,
)

from informal_update.writable_nested_serializers import (
    NestedCreateMixin,
    NestedUpdateMixin
)

from lang.serializers import ModelSerializer


class InformalGraphicMapSerializer(serializers.ModelSerializer):
    created_by_details = UserNameSerializer(source='created_by', read_only=True)

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
        fields = ('name', 'id', 'organizations', 'category', 'tooltip_text')


class InformalActionsTakenSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer
):
    actions = InformalActionSerializer(many=True)
    organization_display = serializers.CharField(source='get_organization_display', read_only=True)

    class Meta:
        model = InformalActionsTaken
        fields = ('organization', 'organization_display', 'actions', 'summary', 'id',)
        read_only_fields = ('informal_update',)


class InformalReferenceUrls(serializers.ModelSerializer):
    class Meta:
        model = ReferenceUrls
        fields = '__all__'


class InformalReferencesSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer
):
    url = InformalReferenceUrls(many=True)
    document_details = InformalGraphicMapSerializer(source='document', read_only=True)

    class Meta:
        model = InformalReferences
        fields = '__all__'


class InformalCountryDistrictSerializer(serializers.ModelSerializer):
    country_details = CountrySerializer(source='country', read_only=True)
    district_details = MiniDistrictSerializer(source='district', read_only=True)

    class Meta:
        model = InformalCountryDistrict
        fields = ('id', 'country', 'district', 'country_details', 'district_details')
        read_only_fields = ('informal_update',)

    def validate(sel, data):
        if len(data) > 10:
            raise serializers.ValidationError("Number of countries selected should be less than 10")
        district = data['district']
        if district:
            if district.country != data['country']:
                raise serializers.ValidationError({
                    'district': ugettext('Different districts found for given country')
                })
        return data


class InformalUpdateSerializer(
    EnumSupportSerializerMixin,
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer
):
    country_district = InformalCountryDistrictSerializer(source='informalcountrydistrict_set', many=True, required=False)
    references = InformalReferencesSerializer(many=True, required=False)
    actions_taken = InformalActionsTakenSerializer(source='actions_taken_informal', many=True, required=False)
    created_by_details = UserNameSerializer(source='created_by', read_only=True)
    hazard_type_details = DisasterTypeSerializer(source='hazard_type', read_only=True)
    share_with_display = serializers.CharField(source='get_share_with_display', read_only=True)
    map_details = InformalGraphicMapSerializer(source='map', read_only=True)
    graphics_details = InformalGraphicMapSerializer(source='graphics', read_only=True)

    class Meta:
        model = InformalUpdate
        fields = '__all__'

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        response = super().create(validated_data)
        return response

    def update(self, instance, validated_data):
        validated_data['modified_by'] = self.context['request'].user
        return super().update(instance, validated_data)
