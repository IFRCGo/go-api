from rest_framework import serializers

from lang.serializers import ModelSerializer
from enumfields.drf.serializers import EnumSupportSerializerMixin
from dref.writable_nested_serializers import (
    NestedCreateMixin,
    NestedUpdateMixin
)
from dref.models import (
    Dref,
    PlannedIntervention,
    NationalSocietyAction,
    IdentifiedNeed,
    DrefCountryDistrict
)


class PlannedInterventionSerializer(ModelSerializer):

    class Meta:
        model = PlannedIntervention
        fields = '__all__'


class NationalSocietyActionSerializer(ModelSerializer):

    class Meta:
        model = NationalSocietyAction
        fields = '__all__'


class IdentifiedNeedSerializer(ModelSerializer):
    class Meta:
        model = IdentifiedNeed
        fields = '__all__'


class DrefCountryDistrictSerializer(ModelSerializer):
    class Meta:
        model = DrefCountryDistrict
        fields = ('id', 'country', 'district')
        read_only_fields = ('dref',)


class DrefSerializer(
    EnumSupportSerializerMixin,
    NestedUpdateMixin,
    NestedCreateMixin,
    ModelSerializer
):
    country_district = DrefCountryDistrictSerializer(source='drefcountrydistrict_set', many=True, required=False)
    national_society_actions = NationalSocietyActionSerializer(many=True, required=False)
    needs_identified = IdentifiedNeedSerializer(many=True, required=False)
    planned_interventions = PlannedInterventionSerializer(many=True, required=False)
    type_of_onset_display = serializers.CharField(source='get_type_of_onset_display', read_only=True)
    disaster_category_level_display = serializers.CharField(source='get_disaster_category_level_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Dref
        fields = '__all__'
