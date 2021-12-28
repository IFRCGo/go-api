from django.utils.translation import ugettext

from rest_framework import serializers

from lang.serializers import ModelSerializer
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


class InformalGraphicMapSerializer(ModelSerializer):
    created_by_details = UserNameSerializer(source='created_by', read_only=True)

    class Meta:
        model = InformalGraphicMap
        fields = '__all__'
        read_only_fields = ('created_by',)

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class InformalActionSerializer(ModelSerializer):
    class Meta:
        model = InformalAction
        fields = ('name', 'id', 'organizations', 'field_report_types', 'category', 'tooltip_text')


class InformalActionsTakenSerializer(ModelSerializer):
    actions = InformalActionSerializer(many=True)

    class Meta:
        model = InformalActionsTaken
        fields = ('organization', 'actions', 'summary', 'id',)


class InformalReferenceUrls(ModelSerializer):
    class Meta:
        model = ReferenceUrls
        fields = '__all__'


class InformalReferencesSerializer(ModelSerializer):
    url = InformalReferenceUrls(many=True)

    class Meta:
        model = InformalReferences
        fields = '__all__'


class InformalCountryDistrictSerializer(ModelSerializer):
    country_details = CountrySerializer(source='country', read_only=True)
    district_details = MiniDistrictSerializer(source='district', read_only=True, many=True)

    class Meta:
        model = InformalCountryDistrict
        fields = ('id', 'country', 'district', 'country_details', 'district_details')
        read_only_fields = ('informal_update',)

    def validate(sel, data):
        districts = data['district']
        if isinstance(districts, list) and len(districts):
            for district in districts:
                if district.country != data['country']:
                    raise serializers.ValidationError({
                        'district': ugettext('Different districts found for given country')
                    })
        return data


class InformalUpdateSerializer(
    EnumSupportSerializerMixin,
    NestedUpdateMixin,
    NestedCreateMixin,
    ModelSerializer
):
    country_district = InformalCountryDistrictSerializer(source='informalupdatecountrydistrict_set', many=True, required=False)
    references = InformalReferencesSerializer(many=True, required=False)
    actions_taken = InformalActionsTakenSerializer(many=True)
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
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['modified_by'] = self.context['request'].user
        return super().update(instance, validated_data)