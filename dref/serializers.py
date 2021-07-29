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

    class Meta:
        model = Dref
        fields = '__all__'
