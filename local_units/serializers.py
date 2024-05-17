import json

from rest_framework import serializers
from django.utils.translation import gettext
from django.contrib.gis.geos import Point

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
    GeneralMedicalService,
    SpecializedMedicalService,
)
from api.models import Country
from main.writable_nested_serializers import NestedCreateMixin, NestedUpdateMixin


class GeneralMedicalServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralMedicalService
        fields = "__all__"


class SpecializedMedicalServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecializedMedicalService
        fields = "__all__"


class AffiliationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Affiliation
        fields = "__all__"


class FunctionalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Functionality
        fields = "__all__"


class FacilityTypeSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = FacilityType
        fields = "__all__"

    def get_image_url(self, facility_type):
        code = facility_type.code
        if code and self.context and "request" in self.context:
            request = self.context["request"]
            return FacilityType.get_image_map(code, request)
        return None


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


class ProfessionalTrainingFacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalTrainingFacility
        fields = ('__all__')


class MiniHealthDataSerializer(
    serializers.ModelSerializer
):
    health_facility_type_details = FacilityTypeSerializer(source='health_facility_type', read_only=True)

    class Meta:
        model = HealthData
        fields = (
            'id',
            'health_facility_type',
            'health_facility_type_details',
        )


class HealthDataSerializer(
    NestedCreateMixin,
    NestedUpdateMixin,
):
    health_facility_type_details = FacilityTypeSerializer(source='health_facility_type', read_only=True)
    affiliation_details = AffiliationSerializer(source='affiliation', read_only=True)
    functionality_details = FunctionalitySerializer(source='functionality', read_only=True)
    primary_health_care_center_details = PrimaryHCCSerializer(
        source='primary_health_care_center',
        read_only=True
    )
    hospital_type_details = HospitalTypeSerializer(
        source='hospital_type',
        read_only=True
    )
    general_medical_services_details = GeneralMedicalServiceSerializer(
        source='general_medical_services',
        read_only=True,
        many=True
    )
    specialized_medical_beyond_primary_level_details = SpecializedMedicalServiceSerializer(
        source='specialized_medical_beyond_primary_level',
        read_only=True,
        many=True
    )
    blood_services_details = BloodServiceSerializer(
        source='blood_services',
        read_only=True,
        many=True,
    )
    professional_training_facilities_details = ProfessionalTrainingFacilitySerializer(
        source='professional_training_facilities',
        many=True,
        read_only=True
    )

    class Meta:
        model = HealthData
        fields = ('__all__')


class LocalUnitCountrySerializer(serializers.ModelSerializer):

    class Meta:
        model = Country
        fields = (
            'name', 'iso3', 'id'
        )


class LocalUnitTypeSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = LocalUnitType
        fields = (
            'name',
            'code',
            'id',
            'colour',
            'image_url',
        )

    def get_image_url(self, facility_type):
        code = facility_type.code
        if code and self.context and "request" in self.context:
            request = self.context["request"]
            return LocalUnitType.get_image_map(code, request)
        return None


class LocalUnitLevelSerializer(serializers.ModelSerializer):

    class Meta:
        model = LocalUnitLevel
        fields = (
            'name', 'level', 'id'
        )


class LocalUnitDetailSerializer(
    serializers.ModelSerializer
):
    country_details = LocalUnitCountrySerializer(source='country', read_only=True)
    type_details = LocalUnitTypeSerializer(source='type', read_only=True)
    level_details = LocalUnitLevelSerializer(source='level', read_only=True)
    health = HealthDataSerializer(required=False, allow_null=True)
    location_details = serializers.SerializerMethodField()
    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)
    validated = serializers.BooleanField(read_only=True)

    class Meta:
        model = LocalUnit
        fields = (
            'local_branch_name', 'english_branch_name', 'type', 'country',
            'created_at', 'modified_at', 'draft', 'validated', 'postcode',
            'address_loc', 'address_en', 'city_loc', 'city_en', 'link',
            'location', 'source_loc', 'source_en', 'subtype', 'date_of_data',
            'level', 'health', 'visibility_display', 'location_details', 'type_details',
            'level_details', 'country_details'
        )

    def get_location_details(self, unit) -> dict:
        return json.loads(unit.location.geojson)


