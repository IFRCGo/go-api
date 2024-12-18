import json

import reversion
from django.contrib.auth.models import User
from django.contrib.gis.geos import GEOSGeometry
from django.utils.translation import gettext
from rest_framework import serializers
from reversion.models import Version
from shapely.geometry import MultiPolygon, Point, Polygon

from api.models import Country
from main.writable_nested_serializers import NestedCreateMixin, NestedUpdateMixin

from .models import (
    Affiliation,
    BloodService,
    DelegationOffice,
    DelegationOfficeType,
    FacilityType,
    Functionality,
    GeneralMedicalService,
    HealthData,
    HospitalType,
    LocalUnit,
    LocalUnitChangeRequest,
    LocalUnitLevel,
    LocalUnitType,
    PrimaryHCC,
    ProfessionalTrainingFacility,
    SpecializedMedicalService,
)


class LocationSerializer(serializers.Serializer):
    lat = serializers.FloatField(required=True)
    lng = serializers.FloatField(required=True)


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
        fields = "__all__"


class MiniHealthDataSerializer(serializers.ModelSerializer):
    health_facility_type_details = FacilityTypeSerializer(source="health_facility_type", read_only=True)

    class Meta:
        model = HealthData
        fields = (
            "id",
            "health_facility_type",
            "health_facility_type_details",
        )


class LocalUnitMiniUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")


class HealthDataSerializer(
    NestedCreateMixin,
    NestedUpdateMixin,
):
    health_facility_type_details = FacilityTypeSerializer(source="health_facility_type", read_only=True)
    affiliation_details = AffiliationSerializer(source="affiliation", read_only=True)
    functionality_details = FunctionalitySerializer(source="functionality", read_only=True)
    primary_health_care_center_details = PrimaryHCCSerializer(source="primary_health_care_center", read_only=True)
    hospital_type_details = HospitalTypeSerializer(source="hospital_type", read_only=True)
    general_medical_services_details = GeneralMedicalServiceSerializer(
        source="general_medical_services", read_only=True, many=True
    )
    specialized_medical_beyond_primary_level_details = SpecializedMedicalServiceSerializer(
        source="specialized_medical_beyond_primary_level", read_only=True, many=True
    )
    blood_services_details = BloodServiceSerializer(
        source="blood_services",
        read_only=True,
        many=True,
    )
    professional_training_facilities_details = ProfessionalTrainingFacilitySerializer(
        source="professional_training_facilities", many=True, read_only=True
    )
    modified_by_details = LocalUnitMiniUserSerializer(source="modified_by", read_only=True)
    created_by_details = LocalUnitMiniUserSerializer(source="created_by", read_only=True)

    class Meta:
        model = HealthData
        fields = "__all__"

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["modified_by"] = self.context["request"].user
        return super().update(instance, validated_data)


class LocalUnitCountrySerializer(serializers.ModelSerializer):

    class Meta:
        model = Country
        fields = ("name", "iso3", "id")


class LocalUnitTypeSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = LocalUnitType
        fields = (
            "name",
            "code",
            "id",
            "colour",
            "image_url",
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
        fields = ("name", "level", "id")


class LocalUnitDetailSerializer(serializers.ModelSerializer):
    country_details = LocalUnitCountrySerializer(source="country", read_only=True)
    type_details = LocalUnitTypeSerializer(source="type", read_only=True)
    level_details = LocalUnitLevelSerializer(source="level", read_only=True)
    health = HealthDataSerializer(required=False, allow_null=True)
    location_geojson = serializers.SerializerMethodField()
    visibility_display = serializers.CharField(source="get_visibility_display", read_only=True)
    validated = serializers.BooleanField(read_only=True)

    class Meta:
        model = LocalUnit
        fields = (
            "local_branch_name",
            "english_branch_name",
            "type",
            "country",
            "created_at",
            "modified_at",
            "draft",
            "validated",
            "postcode",
            "address_loc",
            "address_en",
            "city_loc",
            "city_en",
            "link",
            "location",
            "source_loc",
            "source_en",
            "subtype",
            "date_of_data",
            "level",
            "health",
            "visibility_display",
            "location_geojson",
            "type_details",
            "level_details",
            "country_details",
        )

    def get_location_geojson(self, unit) -> dict:
        return json.loads(unit.location.geojson)


"""
NOTE: This `PrivateLocalUnitDetailSerializer` is used to store the previous_data of local unit
changing the serializer might effect the data of previous_data
"""


class PrivateLocalUnitDetailSerializer(NestedCreateMixin, NestedUpdateMixin):
    country_details = LocalUnitCountrySerializer(source="country", read_only=True)
    type_details = LocalUnitTypeSerializer(source="type", read_only=True)
    level_details = LocalUnitLevelSerializer(source="level", read_only=True)
    health = HealthDataSerializer(required=False, allow_null=True)
    # NOTE: location_geojson contains the geojson of the location
    location_geojson = serializers.SerializerMethodField(read_only=True)
    visibility_display = serializers.CharField(source="get_visibility_display", read_only=True)
    validated = serializers.BooleanField(read_only=True)
    location_json = LocationSerializer(required=True)
    location = serializers.CharField(required=False)
    modified_by_details = LocalUnitMiniUserSerializer(source="modified_by", read_only=True)
    created_by_details = LocalUnitMiniUserSerializer(source="created_by", read_only=True)
    version_id = serializers.SerializerMethodField()
    is_locked = serializers.BooleanField(read_only=True)

    class Meta:
        model = LocalUnit
        fields = (
            "id",
            "local_branch_name",
            "english_branch_name",
            "type",
            "country",
            "created_at",
            "modified_at",
            "modified_by",
            "draft",
            "validated",
            "postcode",
            "address_loc",
            "address_en",
            "city_loc",
            "city_en",
            "link",
            "location",
            "source_loc",
            "source_en",
            "subtype",
            "date_of_data",
            "level",
            "health",
            "visibility_display",
            "location_geojson",
            "type_details",
            "level_details",
            "country_details",
            "focal_person_loc",
            "focal_person_en",
            "email",
            "phone",
            "location_json",
            "visibility",
            "modified_by_details",
            "created_by_details",
            "version_id",
            "is_locked",
        )

    def get_location_geojson(self, unit) -> dict:
        return json.loads(unit.location.geojson)

    def get_version_id(self, resource):
        # TODO: Add this as global method
        if not reversion.is_registered(resource.__class__):
            return None
        version_id = Version.objects.get_for_object(resource).count()

        request = self.context["request"]
        if request.method in ["POST", "PUT", "PATCH"]:
            if not (request.method == "POST" and self.context.get("post_is_used_for_filter", False)):
                version_id += 1
        return version_id

    def validate(self, data):
        local_branch_name = data.get("local_branch_name")
        english_branch_name = data.get("english_branch_name")
        if (not local_branch_name) and (not english_branch_name):
            raise serializers.ValidationError(gettext("Branch Name Combination is required !"))
        type = data.get("type")
        health = data.get("health")
        if type.code == 1 and health:
            raise serializers.ValidationError({"Can't have health data for type %s" % type.code})
        return data

    def create(self, validated_data):
        country = validated_data.get("country")
        location_json = validated_data.pop("location_json")
        lat = location_json.get("lat")
        lng = location_json.get("lng")
        input_point = Point(lng, lat)
        if country.bbox:
            country_json = json.loads(country.countrygeoms.geom.geojson)
            coordinates = country_json["coordinates"]
            # Convert to Shapely Polygons
            polygons = []
            for polygon_coords in coordinates:
                exterior = polygon_coords[0]
                interiors = polygon_coords[1:] if len(polygon_coords) > 1 else []
                polygon = Polygon(exterior, interiors)
                polygons.append(polygon)

            # Create a Shapely MultiPolygon
            shapely_multipolygon = MultiPolygon(polygons)
            if not input_point.within(shapely_multipolygon):
                raise serializers.ValidationError(
                    {"location_json": gettext("Input coordinates is outside country %s boundary" % country.name)}
                )
        validated_data["location"] = GEOSGeometry("POINT(%f %f)" % (lng, lat))
        validated_data["created_by"] = self.context["request"].user
        validated_data["is_locked"] = True
        return super().create(validated_data)

    def update(self, instance, validated_data):
        country = instance.country
        location_json = validated_data.pop("location_json")
        lat = location_json.get("lat")
        lng = location_json.get("lng")
        input_point = Point(lng, lat)
        if country.bbox:
            country_json = json.loads(country.countrygeoms.geom.geojson)
            coordinates = country_json["coordinates"]
            # Convert to Shapely Polygons
            polygons = []
            for polygon_coords in coordinates:
                exterior = polygon_coords[0]
                interiors = polygon_coords[1:] if len(polygon_coords) > 1 else []
                polygon = Polygon(exterior, interiors)
                polygons.append(polygon)

            # Create a Shapely MultiPolygon
            shapely_multipolygon = MultiPolygon(polygons)
            if not input_point.within(shapely_multipolygon):
                raise serializers.ValidationError(
                    {"location_json": gettext("Input coordinates is outside country %s boundary" % country.name)}
                )
        validated_data["location"] = GEOSGeometry("POINT(%f %f)" % (lng, lat))
        validated_data["modified_by"] = self.context["request"].user
        # NOTE: Each time form is updated change validated status to `False`
        validated_data["validated"] = False
        return super().update(instance, validated_data)


class LocalUnitSerializer(serializers.ModelSerializer):
    # NOTE: location_geojson contains the geojson of the location
    location_geojson = serializers.SerializerMethodField()
    country_details = LocalUnitCountrySerializer(source="country", read_only=True)
    type_details = LocalUnitTypeSerializer(source="type", read_only=True)
    health_details = MiniHealthDataSerializer(read_only=True, source="health")
    validated = serializers.BooleanField(read_only=True)

    class Meta:
        model = LocalUnit
        fields = (
            "id",
            "country",
            "local_branch_name",
            "english_branch_name",
            "location_geojson",
            "type",
            "validated",
            "address_loc",
            "address_en",
            "country_details",
            "type_details",
            "health",
            "health_details",
        )

    def get_location_geojson(self, unit) -> dict:
        return json.loads(unit.location.geojson)


class PrivateLocalUnitSerializer(serializers.ModelSerializer):
    # NOTE: location_geojson contains the geojson of the location
    location_geojson = serializers.SerializerMethodField()
    country_details = LocalUnitCountrySerializer(source="country", read_only=True)
    type_details = LocalUnitTypeSerializer(source="type", read_only=True)
    health_details = MiniHealthDataSerializer(read_only=True, source="health")
    validated = serializers.BooleanField(read_only=True)
    modified_by_details = LocalUnitMiniUserSerializer(source="modified_by", read_only=True)
    is_locked = serializers.BooleanField(read_only=True)

    class Meta:
        model = LocalUnit
        fields = (
            "id",
            "country",
            "local_branch_name",
            "english_branch_name",
            "location_geojson",
            "type",
            "validated",
            "address_loc",
            "address_en",
            "country_details",
            "type_details",
            "health",
            "health_details",
            "focal_person_loc",
            "focal_person_en",
            "email",
            "phone",
            "modified_at",
            "modified_by_details",
            "is_locked",
        )

    def get_location_geojson(self, unit) -> dict:
        return json.loads(unit.location.geojson)


class DelegationOfficeCountrySerializer(serializers.ModelSerializer):

    class Meta:
        model = Country
        fields = ("name", "iso3", "region", "region")


class DelegationOfficeTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = DelegationOfficeType
        fields = ("name", "code")


class DelegationOfficeSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()
    country = DelegationOfficeCountrySerializer()
    dotype = DelegationOfficeTypeSerializer()

    class Meta:
        model = DelegationOffice
        fields = [
            "name",
            "city",
            "address",
            "postcode",
            "location",
            "society_url",
            "url_ifrc",
            "hod_first_name",
            "hod_last_name",
            "hod_mobile_number",
            "hod_email",
            "assistant_name",
            "assistant_email",
            "is_ns_same_location",
            "is_multiple_ifrc_offices",
            "visibility",
            "created_at",
            "modified_at",
            "date_of_data",
            "country",
            "dotype",
        ]

    def get_location(self, office):
        return json.loads(office.location.geojson)

    def get_country(self, office):
        return {"country"}

    def get_type(self, office):
        return {"type"}


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
    dotype_name = serializers.CharField(source="dotype.name", read_only=True)

    class Meta:
        model = DelegationOffice
        fields = (
            "hod_first_name",
            "hod_last_name",
            "hod_mobile_number",
            "hod_email",
            "dotype_name",
            "city",
            "address",
        )


class RejectedReasonSerialzier(serializers.Serializer):
    reason = serializers.CharField(required=True)


class LocalUnitChangeRequestSerializer(serializers.ModelSerializer):
    created_by_details = LocalUnitMiniUserSerializer(source="created_by", read_only=True)
    status_details = serializers.CharField(source="get_status_display", read_only=True)
    current_validator_details = serializers.CharField(source="get_current_validator_display", read_only=True)
    # NOTE: Typing issue on JsonField, So returning as string
    previous_data_details = serializers.SerializerMethodField(read_only=True, required=False)

    class Meta:
        model = LocalUnitChangeRequest
        fields = (
            "id",
            "status",
            "status_details",
            "current_validator",
            "current_validator_details",
            "created_by_details",
            "previous_data_details",
        )

    def get_previous_data_details(self, obj):
        return obj.previous_data


class LocalUnitDeprecateSerializer(serializers.ModelSerializer):
    deprecated_reason = serializers.ChoiceField(choices=LocalUnit.DeprecateReason, required=True)
    deprecated_reason_overview = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = LocalUnit
        fields = ("deprecated_reason", "deprecated_reason_overview")

    def create(self, _):
        raise serializers.ValidationError({"non_field_errors": gettext("Create is not allowed")})

    def validate(self, attrs):
        instance = self.instance

        if instance and instance.is_deprecated:
            raise serializers.ValidationError({"non_field_errors": gettext("This object is already depricated")})

        return attrs

    def update(self, instance, validated_data):
        instance.is_deprecated = True
        instance.deprecated_reason = validated_data.get("deprecated_reason", instance.deprecated_reason)
        instance.deprecated_reason_overview = validated_data.get(
            "deprecated_reason_overview", instance.deprecated_reason_overview
        )
        instance.save(update_fields=["is_deprecated", "deprecated_reason", "deprecated_reason_overview"])
        return instance
