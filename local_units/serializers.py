import json
from rest_framework import serializers

from .models import (
    HealthData,
    LocalUnit,
    LocalUnitType,
    LocalUnitLevel,
    DelegationOffice,
    DelegationOfficeType,
    Affiliation,
    Functionality,
    FacilityType,
    PrimaryHCC,
    HospitalType,
    BloodService,
    ProfessionalTrainingFacility,
)
from api.models import Country


class AffiliationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Affiliation
        fields = "__all__"


class FunctionalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Functionality
        fields = "__all__"


class FacilityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilityType
        fields = "__all__"


class PrimaryHCCSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrimaryHCC
        fields = "__all__"


class HospitalTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalType
        fields = "__all__"


class BloodServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodService
        fields = "__all__"


class HealthDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = HealthData
        fields = ('__all__')


class ProfessionalTrainingFacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalTrainingFacility
        fields = ('__all__')


class LocalUnitCountrySerializer(serializers.ModelSerializer):

    class Meta:
        model = Country
        fields = (
            'name', 'iso3'
        )


class LocalUnitTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = LocalUnitType
        fields = (
            'name', 'code', 'id'
        )


class LocalUnitLevelSerializer(serializers.ModelSerializer):

    class Meta:
        model = LocalUnitLevel
        fields = (
            'name', 'level', 'id'
        )


class LocalUnitSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()
    country = LocalUnitCountrySerializer()
    type = LocalUnitTypeSerializer()
    coverage = LocalUnitLevelSerializer(source='level')  # renaming level to coverage
    health = HealthDataSerializer()

    class Meta:
        model = LocalUnit
        fields = [
            'local_branch_name', 'english_branch_name', 'type', 'country',
            'created_at', 'modified_at', 'draft', 'validated', 'postcode',
            'address_loc', 'address_en', 'city_loc', 'city_en', 'link',
            'location', 'source_loc', 'source_en', 'subtype', 'date_of_data',
            'coverage', 'health'
        ]
        # Hiding following fields for now
        # ['focal_person_loc', 'focal_person_en', 'email', 'phone',]

    def get_location(self, unit):
        return json.loads(unit.location.geojson)

    def get_country(self, unit):
        return {'country'}

    def get_type(self, unit):
        return {'type'}


class DelegationOfficeCountrySerializer(serializers.ModelSerializer):

    class Meta:
        model = Country
        fields = (
            'name', 'iso3', 'region', 'region'
        )


class DelegationOfficeTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = DelegationOfficeType
        fields = (
            'name', 'code'
        )


class DelegationOfficeSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()
    country = DelegationOfficeCountrySerializer()
    dotype = DelegationOfficeTypeSerializer()

    class Meta:
        model = DelegationOffice
        fields = [
            'name',
            'city',
            'address',
            'postcode',
            'location',
            'society_url',
            'url_ifrc',
            'hod_first_name',
            'hod_last_name',
            'hod_mobile_number',
            'hod_email',
            'assistant_name',
            'assistant_email',
            'is_ns_same_location',
            'is_multiple_ifrc_offices',
            'visibility',
            'created_at',
            'modified_at',
            'date_of_data',
            'country',
            'dotype']

    def get_location(self, office):
        return json.loads(office.location.geojson)

    def get_country(self, office):
        return {'country'}

    def get_type(self, office):
        return {'type'}


class LocalUnitOptionsSerializer(serializers.Serializer):
    type = LocalUnitTypeSerializer(many=True)
    coverage = LocalUnitLevelSerializer(many=True, source='level')  # renaming level to coverage
    affiliation = AffiliationSerializer(many=True)
    functionality = FunctionalitySerializer(many=True)
    health_facility_type = FacilityTypeSerializer(many=True)
    primary_health_care_center = PrimaryHCCSerializer(many=True)
    hospital_type = HospitalTypeSerializer(many=True)
    blood_services = BloodServiceSerializer(many=True)
    professional_training_facilities = ProfessionalTrainingFacilitySerializer(many=True)


class MiniDelegationOfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DelegationOffice
        fields = (
            'hod_first_name',
            'hod_last_name',
            'hod_mobile_number',
            'hod_email',
        )