class PrivateLocalUnitDetailSerializer(
    NestedCreateMixin,
    NestedUpdateMixin
):
    country_details = LocalUnitCountrySerializer(source='country', read_only=True)
    type_details = LocalUnitTypeSerializer(source='type', read_only=True)
    level_details = LocalUnitLevelSerializer(source='level', read_only=True)
    health = HealthDataSerializer(required=False, allow_null=True)
    location_details = serializers.SerializerMethodField()
    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)
    validated = serializers.BooleanField(read_only=True)
    location_json = serializers.JSONField(
        required=True,
        write_only=True
    )
    location = serializers.CharField(required=False)

    class Meta:
        model = LocalUnit
        fields = (
            'local_branch_name', 'english_branch_name', 'type', 'country',
            'created_at', 'modified_at', 'draft', 'validated', 'postcode',
            'address_loc', 'address_en', 'city_loc', 'city_en', 'link',
            'location', 'source_loc', 'source_en', 'subtype', 'date_of_data',
            'level', 'health', 'visibility_display', 'location_details', 'type_details',
            'level_details', 'country_details', 'focal_person_loc', 'focal_person_en',
            'email', 'phone', 'location_json', 'visibility',
        )

    def get_location_details(self, unit) -> dict:
        return json.loads(unit.location.geojson)

    def validate(self, data):
        local_branch_name = data.get('local_branch_name')
        english_branch_name = data.get('english_branch_name')
        if (not local_branch_name) or (not english_branch_name):
            raise serializers.ValidationError(
                gettext('Branch Name Combination is required !')
            )
        type = data.get('type')
        health = data.get('health')
        if type.code == 1 and health:
            raise serializers.ValidationError({
                'Can\'t have health data for type %s' % type.code
            })
        return data

    def create(self, validated_data):
        location_json = validated_data.pop('location_json')
        lat = location_json.get('lat')
        lon = location_json.get('lon')
        if not lat and not lon:
            raise serializers.ValidationError(
                gettext('Combination of lat/lon is required')
            )
        validated_data['location'] = Point(lon, lat)
        return super().create(validated_data)


class LocalUnitSerializer(
    serializers.ModelSerializer
):
    location_details = serializers.SerializerMethodField()
    country_details = LocalUnitCountrySerializer(source='country', read_only=True)
    type_details = LocalUnitTypeSerializer(source='type', read_only=True)
    health_details = MiniHealthDataSerializer(read_only=True, source='health')
    validated = serializers.BooleanField(read_only=True)

    class Meta:
        model = LocalUnit
        fields = (
            'id',
            'country',
            'local_branch_name',
            'english_branch_name',
            'location_details',
            'type',
            'validated',
            'address_loc',
            'address_en',
            'country_details',
            'type_details',
            'health',
            'health_details',
        )

    def get_location_details(self, unit) -> dict:
        return json.loads(unit.location.geojson)


class PrivateLocalUnitSerializer(
    serializers.ModelSerializer
):
    location_details = serializers.SerializerMethodField()
    country_details = LocalUnitCountrySerializer(source='country', read_only=True)
    type_details = LocalUnitTypeSerializer(source='type', read_only=True)
    health_details = MiniHealthDataSerializer(read_only=True, source='health')
    validated = serializers.BooleanField(read_only=True)

    class Meta:
        model = LocalUnit
        fields = (
            'id',
            'country',
            'local_branch_name',
            'english_branch_name',
            'location_details',
            'type',
            'validated',
            'address_loc',
            'address_en',
            'country_details',
            'type_details',
            'health',
            'health_details',
            'focal_person_loc',
            'focal_person_en',
            'email',
            'phone',
        )

    def get_location_details(self, unit) -> dict:
        return json.loads(unit.location.geojson)


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
    level = LocalUnitLevelSerializer(many=True)  # renaming level to coverage
    affiliation = AffiliationSerializer(many=True)
    functionality = FunctionalitySerializer(many=True)
    health_facility_type = FacilityTypeSerializer(many=True)
    primary_health_care_center = PrimaryHCCSerializer(many=True)
    hospital_type = HospitalTypeSerializer(many=True)
    blood_services = BloodServiceSerializer(many=True)
    professional_training_facilities = ProfessionalTrainingFacilitySerializer(many=True)
    general_medical_services = GeneralMedicalServiceSerializer(many=True)
    specialized_medical_services = SpecializedMedicalServiceSerializer(many=True)


class MiniDelegationOfficeSerializer(serializers.ModelSerializer):
    dotype_name = serializers.CharField(source='dotype.name', read_only=True)

    class Meta:
        model = DelegationOffice
        fields = (
            'hod_first_name',
            'hod_last_name',
            'hod_mobile_number',
            'hod_email',
            'dotype_name'
        )
