import json
import os
from datetime import datetime

import reversion
from django.contrib.auth.models import User
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from django.utils.translation import gettext
from rest_framework import serializers
from reversion.models import Version
from shapely.geometry import MultiPolygon, Point, Polygon

from api.models import Country, CountryType, VisibilityChoices
from local_units.tasks import process_bulk_upload_local_unit
from local_units.utils import normalize_bool, numerize, wash
from main.writable_nested_serializers import NestedCreateMixin, NestedUpdateMixin

from .models import (
    Affiliation,
    BloodService,
    DelegationOffice,
    DelegationOfficeType,
    ExternallyManagedLocalUnit,
    FacilityType,
    Functionality,
    GeneralMedicalService,
    HealthData,
    HospitalType,
    LocalUnit,
    LocalUnitBulkUpload,
    LocalUnitChangeRequest,
    LocalUnitLevel,
    LocalUnitType,
    OtherProfile,
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


class OtherProfileSerializer(NestedCreateMixin, NestedUpdateMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = OtherProfile
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
    other_profiles = OtherProfileSerializer(
        many=True,
        required=False,
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
    status_details = serializers.CharField(source="get_status_display", read_only=True)

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
            "status",
            "status_details",
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
    status_details = serializers.CharField(source="get_status_display", read_only=True)
    location_json = LocationSerializer(required=True)
    location = serializers.CharField(required=False)
    modified_by_details = LocalUnitMiniUserSerializer(source="modified_by", read_only=True)
    created_by_details = LocalUnitMiniUserSerializer(source="created_by", read_only=True)
    version_id = serializers.SerializerMethodField()

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
            "status",
            "status_details",
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
            "update_reason_overview",
            "bulk_upload",
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

        # Externally managed check
        country = data.get("country")
        type = data.get("type")
        qs = ExternallyManagedLocalUnit.objects.filter(country=country, local_unit_type=type, enabled=True)
        if qs.exists():
            raise serializers.ValidationError(
                gettext("Country and Local unit Type is externally managed cannot be created manually.")
            )

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
        validated_data["status"] = LocalUnit.Status.UNVALIDATED
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
        return super().update(instance, validated_data)


class LocalUnitSerializer(serializers.ModelSerializer):
    # NOTE: location_geojson contains the geojson of the location
    location_geojson = serializers.SerializerMethodField()
    country_details = LocalUnitCountrySerializer(source="country", read_only=True)
    type_details = LocalUnitTypeSerializer(source="type", read_only=True)
    health_details = MiniHealthDataSerializer(read_only=True, source="health")
    status_details = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = LocalUnit
        fields = (
            "id",
            "country",
            "local_branch_name",
            "english_branch_name",
            "location_geojson",
            "type",
            "status",
            "status_details",
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
    status_details = serializers.CharField(source="get_status_display", read_only=True)
    modified_by_details = LocalUnitMiniUserSerializer(source="modified_by", read_only=True)
    update_reason_overview = serializers.CharField(read_only=True)

    class Meta:
        model = LocalUnit
        fields = (
            "id",
            "country",
            "local_branch_name",
            "english_branch_name",
            "location_geojson",
            "type",
            "status",
            "status_details",
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
            "bulk_upload",
            "update_reason_overview",
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
    specialized_medical_beyond_primary_level = SpecializedMedicalServiceSerializer(many=True)


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
    previous_data_details = serializers.SerializerMethodField(read_only=True)

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


class ExternallyManagedLocalUnitSerializer(serializers.ModelSerializer):
    country = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.filter(
            is_deprecated=False, independent=True, iso3__isnull=False, record_type=CountryType.COUNTRY
        ),
        write_only=True,
    )
    local_unit_type = serializers.PrimaryKeyRelatedField(queryset=LocalUnitType.objects.all(), write_only=True)
    country_details = LocalUnitCountrySerializer(source="country", read_only=True)
    local_unit_type_details = LocalUnitTypeSerializer(source="local_unit_type", read_only=True)

    class Meta:
        model = ExternallyManagedLocalUnit
        fields = (
            "id",
            "country",
            "local_unit_type",
            "country_details",
            "local_unit_type_details",
            "enabled",
        )

    def validate(self, validated_data):
        if (
            not self.instance
            and ExternallyManagedLocalUnit.objects.filter(
                country=validated_data["country"],
                local_unit_type=validated_data["local_unit_type"],
            ).first()
        ):
            raise serializers.ValidationError(
                gettext("An externally managed local unit with this country and type already exists.")
            )
        return validated_data

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)


class LocalUnitBulkUploadSerializer(serializers.ModelSerializer):
    country = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.filter(
            is_deprecated=False, independent=True, iso3__isnull=False, record_type=CountryType.COUNTRY
        ),
        write_only=True,
    )
    local_unit_type = serializers.PrimaryKeyRelatedField(queryset=LocalUnitType.objects.all(), write_only=True)
    country_details = LocalUnitCountrySerializer(source="country", read_only=True)
    local_unit_type_details = LocalUnitTypeSerializer(source="local_unit_type", read_only=True)
    triggered_by_details = LocalUnitMiniUserSerializer(source="triggered_by", read_only=True)
    file_name = serializers.SerializerMethodField()
    error_message = serializers.CharField(read_only=True)
    status_details = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = LocalUnitBulkUpload
        fields = "__all__"
        read_only_fields = (
            "success_count",
            "failed_count",
            "file_size",
            "status",
            "status_details",
            "error_file",
            "triggered_by",
            "file_name",
            "error_message",
        )

    def validate_file(self, file):
        if not file.name.endswith(".xlsx"):
            raise serializers.ValidationError(gettext("File must be a xlsx file."))
        if file.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(gettext("File must be less than 10 MB."))
        return file

    def get_file_name(self, obj):
        return os.path.basename(obj.file.name) if obj.file else None

    def validate(self, attrs):

        country = attrs.get("country")
        local_unit_type = attrs.get("local_unit_type")
        is_externally_managed = ExternallyManagedLocalUnit.objects.filter(
            country=country, local_unit_type=local_unit_type, enabled=True
        )
        if not is_externally_managed.exists():
            raise serializers.ValidationError(gettext("Country and local unit type are not externally managed."))
        return attrs

    def create(self, validated_data):
        validated_data["triggered_by"] = self.context["request"].user
        upload_file = validated_data.get("file")
        # TODO(@susilnem): Find a better way to get the file size
        validated_data["file_size"] = upload_file.size
        validated_data["status"] = LocalUnitBulkUpload.Status.PENDING
        instance = super().create(validated_data)

        transaction.on_commit(lambda: process_bulk_upload_local_unit.delay(instance.id))
        return instance


class LocalUnitTemplateFilesSerializer(serializers.Serializer):
    template_url = serializers.CharField(read_only=True)


# NOTE: The `HealthDataBulkUploadSerializer` is used to validate the data for bulk upload of local unit health care type.


class HealthDataBulkUploadSerializer(NestedCreateMixin):
    class Meta:
        model = HealthData
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._m2m_data = {}
        self._maps_loaded = False

    def _load_maps(self):
        """Only load model lookups when needed"""
        if self._maps_loaded:
            return
        self.affiliation_map = self._build_map(Affiliation)
        self.functionality_map = self._build_map(Functionality)
        self.facilitytype_map = self._build_map(FacilityType)
        self.primaryhcc_map = self._build_map(PrimaryHCC)
        self.hospitaltype_map = self._build_map(HospitalType)

        self.generalmedicalservice_map = self._build_map(GeneralMedicalService)
        self.specializedmedicalservice_map = self._build_map(SpecializedMedicalService)
        self.bloodservice_map = self._build_map(BloodService)
        self.professionaltrainingfacility_map = self._build_map(ProfessionalTrainingFacility)
        self._maps_loaded = True

    def _build_map(self, model):
        mapping = {}
        for obj in model.objects.all():
            if not obj.name:
                continue
            name_key = wash(obj.name)
            mapping[name_key] = obj

            if hasattr(obj, "code") and obj.code is not None:
                mapping[str(obj.code).strip()] = obj
                label = f"{obj.name} ({obj.code})"
                mapping[wash(label)] = obj
        return mapping

    def _resolve_required_fk(self, data, field_name, mapping):
        key = wash(data.get(field_name))
        if not key:
            raise serializers.ValidationError({field_name: f"{field_name.replace('_', ' ').title()} is required."})
        instance = mapping.get(key)
        if not instance:
            raise serializers.ValidationError(
                {field_name: f"{field_name.replace('_', ' ').title()} '{data.get(field_name)}' not found"}
            )
        data[field_name] = instance.pk

    def _resolve_optional_fk(self, data, field_name, mapping):
        key = wash(data.get(field_name))
        instance = mapping.get(key) if key else None
        data[field_name] = instance.pk if instance else None

    def to_internal_value(self, data):
        self._load_maps()
        data = data.copy()

        self._resolve_required_fk(data, "affiliation", self.affiliation_map)
        self._resolve_required_fk(data, "functionality", self.functionality_map)
        self._resolve_required_fk(data, "health_facility_type", self.facilitytype_map)

        self._resolve_optional_fk(data, "primary_health_care_center", self.primaryhcc_map)
        self._resolve_optional_fk(data, "hospital_type", self.hospitaltype_map)

        for bool_field in [
            "is_teaching_hospital",
            "is_in_patient_capacity",
            "is_isolation_rooms_wards",
            "is_warehousing",
            "is_cold_chain",
            "other_medical_heal",
        ]:
            if bool_field in data:
                data[bool_field] = normalize_bool(data.get(bool_field))
        for int_field in [
            "total_number_of_human_resource",
            "general_practitioner",
            "specialist",
            "residents_doctor",
            "nurse",
            "dentist",
            "nursing_aid",
            "midwife",
        ]:
            if int_field in data:
                val = data.get(int_field)
                converted = numerize(val)
                if val and converted is None:
                    raise serializers.ValidationError({int_field: f"Invalid integer value: {val}"})
                data[int_field] = converted

        def parse_m2m(field_name, mapping):
            raw = data.get(field_name, "")
            ids = []
            if raw:
                for val in raw.split(","):
                    key = wash(val)
                    if key in mapping:
                        ids.append(mapping[key].id)
                    else:
                        raise serializers.ValidationError({field_name: f"Invalid value '{val}'"})
            self._m2m_data[field_name] = ids
            data.pop(field_name, None)

        parse_m2m("general_medical_services", self.generalmedicalservice_map)
        parse_m2m("specialized_medical_beyond_primary_level", self.specializedmedicalservice_map)
        parse_m2m("blood_services", self.bloodservice_map)
        parse_m2m("professional_training_facilities", self.professionaltrainingfacility_map)
        return super().to_internal_value(data)

    def create(self, validated_data):
        m2m_data = self._m2m_data or {}
        instance = super().create(validated_data)
        for field, ids in m2m_data.items():
            getattr(instance, field).set(ids)
        return instance


# NOTE: The `LocalUnitBulkUploadDetailSerializer` is used to validate the data for bulk upload of local units.
class LocalUnitBulkUploadDetailSerializer(serializers.ModelSerializer):
    location = serializers.CharField(required=False)
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)
    visibility = serializers.CharField(required=True, allow_blank=True)
    date_of_data = serializers.CharField(required=False, allow_null=True)
    level = serializers.CharField(required=False, allow_null=True)
    health = serializers.PrimaryKeyRelatedField(queryset=HealthData.objects.all(), required=False, allow_null=True)

    class Meta:
        model = LocalUnit
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.level_map = {lvl.name.lower(): lvl for lvl in LocalUnitLevel.objects.all()}

    def validate_date_of_data(self, value: str):
        today = datetime.today().strftime("%Y-%m-%d")
        if not value:
            return today

        possible_formats = ("%d-%b-%y", "%m/%d/%Y", "%Y-%m-%d")
        for date_format in possible_formats:
            try:
                return datetime.strptime(value.strip(), date_format).strftime("%Y-%m-%d")
            except ValueError:
                continue
        # If no format matched, return today's date
        return today

    def validate_visibility(self, value: str):
        if not value:
            return VisibilityChoices.MEMBERSHIP

        visibility = value.lower()
        if visibility == "public":
            return VisibilityChoices.PUBLIC

        # return default visibility if not matched
        return VisibilityChoices.MEMBERSHIP

    def validate_level(self, value):
        if not value:
            return None
        level_name = value.strip().lower()
        level_id = self.level_map.get(level_name)
        if not level_id:
            raise serializers.ValidationError(gettext("Level is not valid"))
        return level_id

    def validate(self, validated_data):

        if not validated_data.get("local_branch_name") and not validated_data.get("english_branch_name"):
            raise serializers.ValidationError(gettext("Branch Name Combination is required."))

        # Country location validation
        latitude = validated_data.pop("latitude")
        longitude = validated_data.pop("longitude")
        if not latitude or not longitude:
            raise serializers.ValidationError(gettext("Latitude and Longitude are required."))
        country = validated_data.get("country")
        if not country:
            raise serializers.ValidationError(gettext("Country is required."))

        input_point = Point(longitude, latitude)
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
                    {"location": gettext("Input coordinates is outside country %s boundary" % country.name)}
                )

        validated_data["location"] = GEOSGeometry("POINT(%f %f)" % (longitude, latitude))
        validated_data["status"] = LocalUnit.Status.EXTERNALLY_MANAGED

        # NOTE: Bulk upload doesn't call create() method
        return validated_data


# Public, flattened serializer for Health Local Units (Type Code = 2)
class _CodeNameSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    name = serializers.CharField()


class HealthLocalUnitFlatSerializer(serializers.ModelSerializer):
    # LocalUnit basics
    id = serializers.IntegerField(read_only=True)
    country_id = serializers.IntegerField(source="country.id", read_only=True)
    country_name = serializers.CharField(source="country.name", read_only=True)
    country_iso3 = serializers.CharField(source="country.iso3", read_only=True)
    type_code = serializers.IntegerField(source="type.code", read_only=True)
    type_name = serializers.CharField(source="type.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    location = serializers.SerializerMethodField()

    # HealthData flattened
    affiliation = serializers.SerializerMethodField()
    functionality = serializers.SerializerMethodField()
    health_facility_type = serializers.SerializerMethodField()
    primary_health_care_center = serializers.SerializerMethodField()
    hospital_type = serializers.SerializerMethodField()

    general_medical_services = serializers.SerializerMethodField()
    specialized_medical_beyond_primary_level = serializers.SerializerMethodField()
    blood_services = serializers.SerializerMethodField()
    professional_training_facilities = serializers.SerializerMethodField()

    class Meta:
        model = LocalUnit
        fields = (
            # LocalUnit
            "id",
            "country_id",
            "country_name",
            "country_iso3",
            "local_branch_name",
            "english_branch_name",
            "address_loc",
            "address_en",
            "city_loc",
            "city_en",
            "postcode",
            "phone",
            "email",
            "link",
            "focal_person_loc",
            "focal_person_en",
            "date_of_data",
            "subtype",
            "type_code",
            "type_name",
            "status",
            "status_display",
            "location",
            # HealthData core
            "affiliation",
            "other_affiliation",
            "functionality",
            "focal_point_email",
            "focal_point_phone_number",
            "focal_point_position",
            "health_facility_type",
            "other_facility_type",
            "primary_health_care_center",
            "speciality",
            "hospital_type",
            "is_teaching_hospital",
            "is_in_patient_capacity",
            "is_isolation_rooms_wards",
            "maximum_capacity",
            "number_of_isolation_rooms",
            "is_warehousing",
            "is_cold_chain",
            "ambulance_type_a",
            "ambulance_type_b",
            "ambulance_type_c",
            "general_medical_services",
            "specialized_medical_beyond_primary_level",
            "other_services",
            "blood_services",
            "professional_training_facilities",
            "total_number_of_human_resource",
            "general_practitioner",
            "specialist",
            "residents_doctor",
            "nurse",
            "dentist",
            "nursing_aid",
            "midwife",
            "other_medical_heal",
            "other_profiles",
            "feedback",
        )

    # NOTE: HealthData direct field mappings via source
    other_affiliation = serializers.CharField(source="health.other_affiliation", read_only=True)
    focal_point_email = serializers.EmailField(source="health.focal_point_email", read_only=True)
    focal_point_phone_number = serializers.CharField(source="health.focal_point_phone_number", read_only=True)
    focal_point_position = serializers.CharField(source="health.focal_point_position", read_only=True)
    other_facility_type = serializers.CharField(source="health.other_facility_type", read_only=True)
    speciality = serializers.CharField(source="health.speciality", read_only=True)
    is_teaching_hospital = serializers.BooleanField(source="health.is_teaching_hospital", read_only=True)
    is_in_patient_capacity = serializers.BooleanField(source="health.is_in_patient_capacity", read_only=True)
    is_isolation_rooms_wards = serializers.BooleanField(source="health.is_isolation_rooms_wards", read_only=True)
    maximum_capacity = serializers.IntegerField(source="health.maximum_capacity", read_only=True)
    number_of_isolation_rooms = serializers.IntegerField(source="health.number_of_isolation_rooms", read_only=True)
    is_warehousing = serializers.BooleanField(source="health.is_warehousing", read_only=True)
    is_cold_chain = serializers.BooleanField(source="health.is_cold_chain", read_only=True)
    ambulance_type_a = serializers.IntegerField(source="health.ambulance_type_a", read_only=True)
    ambulance_type_b = serializers.IntegerField(source="health.ambulance_type_b", read_only=True)
    ambulance_type_c = serializers.IntegerField(source="health.ambulance_type_c", read_only=True)
    other_services = serializers.CharField(source="health.other_services", read_only=True)
    total_number_of_human_resource = serializers.IntegerField(source="health.total_number_of_human_resource", read_only=True)
    general_practitioner = serializers.IntegerField(source="health.general_practitioner", read_only=True)
    specialist = serializers.IntegerField(source="health.specialist", read_only=True)
    residents_doctor = serializers.IntegerField(source="health.residents_doctor", read_only=True)
    nurse = serializers.IntegerField(source="health.nurse", read_only=True)
    dentist = serializers.IntegerField(source="health.dentist", read_only=True)
    nursing_aid = serializers.IntegerField(source="health.nursing_aid", read_only=True)
    midwife = serializers.IntegerField(source="health.midwife", read_only=True)
    other_medical_heal = serializers.BooleanField(source="health.other_medical_heal", read_only=True)
    other_profiles = serializers.CharField(source="health.other_profiles", read_only=True)
    feedback = serializers.CharField(source="health.feedback", read_only=True)

    def get_location(self, unit) -> dict:
        return {"lat": unit.location.y, "lng": unit.location.x}

    def _code_name(self, obj):
        if not obj:
            return None
        return {"code": obj.code, "name": obj.name}

    def _code_name_list(self, qs):
        return [{"code": x.code, "name": x.name} for x in qs.all()] if qs is not None else []

    def get_affiliation(self, obj):
        return self._code_name(getattr(obj.health, "affiliation", None) if obj.health else None)

    def get_functionality(self, obj):
        return self._code_name(getattr(obj.health, "functionality", None) if obj.health else None)

    def get_health_facility_type(self, obj):
        if not obj.health or not obj.health.health_facility_type:
            return None
        ft = obj.health.health_facility_type
        data = {"code": ft.code, "name": ft.name}
        # Attach image_url if request in context
        request = self.context.get("request") if self.context else None
        if request:
            data["image_url"] = FacilityType.get_image_map(ft.code, request)
        return data

    def get_primary_health_care_center(self, obj):
        return self._code_name(getattr(obj.health, "primary_health_care_center", None) if obj.health else None)

    def get_hospital_type(self, obj):
        return self._code_name(getattr(obj.health, "hospital_type", None) if obj.health else None)

    def get_general_medical_services(self, obj):
        return self._code_name_list(obj.health.general_medical_services if obj.health else None)

    def get_specialized_medical_beyond_primary_level(self, obj):
        return self._code_name_list(obj.health.specialized_medical_beyond_primary_level if obj.health else None)

    def get_blood_services(self, obj):
        return self._code_name_list(obj.health.blood_services if obj.health else None)

    def get_professional_training_facilities(self, obj):
        return self._code_name_list(obj.health.professional_training_facilities if obj.health else None)
