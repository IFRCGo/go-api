import json
from collections import defaultdict
from typing import List, Union

from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import get_language as django_get_language
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

# from api.utils import pdf_exporter
from api.tasks import generate_url
from api.utils import CountryValidator, RegionValidator
from deployments.models import EmergencyProject, Personnel, PersonnelDeployment
from dref.models import Dref, DrefFinalReport, DrefOperationalUpdate
from eap.models import FullEAP, SimplifiedEAP
from lang.models import String
from lang.serializers import ModelSerializer
from local_units.models import DelegationOffice
from local_units.serializers import MiniDelegationOfficeSerializer
from main.translation import TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME
from main.utils import get_merged_items_by_fields
from main.writable_nested_serializers import NestedCreateMixin, NestedUpdateMixin
from notifications.models import Subscription
from per.models import Overview
from utils.file_check import validate_file_type

from .event_sources import SOURCES
from .models import (
    Action,
    ActionsTaken,
    Admin2,
    Appeal,
    AppealDocument,
    AppealHistory,
    Country,
    CountryCapacityStrengthening,
    CountryContact,
    CountryDirectory,
    CountryICRCPresence,
    CountryKeyDocument,
    CountryLink,
    CountryOfFieldReportToReview,
    CountryOrganizationalCapacity,
    CountrySnippet,
    CountrySupportingPartner,
    DisasterType,
    District,
    Event,
    EventContact,
    EventFeaturedDocument,
    EventLink,
    EventSeverityLevelHistory,
    Export,
    ExternalPartner,
    FieldReport,
    FieldReportContact,
    KeyFigure,
    MainContact,
    NSDInitiatives,
    Profile,
    Region,
    RegionContact,
    RegionEmergencySnippet,
    RegionKeyFigure,
    RegionLink,
    RegionPreparednessSnippet,
    RegionProfileSnippet,
    RegionSnippet,
    SituationReport,
    SituationReportType,
    Snippet,
    Source,
    SupportedActivity,
    UserCountry,
)


class GeoSerializerMixin:
    """
    A mixin class to encapsulate common methods
    used across serializers that deal with geo objects.
    Will allow us to avoid repeating code to convert objects
    to GeoJSON, etc.

    FIXME: use this base class for existing serializers using geo objects.
    FIXME: the methods can probably be thought through a bit better
    """

    def get_bbox(self, district) -> dict:
        if district.bbox:
            return json.loads(district.bbox.geojson)
        else:
            return None

    def get_centroid(self, district) -> dict:
        if district.centroid:
            return json.loads(district.centroid.geojson)
        else:
            return None


class DisasterTypeSerializer(ModelSerializer):
    class Meta:
        model = DisasterType
        fields = (
            "name",
            "summary",
            "id",
        )


class RegionSerializer(ModelSerializer):
    class Meta:
        model = Region
        fields = (
            "name",
            "id",
            "region_name",
            "label",
        )


class EventSeverityLevelHistorySerializer(ModelSerializer):
    class Meta:
        model = EventSeverityLevelHistory
        fields = "__all__"


class RegionGeoSerializer(ModelSerializer):
    bbox = serializers.SerializerMethodField()

    @staticmethod
    def get_bbox(region):
        return region.bbox and json.loads(region.bbox.geojson)

    class Meta:
        model = Region
        fields = (
            "name",
            "id",
            "region_name",
            "bbox",
            "label",
        )


class CountryLinkSerializer(ModelSerializer):
    class Meta:
        model = CountryLink
        fields = (
            "title",
            "url",
            "id",
        )


class CountryTableauSerializer(ModelSerializer):
    region = RegionSerializer()
    record_type_display = serializers.CharField(source="get_record_type_display", read_only=True)

    class Meta:
        model = Country
        fields = (
            "name",
            "iso",
            "iso3",
            "society_name",
            "society_url",
            "region",
            "overview",
            "key_priorities",
            "inform_score",
            "id",
            "url_ifrc",
            "record_type",
            "record_type_display",
        )


class CountrySerializer(ModelSerializer):
    record_type_display = serializers.CharField(source="get_record_type_display", read_only=True)

    class Meta:
        model = Country
        fields = (
            "name",
            "iso",
            "iso3",
            "society_name",
            "society_url",
            "region",
            "overview",
            "key_priorities",
            "inform_score",
            "id",
            "url_ifrc",
            "record_type",
            "record_type_display",
            "independent",
            "is_deprecated",
            "fdrs",
            "average_household_size",
        )

    def validate_logo(self, logo):
        validate_file_type(logo)
        return logo


class CountryGeoSerializer(ModelSerializer):
    bbox = serializers.SerializerMethodField()
    centroid = serializers.SerializerMethodField()
    record_type_display = serializers.CharField(source="get_record_type_display", read_only=True)
    links = CountryLinkSerializer(many=True, read_only=True)

    @staticmethod
    def get_bbox(country) -> dict:
        return country.bbox and json.loads(country.bbox.geojson)

    @staticmethod
    def get_centroid(country) -> dict:
        return country.centroid and json.loads(country.centroid.geojson)

    class Meta:
        model = Country
        fields = (
            "name",
            "iso",
            "iso3",
            "society_name",
            "society_url",
            "region",
            "overview",
            "key_priorities",
            "inform_score",
            "id",
            "url_ifrc",
            "record_type",
            "record_type_display",
            "bbox",
            "centroid",
            "independent",
            "is_deprecated",
            "fdrs",
            "links",
            "address_1",
            "address_2",
            "city_code",
            "phone",
            "website",
            "emails",
        )


class MiniCountrySerializer(ModelSerializer):
    record_type_display = serializers.CharField(source="get_record_type_display", read_only=True)

    class Meta:
        model = Country
        fields = (
            "name",
            "iso",
            "iso3",
            "society_name",
            "id",
            "record_type",
            "record_type_display",
            "region",
            "independent",
            "is_deprecated",
            "fdrs",
            "average_household_size",
        )


class CountrySerializerRMD(ModelSerializer):
    class Meta:
        model = Country
        fields = ("name", "iso3")


class DistrictSerializerRMD(ModelSerializer):
    class Meta:
        model = District
        fields = (
            "name",
            "code",
            "is_deprecated",
        )

    @staticmethod
    def get_bbox(district) -> dict:
        return district.bbox and json.loads(district.bbox.geojson)

    @staticmethod
    def get_centroid(district) -> dict:
        return district.centroid and json.loads(district.centroid.geojson)


class MicroCountrySerializer(ModelSerializer):
    class Meta:
        model = Country
        fields = ("id", "name", "iso", "iso3", "society_name")


class NanoCountrySerializer(ModelSerializer):
    region = serializers.SerializerMethodField()

    @staticmethod
    def get_region(obj):
        return obj.region.label if obj.region else None

    class Meta:
        model = Country
        fields = ("iso3", "name", "society_name", "region")


class RegoCountrySerializer(ModelSerializer):
    class Meta:
        model = Country
        fields = (
            "name",
            "society_name",
            "region",
            "id",
        )


class NotCountrySerializer(ModelSerializer):  # fake serializer for a short data response for PER
    class Meta:
        model = Country
        fields = ("id",)


class DistrictSerializer(ModelSerializer):
    country = MiniCountrySerializer()
    bbox = serializers.SerializerMethodField()
    centroid = serializers.SerializerMethodField()

    class Meta:
        model = District
        fields = (
            "name",
            "code",
            "country",
            "id",
            "is_deprecated",
            "bbox",
            "centroid",
            "wb_population",
            "wb_year",
            "nuts1",
            "nuts2",
            "nuts3",
            "emma_id",
            "fips_code",
        )

    @staticmethod
    def get_bbox(district) -> dict:
        return district.bbox and json.loads(district.bbox.geojson)

    @staticmethod
    def get_centroid(district) -> dict:
        return district.centroid and json.loads(district.centroid.geojson)


class Admin2Serializer(GeoSerializerMixin, ModelSerializer):
    bbox = serializers.SerializerMethodField()
    centroid = serializers.SerializerMethodField()
    district_id = serializers.IntegerField(source="admin1.id", read_only=True)

    class Meta:
        model = Admin2
        fields = (
            "id",
            "district_id",
            "name",
            "code",
            "bbox",
            "centroid",
            "is_deprecated",
        )


class MiniAdmin2Serializer(ModelSerializer):
    district_id = serializers.IntegerField(source="admin1.id", read_only=True)

    class Meta:
        model = Admin2
        fields = ("id", "name", "code", "district_id")


class MiniDistrictSerializer(ModelSerializer):
    class Meta:
        model = District
        fields = (
            "name",
            "code",
            "id",
            "is_enclave",
            "is_deprecated",
        )


class MiniDistrictGeoSerializer(GeoSerializerMixin, ModelSerializer):
    bbox = serializers.SerializerMethodField()
    centroid = serializers.SerializerMethodField()
    country_name = serializers.CharField(source="country.name", read_only=True)
    country_iso = serializers.CharField(source="country.iso", read_only=True)
    country_iso3 = serializers.CharField(source="country.iso3", read_only=True)
    nuts1 = serializers.CharField(read_only=True)
    nuts2 = serializers.CharField(read_only=True)
    nuts3 = serializers.CharField(read_only=True)
    emma_id = serializers.CharField(read_only=True)
    fips_code = serializers.IntegerField(read_only=True)

    @staticmethod
    def get_bbox(district) -> Union[dict, None]:
        if district.bbox:
            return json.loads(district.bbox.geojson)
        else:
            return None

    @staticmethod
    def get_centroid(district) -> Union[dict, None]:
        if district.centroid:
            return json.loads(district.centroid.geojson)
        else:
            return None

    class Meta:
        model = District
        fields = (
            "id",
            "name",
            "code",
            "country_name",
            "country_iso",
            "country_iso3",
            "is_enclave",
            "bbox",
            "centroid",
            "is_deprecated",
            "wb_population",
            "wb_year",
            "nuts1",
            "nuts2",
            "nuts3",
            "emma_id",
            "fips_code",
        )


class RegionKeyFigureSerializer(ModelSerializer):
    class Meta:
        model = RegionKeyFigure
        fields = (
            "region",
            "figure",
            "deck",
            "source",
            "visibility",
            "id",
        )


class RegionSnippetTableauSerializer(ModelSerializer):
    region = RegionSerializer()
    visibility_display = serializers.CharField(source="get_visibility_display", read_only=True)

    class Meta:
        model = RegionSnippet
        fields = (
            "region",
            "snippet",
            "image",
            "visibility",
            "visibility_display",
            "id",
        )


class RegionSnippetSerializer(ModelSerializer):
    visibility_display = serializers.CharField(source="get_visibility_display", read_only=True)

    class Meta:
        model = RegionSnippet
        fields = (
            "region",
            "snippet",
            "image",
            "visibility",
            "visibility_display",
            "id",
        )

    def validate_image(self, image):
        validate_file_type(image)
        return image


class RegionEmergencySnippetSerializer(ModelSerializer):
    class Meta:
        model = RegionEmergencySnippet
        fields = (
            "region",
            "title",
            "snippet",
            "id",
        )


class RegionProfileSnippetSerializer(ModelSerializer):
    class Meta:
        model = RegionProfileSnippet
        fields = (
            "region",
            "title",
            "snippet",
            "id",
        )


class RegionPreparednessSnippetSerializer(ModelSerializer):
    class Meta:
        model = RegionPreparednessSnippet
        fields = (
            "region",
            "title",
            "snippet",
            "id",
        )


class CountrySnippetTableauSerializer(serializers.ModelSerializer):
    country = CountrySerializer()
    visibility_display = serializers.CharField(source="get_visibility_display", read_only=True)

    class Meta:
        model = CountrySnippet
        fields = (
            "country",
            "snippet",
            "image",
            "visibility",
            "visibility_display",
            "id",
        )


class CountrySnippetSerializer(ModelSerializer):
    visibility_display = serializers.CharField(source="get_visibility_display", read_only=True)

    class Meta:
        model = CountrySnippet
        fields = (
            "country",
            "snippet",
            "image",
            "visibility",
            "visibility_display",
            "id",
        )

    def validate_image(self, image):
        validate_file_type(image)
        return image


class RegionLinkSerializer(ModelSerializer):
    class Meta:
        model = RegionLink
        fields = (
            "title",
            "url",
            "id",
            "show_in_go",
        )


class RegionContactSerializer(ModelSerializer):
    class Meta:
        model = RegionContact
        fields = (
            "ctype",
            "name",
            "title",
            "email",
            "id",
        )


class CountryContactSerializer(ModelSerializer):
    class Meta:
        model = CountryContact
        fields = (
            "ctype",
            "name",
            "title",
            "email",
            "id",
        )


class RegionRelationSerializer(ModelSerializer):
    links = RegionLinkSerializer(many=True, read_only=True)
    contacts = RegionContactSerializer(many=True, read_only=True)
    # Visibility filtering now handled in RegionViewset.get_queryset via Prefetch.
    snippets = RegionSnippetSerializer(many=True, read_only=True)
    emergency_snippets = RegionEmergencySnippetSerializer(many=True, read_only=True)
    profile_snippets = RegionProfileSnippetSerializer(many=True, read_only=True)
    preparedness_snippets = RegionPreparednessSnippetSerializer(many=True, read_only=True)
    national_society_count = serializers.SerializerMethodField()
    country_cluster_count = serializers.SerializerMethodField()
    country_plan_count = serializers.IntegerField(read_only=True)
    bbox = serializers.SerializerMethodField()
    # centroid = serializers.SerializerMethodField()

    class Meta:
        model = Region
        fields = (
            "links",
            "contacts",
            "snippets",
            "emergency_snippets",
            "profile_snippets",
            "preparedness_snippets",
            "name",
            "region_name",
            "id",
            "additional_tab_name",
            "country_plan_count",
            "national_society_count",
            "country_cluster_count",
            "bbox",
            # "centroid"
        )

    @staticmethod
    def get_national_society_count(obj) -> int:
        return obj.get_national_society_count()

    @staticmethod
    def get_country_cluster_count(obj) -> int:
        return obj.get_country_cluster_count()

    @staticmethod
    def get_bbox(region) -> dict:
        return region.bbox and json.loads(region.bbox.geojson)

    # get_snippets removed – visibility filtering now done entirely in the viewset.


class CountryDirectorySerializer(ModelSerializer):
    class Meta:
        model = CountryDirectory
        fields = ("id", "first_name", "last_name", "position")


class NSDInitiativesSerializer(ModelSerializer):
    # Return translated category names (current active language) – like title does.
    categories = serializers.SerializerMethodField()

    class Meta:
        model = NSDInitiatives
        fields = "__all__"

    @staticmethod
    def get_categories(obj):
        """
        Return category names in the currently active language (like title does),
        avoiding duplicates and avoiding showing the same semantic category in
        multiple languages (caused by legacy per-language rows).

        Strategy:
        - Active language value (name_<lang>) wins.
        - If missing, fall back to English ONLY if no row already provided a
          translated value for that semantic slot.
        - Ignore rows that have neither an active-language value nor an English fallback.
        """
        from django.utils.translation import get_language

        lang = (get_language() or "en")[:2]
        lang_field = f"name_{lang}"

        cats = obj.categories.all()
        # First collect all explicit translations in the active language
        explicit_lang_values = {
            getattr(c, lang_field).strip() for c in cats if getattr(c, lang_field, None) and getattr(c, lang_field).strip()
        }

        seen = set()
        result = []
        for c in cats:
            val_lang = getattr(c, lang_field, None)
            val_lang = val_lang.strip() if val_lang else ""
            if val_lang:
                if val_lang not in seen:
                    seen.add(val_lang)
                    result.append(val_lang)
                continue
            # fallback to English only if there is NO active-language version in any row
            val_en = getattr(c, "name_en", None)
            val_en = val_en.strip() if val_en else ""
            if val_en and not explicit_lang_values and val_en not in seen:
                seen.add(val_en)
                result.append(val_en)
        return result


class CountryCapacityStrengtheningSerializer(ModelSerializer):
    assessment_type_display = serializers.CharField(read_only=True, source="get_assessment_type_display")

    class Meta:
        model = CountryCapacityStrengthening
        fields = "__all__"


class CountryOrganizationalCapacitySerializer(ModelSerializer):
    class Meta:
        model = CountryOrganizationalCapacity
        fields = "__all__"


class CountryICRCPresenceSerializer(ModelSerializer):
    class Meta:
        model = CountryICRCPresence
        fields = "__all__"


class CountryRelationSerializer(ModelSerializer):
    links = CountryLinkSerializer(many=True, read_only=True)
    contacts = CountryContactSerializer(many=True, read_only=True)
    has_country_plan = serializers.BooleanField(read_only=True)
    bbox = serializers.SerializerMethodField()
    centroid = serializers.SerializerMethodField()
    regions_details = RegionSerializer(source="region", read_only=True)
    directory = CountryDirectorySerializer(source="countrydirectory_set", read_only=True, many=True)
    initiatives = NSDInitiativesSerializer(source="nsdinitiatives_set", read_only=True, many=True)
    capacity = CountryCapacityStrengtheningSerializer(source="countrycapacitystrengthening_set", read_only=True, many=True)
    organizational_capacity = CountryOrganizationalCapacitySerializer(
        source="countryorganizationalcapacity",
        read_only=True,
    )
    icrc_presence = CountryICRCPresenceSerializer(
        source="countryicrcpresence",
        read_only=True,
    )
    country_delegation = serializers.SerializerMethodField()

    class Meta:
        model = Country
        fields = (
            "links",
            "contacts",
            "name",
            "iso",
            "iso3",
            "society_name",
            "society_url",
            "region",
            "overview",
            "key_priorities",
            "inform_score",
            "id",
            "url_ifrc",
            "additional_tab_name",
            "nsi_income",
            "nsi_expenditures",
            "nsi_branches",
            "nsi_staff",
            "nsi_volunteers",
            "nsi_youth",
            "nsi_trained_in_first_aid",
            "nsi_gov_financial_support",
            "nsi_domestically_generated_income",
            "nsi_annual_fdrs_reporting",
            "nsi_policy_implementation",
            "nsi_risk_management_framework",
            "nsi_cmc_dashboard_compliance",
            "wash_kit2",
            "wash_kit5",
            "wash_kit10",
            "wash_staff_at_hq",
            "wash_staff_at_branch",
            "wash_ndrt_trained",
            "wash_rdrt_trained",
            "has_country_plan",
            "bbox",
            "centroid",
            "fdrs",
            "regions_details",
            "address_1",
            "address_2",
            "city_code",
            "phone",
            "website",
            "emails",
            "directory",
            "initiatives",
            "capacity",
            "organizational_capacity",
            "icrc_presence",
            "disaster_law_url",
            "country_delegation",
            "independent",
            "sovereign_state_id",
        )

    @staticmethod
    def get_bbox(country) -> dict:
        return country.bbox and json.loads(country.bbox.geojson)

    @staticmethod
    def get_centroid(country) -> dict:
        return country.centroid and json.loads(country.centroid.geojson)

    @extend_schema_field(MiniDelegationOfficeSerializer(many=True))
    def get_country_delegation(self, country):
        return (
            DelegationOffice.objects.filter(
                country=country,
            )
            .values(
                "hod_first_name",
                "hod_last_name",
                "hod_mobile_number",
                "hod_email",
                "city",
                "address",
            )
            .annotate(dotype_name=models.F("dotype__name"))
            .distinct()
        )


class CountryKeyDocumentSerializer(ModelSerializer):
    country_details = MiniCountrySerializer(source="country", read_only=True)

    class Meta:
        model = CountryKeyDocument
        fields = "__all__"


class RelatedAppealSerializer(ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    atype_display = serializers.CharField(source="get_atype_display", read_only=True)

    class Meta:
        model = Appeal
        fields = (
            "aid",
            "num_beneficiaries",
            "amount_requested",
            "code",
            "amount_funded",
            "status",
            "status_display",
            "start_date",
            "end_date",
            "sector",
            "atype",
            "atype_display",
            "id",
        )


class KeyFigureSerializer(ModelSerializer):
    class Meta:
        model = KeyFigure
        fields = (
            "number",
            "deck",
            "source",
            "id",
        )


class SnippetSerializer(ModelSerializer):
    visibility_display = serializers.CharField(source="get_visibility_display", read_only=True)
    position_display = serializers.CharField(source="get_position_display", read_only=True)
    tab_display = serializers.CharField(source="get_tab_display", read_only=True)

    class Meta:
        model = Snippet
        fields = (
            "event",
            "snippet",
            "image",
            "id",
            "visibility",
            "visibility_display",
            "position",
            "position_display",
            "tab",
            "tab_display",
        )

    def validate_image(self, image):
        validate_file_type(image)
        return image


class EventContactSerializer(ModelSerializer):
    class Meta:
        model = EventContact
        fields = (
            "ctype",
            "name",
            "title",
            "email",
            "phone",
            "event",
            "id",
        )


class FieldReportContactSerializer(ModelSerializer):
    class Meta:
        model = FieldReportContact
        fields = (
            "ctype",
            "name",
            "title",
            "email",
            "phone",
            "id",
        )


class MiniFieldReportSerializer(ModelSerializer):
    contacts = FieldReportContactSerializer(many=True, read_only=True)
    countries = MiniCountrySerializer(many=True, read_only=True)
    epi_figures_source_display = serializers.CharField(source="get_epi_figures_source_display", read_only=True)
    visibility_display = serializers.CharField(source="get_visibility_display", read_only=True)

    class Meta:
        model = FieldReport
        fields = (
            "summary",
            "status",
            "description",
            "contacts",
            "countries",
            "created_at",
            "updated_at",
            "report_date",
            "id",
            "is_covid_report",
            "num_injured",
            "num_dead",
            "num_missing",
            "num_affected",
            "num_displaced",
            "epi_num_dead",
            "num_assisted",
            "num_localstaff",
            "num_volunteers",
            "num_expats_delegates",
            "gov_num_injured",
            "gov_num_dead",
            "gov_num_missing",
            "gov_num_affected",
            "gov_num_displaced",
            "gov_num_assisted",
            "other_num_injured",
            "other_num_dead",
            "other_num_missing",
            "other_num_affected",
            "other_num_displaced",
            "other_num_assisted",
            "num_potentially_affected",
            "gov_num_potentially_affected",
            "other_num_potentially_affected",
            "num_highest_risk",
            "gov_num_highest_risk",
            "other_num_highest_risk",
            "affected_pop_centres",
            "gov_affected_pop_centres",
            "other_affected_pop_centres",
            "epi_cases",
            "epi_suspected_cases",
            "epi_probable_cases",
            "epi_confirmed_cases",
            "epi_figures_source",
            "epi_figures_source_display",
            "epi_cases_since_last_fr",
            "epi_deaths_since_last_fr",
            "epi_notes_since_last_fr",
            "visibility",
            "visibility_display",
            "request_assistance",
            "ns_request_assistance",
            "notes_health",
            "notes_ns",
            "notes_socioeco",
            "recent_affected",
        )


class EventFeaturedDocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = EventFeaturedDocument
        fields = (
            "id",
            "title",
            "description",
            "thumbnail",
            "file",
        )

    def validate_thumbnail(self, thumbnail):
        validate_file_type(thumbnail)
        return thumbnail

    def validate_file(self, file):
        validate_file_type(file)
        return file


class EventLinkSerializer(ModelSerializer):
    class Meta:
        model = EventLink
        fields = (
            "id",
            "title",
            "description",
            "url",
        )


# The list serializer can include a smaller subset of the to-many fields.
# Also include a very minimal one for linking, and no other related fields.
class MiniEventSerializer(ModelSerializer):
    countries_for_preview = MiniCountrySerializer(many=True, read_only=True)
    dtype_details = DisasterTypeSerializer(read_only=True)

    class Meta:
        model = Event
        fields = (
            "name",
            "dtype",
            "id",
            "slug",
            "parent_event",
            "emergency_response_contact_email",
            "countries_for_preview",
            "start_date",
            "dtype_details",
        )


class ListMiniEventSerializer(ModelSerializer):
    dtype = DisasterTypeSerializer(required=False)
    countries_for_preview = MiniCountrySerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = (
            "id",
            "name",
            "slug",
            "dtype",
            "auto_generated_source",
            "emergency_response_contact_email",
            "countries_for_preview",
        )


class ListEventSerializer(ModelSerializer):
    appeals = RelatedAppealSerializer(many=True, read_only=True)
    countries = MiniCountrySerializer(many=True)
    field_reports = MiniFieldReportSerializer(many=True, read_only=True)
    dtype = DisasterTypeSerializer(required=False)
    ifrc_severity_level_display = serializers.CharField(source="get_ifrc_severity_level_display", read_only=True)
    active_deployments = serializers.IntegerField(read_only=True)

    class Meta:
        model = Event
        fields = (
            "name",
            "dtype",
            "countries",
            "summary",
            "num_affected",
            "ifrc_severity_level",
            "ifrc_severity_level_display",
            "ifrc_severity_level_update_date",
            "glide",
            "disaster_start_date",
            "created_at",
            "auto_generated",
            "appeals",
            "is_featured",
            "is_featured_region",
            "field_reports",
            "updated_at",
            "id",
            "slug",
            "parent_event",
            "tab_one_title",
            "tab_two_title",
            "tab_three_title",
            "emergency_response_contact_email",
            "active_deployments",
        )


# Instead of the below method we use the queryset's annotate tag:
#    def get_active_deployments(self, event) -> int:
#        now = timezone.now()
#        return Personnel.objects.filter(
#            type=Personnel.TypeChoices.RR,
#            start_date__lt=now,
#            end_date__gt=now,
#            deployment__event_deployed_to=event,
#            is_active=True,
#        ).count()


class SurgeEventSerializer(ModelSerializer):
    appeals = RelatedAppealSerializer(many=True, read_only=True)
    countries = MiniCountrySerializer(many=True)
    dtype = DisasterTypeSerializer(required=False)
    ifrc_severity_level_display = serializers.CharField(source="get_ifrc_severity_level_display", read_only=True)

    class Meta:
        model = Event
        fields = (
            "name",
            "dtype",
            "countries",
            "summary",
            "num_affected",
            "ifrc_severity_level",
            "ifrc_severity_level_display",
            "ifrc_severity_level_update_date",
            "glide",
            "disaster_start_date",
            "created_at",
            "auto_generated",
            "appeals",
            "is_featured",
            "is_featured_region",
            "updated_at",
            "id",
            "slug",
            "parent_event",
            "tab_one_title",
            "tab_two_title",
            "tab_three_title",
            "emergency_response_contact_email",  # omitted intentionally: field_reports
        )


class ListEventTableauSerializer(serializers.ModelSerializer):
    appeals = serializers.SerializerMethodField()
    field_reports = serializers.SerializerMethodField()
    countries = serializers.SerializerMethodField()
    dtype = DisasterTypeSerializer(required=False)
    ifrc_severity_level_display = serializers.CharField(source="get_ifrc_severity_level_display", read_only=True)

    @staticmethod
    def get_countries(obj):
        return get_merged_items_by_fields(obj.countries.all(), ["id", "name"])

    @staticmethod
    def get_field_reports(obj):
        return get_merged_items_by_fields(obj.field_reports.all(), ["id"])

    @staticmethod
    def get_appeals(obj):
        return get_merged_items_by_fields(obj.appeals.all(), ["id"])

    class Meta:
        model = Event
        fields = (
            "name",
            "dtype",
            "countries",
            "summary",
            "num_affected",
            "ifrc_severity_level",
            "ifrc_severity_level_display",
            "ifrc_severity_level_update_date",
            "glide",
            "disaster_start_date",
            "created_at",
            "auto_generated",
            "appeals",
            "is_featured",
            "is_featured_region",
            "field_reports",
            "updated_at",
            "id",
            "slug",
            "parent_event",
        )


class ListEventCsvSerializer(serializers.ModelSerializer):
    appeals = serializers.SerializerMethodField()
    field_reports = serializers.SerializerMethodField()
    countries = serializers.SerializerMethodField()
    dtype = DisasterTypeSerializer(required=False)
    ifrc_severity_level_display = serializers.CharField(source="get_ifrc_severity_level_display", read_only=True)

    @staticmethod
    def get_countries(obj):
        return get_merged_items_by_fields(obj.countries.all(), ["id", "name", "iso", "iso3", "society_name"])

    @staticmethod
    def get_field_reports(obj):
        return get_merged_items_by_fields(obj.field_reports.all(), ["id"])

    @staticmethod
    def get_appeals(obj):
        return get_merged_items_by_fields(obj.appeals.all(), ["id"])

    class Meta:
        model = Event
        fields = (
            "name",
            "dtype",
            "countries",
            "summary",
            "num_affected",
            "ifrc_severity_level",
            "ifrc_severity_level_display",
            "ifrc_severity_level_update_date",
            "glide",
            "disaster_start_date",
            "created_at",
            "auto_generated",
            "appeals",
            "is_featured",
            "is_featured_region",
            "field_reports",
            "updated_at",
            "id",
            "slug",
            "parent_event",
        )


class ListEventForPersonnelCsvSerializer(serializers.ModelSerializer):
    appeals = serializers.SerializerMethodField()
    field_reports = serializers.SerializerMethodField()
    countries = serializers.SerializerMethodField()
    dtype_name = serializers.SerializerMethodField()

    # NOTE: prefetched at deployments/drf_views.py::PersonnelViewset::get_queryset
    @staticmethod
    def get_countries(obj):
        fields = ["id", "name", "iso", "iso3", "society_name"]
        return get_merged_items_by_fields(obj.countries.all(), fields)

    @staticmethod
    def get_field_reports(obj):
        fields = ["id"]
        return get_merged_items_by_fields(obj.field_reports.all(), fields)

    @staticmethod
    def get_appeals(obj):
        fields = ["id", "status"]
        return get_merged_items_by_fields(obj.appeals.all(), fields)

    @staticmethod
    def get_dtype_name(obj):
        return obj.dtype and obj.dtype.name

    class Meta:
        model = Event
        fields = (
            "name",
            "dtype_name",
            "countries",
            "summary",
            "num_affected",
            "ifrc_severity_level",
            "glide",
            "disaster_start_date",
            "created_at",
            "appeals",
            "field_reports",
            "updated_at",
            "id",
            "parent_event",
        )


class SmallEventForPersonnelCsvSerializer(serializers.ModelSerializer):
    countries = serializers.SerializerMethodField()
    dtype_name = serializers.SerializerMethodField()

    @staticmethod
    def get_countries(obj):
        fields = ["name", "iso3", "society_name", "region"]
        return get_merged_items_by_fields(obj.countries.all(), fields)

    @staticmethod
    def get_dtype_name(obj):
        return obj.dtype and obj.dtype.name

    class Meta:
        model = Event
        fields = ("name", "dtype_name", "countries", "ifrc_severity_level", "glide", "id")


class ListEventDeploymentsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    deployments = serializers.IntegerField()


class MiniPersonnelSerializer(serializers.ModelSerializer):
    country_from = MiniCountrySerializer()

    class Meta:
        model = Personnel
        fields = (
            "id",
            "role",
            "name",
            "start_date",
            "end_date",
            "country_from",
        )


class MiniPersonnelDeploymentSerializer(serializers.ModelSerializer):
    personnel = MiniPersonnelSerializer(source="personnel_set", many=True)
    country_deployed_to = MiniCountrySerializer()

    class Meta:
        model = PersonnelDeployment
        fields = (
            "id",
            "personnel",
            "country_deployed_to",
        )


class DeploymentsByEventSerializer(ModelSerializer):
    deployments = MiniPersonnelDeploymentSerializer(source="personneldeployment_set", many=True, read_only=True)
    appeals = RelatedAppealSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = (
            "id",
            "name",
            "disaster_start_date",
            "deployments",
            "appeals",
        )


class DetailEventSerializer(ModelSerializer):
    appeals = RelatedAppealSerializer(many=True, read_only=True)
    contacts = EventContactSerializer(many=True, read_only=True)
    key_figures = KeyFigureSerializer(many=True, read_only=True)
    districts = MiniDistrictSerializer(many=True)
    countries = MiniCountrySerializer(many=True)
    field_reports = MiniFieldReportSerializer(many=True, read_only=True)
    ifrc_severity_level_display = serializers.CharField(source="get_ifrc_severity_level_display", read_only=True)
    featured_documents = EventFeaturedDocumentSerializer(many=True, read_only=True)
    links = EventLinkSerializer(many=True, read_only=True)
    countries_for_preview = MiniCountrySerializer(many=True)
    response_activity_count = serializers.SerializerMethodField()
    active_deployments = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            "name",
            "dtype",
            "countries",
            "districts",
            "summary",
            "num_affected",
            "tab_two_title",
            "tab_three_title",
            "disaster_start_date",
            "created_at",
            "auto_generated",
            "appeals",
            "contacts",
            "key_figures",
            "is_featured",
            "is_featured_region",
            "field_reports",
            "hide_attached_field_reports",
            "hide_field_report_map",
            "updated_at",
            "id",
            "slug",
            "tab_one_title",
            "ifrc_severity_level",
            "ifrc_severity_level_display",
            "ifrc_severity_level_update_date",
            "parent_event",
            "glide",
            "featured_documents",
            "links",
            "emergency_response_contact_email",
            "countries_for_preview",
            "response_activity_count",
            "visibility",
            "active_deployments",
        )
        lookup_field = "slug"

    def get_response_activity_count(self, event) -> int:
        return EmergencyProject.objects.filter(event=event).count()

    def get_active_deployments(self, event) -> int:
        now = timezone.now()
        return Personnel.objects.filter(
            type=Personnel.TypeChoices.RR,
            start_date__lt=now,
            end_date__gt=now,
            deployment__event_deployed_to=event,
            is_active=True,
        ).count()


class SituationReportTypeSerializer(serializers.ModelSerializer):
    type = serializers.CharField(allow_null=False, allow_blank=False, required=True)

    class Meta:
        model = SituationReportType
        fields = (
            "type",
            "id",
            "is_primary",
        )


class SituationReportTableauSerializer(ModelSerializer):
    type = SituationReportTypeSerializer()
    event = MiniEventSerializer()
    visibility_display = serializers.CharField(source="get_visibility_display", read_only=True)

    class Meta:
        model = SituationReport
        fields = (
            "created_at",
            "name",
            "document",
            "document_url",
            "event",
            "type",
            "id",
            "is_pinned",
            "visibility",
            "visibility_display",
        )


class SituationReportSerializer(serializers.ModelSerializer):
    type = SituationReportTypeSerializer()
    visibility_display = serializers.CharField(source="get_visibility_display", read_only=True)

    class Meta:
        model = SituationReport
        fields = (
            "created_at",
            "name",
            "document",
            "document_url",
            "event",
            "type",
            "id",
            "is_pinned",
            "visibility",
            "visibility_display",
        )

    def validate_document(self, document):
        validate_file_type(document)
        return document


class AppealTableauSerializer(serializers.ModelSerializer):
    country = MiniCountrySerializer()
    dtype = DisasterTypeSerializer()
    region = RegionSerializer()
    event = MiniEventSerializer()
    atype_display = serializers.CharField(source="get_atype_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Appeal
        fields = (
            "aid",
            "name",
            "dtype",
            "atype",
            "atype_display",
            "status",
            "status_display",
            "code",
            "sector",
            "num_beneficiaries",
            "amount_requested",
            "amount_funded",
            "start_date",
            "end_date",
            "real_data_update",
            "created_at",
            "modified_at",
            "event",
            "needs_confirmation",
            "country",
            "region",
            "id",
        )


class AppealHistoryTableauSerializer(serializers.ModelSerializer):
    country = MiniCountrySerializer(read_only=True)
    dtype = DisasterTypeSerializer(read_only=True)
    region = RegionSerializer(read_only=True)
    atype_display = serializers.CharField(source="get_atype_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    code = serializers.CharField(source="appeal.code", read_only=True)
    sector = serializers.CharField(source="appeal.sector", read_only=True)
    created_at = serializers.CharField(source="appeal.created_at", read_only=True)
    modified_at = serializers.CharField(source="appeal.modified_at", read_only=True)
    real_data_update = serializers.CharField(source="appeal.real_data_update", read_only=True)
    event = serializers.CharField(source="appeal.event", read_only=True)
    id = serializers.CharField(source="appeal.id", read_only=True)
    name = serializers.CharField(source="appeal.name", read_only=True)

    class Meta:
        model = AppealHistory
        fields = (
            "aid",
            "name",
            "dtype",
            "atype",
            "atype_display",
            "status",
            "status_display",
            "code",
            "sector",
            "num_beneficiaries",
            "amount_requested",
            "amount_funded",
            "start_date",
            "end_date",
            "real_data_update",
            "created_at",
            "modified_at",
            "event",
            "needs_confirmation",
            "country",
            "region",
            "id",
        )


class MiniAppealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appeal
        fields = ("name", "id", "code")


class AppealSerializer(ModelSerializer):
    country = MiniCountrySerializer(read_only=True)
    dtype = DisasterTypeSerializer(read_only=True)
    region = RegionSerializer(read_only=True)
    atype_display = serializers.CharField(source="get_atype_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Appeal
        fields = (
            "aid",
            "name",
            "dtype",
            "atype",
            "atype_display",
            "status",
            "status_display",
            "code",
            "sector",
            "num_beneficiaries",
            "amount_requested",
            "amount_funded",
            "start_date",
            "end_date",
            "real_data_update",
            "created_at",
            "modified_at",
            "event",
            "needs_confirmation",
            "country",
            "region",
            "id",
        )


class AppealHistorySerializer(ModelSerializer):
    country = MiniCountrySerializer(read_only=True)
    dtype = DisasterTypeSerializer(read_only=True)
    region = RegionSerializer(read_only=True)
    atype_display = serializers.CharField(source="get_atype_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    code = serializers.CharField(source="appeal.code", read_only=True)
    sector = serializers.CharField(source="appeal.sector", read_only=True)
    created_at = serializers.CharField(source="appeal.created_at", read_only=True)
    modified_at = serializers.CharField(source="appeal.modified_at", read_only=True)
    real_data_update = serializers.CharField(source="appeal.real_data_update", read_only=True)
    event = serializers.IntegerField(source="appeal.event_id", read_only=True)
    id = serializers.CharField(source="appeal.id", read_only=True)
    name = serializers.CharField(source="appeal.name", read_only=True)

    class Meta:
        model = AppealHistory
        fields = (
            "aid",
            "name",
            "dtype",
            "atype",
            "atype_display",
            "status",
            "status_display",
            "code",
            "sector",
            "num_beneficiaries",
            "amount_requested",
            "amount_funded",
            "start_date",
            "end_date",
            "real_data_update",
            "created_at",
            "modified_at",
            "event",
            "needs_confirmation",
            "country",
            "region",
            "id",
        )


class AppealDocumentTableauSerializer(serializers.ModelSerializer):
    appeal = MiniAppealSerializer()

    class Meta:
        model = AppealDocument
        fields = (
            "created_at",
            "name",
            "document",
            "document_url",
            "appeal",
            "id",
        )


class AppealDocumentAppealSerializer(serializers.ModelSerializer):
    event = MiniEventSerializer(read_only=True)

    class Meta:
        model = Appeal
        fields = (
            "id",
            "code",
            "event",
            "start_date",
        )


class AppealDocumentSerializer(ModelSerializer):
    appeal = AppealDocumentAppealSerializer(read_only=True)
    type = serializers.CharField(source="type.name", read_only=True)  # seems to be identical to the appealdoc name

    class Meta:
        model = AppealDocument
        fields = (
            "created_at",
            "name",
            "document",
            "document_url",
            "appeal",
            "type",
            "iso",
            "description",
            "id",
        )

    def validate_document(self, document):
        validate_file_type(document)
        return document


class ProfileSerializer(ModelSerializer):
    country = MiniCountrySerializer()

    class Meta:
        model = Profile
        fields = (
            "country",
            "org",
            "org_type",
            "city",
            "department",
            "position",
            "phone_number",
            "accepted_montandon_license_terms",
        )


class MiniSubscriptionSerializer(ModelSerializer):
    class Meta:
        model = Subscription
        fields = (
            "stype",
            "rtype",
            "country",
            "region",
            "event",
            "dtype",
            "lookup_id",
        )


class UserSerializer(ModelSerializer):
    profile = ProfileSerializer()
    subscription = MiniSubscriptionSerializer(many=True)
    is_ifrc_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "profile",
            "subscription",
            "is_superuser",
            "is_ifrc_admin",
        )

    def create(self, _):
        raise serializers.ValidationError("Create is not allowed")

    def update(self, instance, validated_data):
        if "profile" in validated_data:
            profile_data = validated_data.pop("profile")
            profile = Profile.objects.get(user=instance)
            profile.city = profile_data.get("city", profile.city)
            profile.org = profile_data.get("org", profile.org)
            profile.org_type = profile_data.get("org_type", profile.org_type)
            profile.department = profile_data.get("department", profile.department)
            profile.position = profile_data.get("position", profile.position)
            profile.phone_number = profile_data.get("phone_number", profile.phone_number)
            profile.country = profile_data.get("country", profile.country)
            profile.save()
        # TODO: Do we allow this to change as well?
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.email = validated_data.get("email", instance.email)
        instance.save()
        return instance


# Instead of the below method we use the queryset's annotate tag:
#    @staticmethod
#    def get_is_ifrc_admin(obj) -> bool:
#        return obj.groups.filter(name__iexact="IFRC Admins").exists()


class UserNameSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name")


class MiniRegionSerialzier(serializers.ModelSerializer):
    name = serializers.CharField(source="get_name_display", read_only=True)

    class Meta:
        model = Region
        fields = ("id", "name")


class UserCountryCountrySerializer(serializers.ModelSerializer):
    region_details = MiniRegionSerialzier(source="region", read_only=True)

    class Meta:
        model = Country
        fields = ("id", "name", "region", "region_details")


class UserCountrySerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.name", read_only=True)
    region = serializers.IntegerField(source="country.region.name", read_only=True)
    region_details = MiniRegionSerialzier(source="country.region", read_only=True)

    class Meta:
        model = UserCountry
        exclude = ("id", "user")


class UserMeSerializer(UserSerializer):
    is_admin_for_countries = serializers.SerializerMethodField()
    is_admin_for_regions = serializers.SerializerMethodField()
    lang_permissions = serializers.SerializerMethodField()
    is_dref_coordinator_for_regions = serializers.SerializerMethodField()
    is_per_admin_for_regions = serializers.SerializerMethodField()
    is_per_admin_for_countries = serializers.SerializerMethodField()
    user_countries_regions = serializers.SerializerMethodField()
    limit_access_to_guest = serializers.BooleanField(read_only=True, source="profile.limit_access_to_guest")

    local_unit_country_validators = serializers.SerializerMethodField()
    local_unit_region_validators = serializers.SerializerMethodField()
    local_unit_global_validators = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + (
            "is_admin_for_countries",
            "is_admin_for_regions",
            "lang_permissions",
            "is_dref_coordinator_for_regions",
            "is_per_admin_for_regions",
            "is_per_admin_for_countries",
            "user_countries_regions",
            "limit_access_to_guest",
            "local_unit_country_validators",
            "local_unit_region_validators",
            "local_unit_global_validators",
        )

    @staticmethod
    def get_is_admin_for_countries(user) -> List[int]:
        return set(
            [
                int(permission[18:])
                for permission in user.get_all_permissions()
                if ("api.country_admin_" in permission and permission[18:].isdigit())
            ]
        )

    @staticmethod
    def get_is_admin_for_regions(user) -> List[int]:
        return set(
            [
                int(permission[17:])
                for permission in user.get_all_permissions()
                if ("api.region_admin_" in permission and permission[17:].isdigit())
            ]
        )

    @staticmethod
    def get_lang_permissions(user) -> dict:
        return String.get_user_permissions_per_language(user)

    @staticmethod
    def get_is_dref_coordinator_for_regions(user) -> List[int]:
        data = list(
            Permission.objects.filter(codename__startswith="dref_region_admin_", group__user=user).values_list(
                "codename", flat=True
            )
        )
        regions = []
        for d in data:
            splitted = d.split("_")[-1]
            regions.append(int(splitted))
        return set(regions)

    @staticmethod
    def get_is_per_admin_for_regions(user) -> List[int]:
        permission_codenames = Permission.objects.filter(codename__startswith="per_region_admin", group__user=user).values_list(
            "codename", flat=True
        )

        regions = {int(code.split("_")[-1]) for code in permission_codenames}
        return list(regions)

    @staticmethod
    def get_is_per_admin_for_countries(user) -> List[int]:
        permission_codenames = Permission.objects.filter(codename__startswith="per_country_admin", group__user=user).values_list(
            "codename", flat=True
        )

        countries = {int(code.split("_")[-1]) for code in permission_codenames}
        return list(countries)

    @staticmethod
    @extend_schema_field(UserCountrySerializer(many=True))
    def get_user_countries_regions(user):
        qs = UserCountry.objects.filter(user=user).distinct("country")
        return UserCountrySerializer(qs, many=True).data

    @staticmethod
    def get_local_unit_global_validators(user) -> List[int]:
        permission_codenames = Permission.objects.filter(
            codename__startswith="local_unit_global_validator", group__user=user
        ).values_list("codename", flat=True)
        global_validators = {int(code.split("_")[-1]) for code in permission_codenames}
        return list(global_validators)

    @staticmethod
    def get_local_unit_region_validators(user) -> list[RegionValidator]:
        permission_codenames = Permission.objects.filter(
            codename__startswith="local_unit_region_validator",
            group__user=user,
        ).values_list("codename", flat=True)
        region_validators = defaultdict(set)
        for code in permission_codenames:
            parts = code.split("_")[-2:]
            if len(parts) == 2 and all(p.isdigit() for p in parts):
                local_unit_type_id = int(parts[0])
                region_id = int(parts[1])
                region_validators[region_id].add(local_unit_type_id)
        return [
            {"region": region, "local_unit_types": list(local_unit_types)}
            for region, local_unit_types in region_validators.items()
        ]

    @staticmethod
    def get_local_unit_country_validators(user) -> list[CountryValidator]:
        permission_codenames = Permission.objects.filter(
            codename__startswith="local_unit_country_validator", group__user=user
        ).values_list("codename", flat=True)
        country_validator = defaultdict(set)
        for code in permission_codenames:
            parts = code.split("_")[-2:]
            if len(parts) == 2 and all(p.isdigit() for p in parts):
                local_unit_type_id = int(parts[0])
                country_id = int(parts[1])
                country_validator[country_id].add(local_unit_type_id)
        return [
            {"country": country, "local_unit_types": list(local_unit_types)}
            for country, local_unit_types in country_validator.items()
        ]


class ActionSerializer(ModelSerializer):
    class Meta:
        model = Action
        fields = ("name", "id", "organizations", "field_report_types", "category", "tooltip_text")


class ActionsTakenSerializer(ModelSerializer):
    actions_details = ActionSerializer(many=True, read_only=True, source="actions")

    class Meta:
        model = ActionsTaken
        fields = (
            "organization",
            "actions",
            "summary",
            "actions_details",
            "id",
        )


class ExternalPartnerSerializer(ModelSerializer):
    class Meta:
        model = ExternalPartner
        fields = ("name", "id")


class SupportedActivitySerializer(ModelSerializer):
    class Meta:
        model = SupportedActivity
        fields = ("name", "id")


class SourceSerializer(ModelSerializer):
    class Meta:
        model = Source
        fields = (
            "stype",
            "spec",
            "id",
        )


class FieldReportEnumDisplayMixin:
    """
    Use for fields = "__all__"
    """

    epi_figures_source_display = serializers.CharField(source="get_epi_figures_source_display", read_only=True)
    visibility_display = serializers.CharField(source="get_visibility_display", read_only=True)
    bulletin_display = serializers.CharField(source="get_bulletin_display", read_only=True)
    dref_display = serializers.CharField(source="get_dref_display", read_only=True)
    appeal_display = serializers.CharField(source="get_appeal_display", read_only=True)
    imminent_dref_display = serializers.CharField(source="get_imminent_dref_display", read_only=True)
    forecast_based_action_display = serializers.CharField(source="get_forecast_based_action_display", read_only=True)
    rdrt_display = serializers.CharField(source="get_rdrt_display", read_only=True)
    fact_display = serializers.CharField(source="get_fact_display", read_only=True)
    emergency_response_unit_display = serializers.CharField(source="get_emergency_response_unit_display", read_only=True)
    eru_base_camp_display = serializers.CharField(source="get_eru_base_camp_display", read_only=True)
    eru_basic_health_care_display = serializers.CharField(source="get_eru_basic_health_care_display", read_only=True)
    eru_it_telecom_display = serializers.CharField(source="get_eru_it_telecom_display", read_only=True)
    eru_logistics_display = serializers.CharField(source="get_eru_logistics_display", read_only=True)
    eru_deployment_hospital_display = serializers.CharField(source="get_eru_deployment_hospital_display", read_only=True)
    eru_referral_hospital_display = serializers.CharField(source="get_eru_referral_hospital_display", read_only=True)
    eru_relief_display = serializers.CharField(source="get_eru_relief_display", read_only=True)
    eru_water_sanitation_15_display = serializers.CharField(source="get_eru_water_sanitation_15_display", read_only=True)
    eru_water_sanitation_40_display = serializers.CharField(source="get_eru_water_sanitation_40_display", read_only=True)
    eru_water_sanitation_20_display = serializers.CharField(source="get_eru_water_sanitation_20_display", read_only=True)


class ListFieldReportSerializer(FieldReportEnumDisplayMixin, ModelSerializer):
    countries = MiniCountrySerializer(many=True)
    dtype = DisasterTypeSerializer()
    event = MiniEventSerializer()
    actions_taken = ActionsTakenSerializer(many=True)

    class Meta:
        model = FieldReport
        fields = "__all__"


class ListFieldReportTableauSerializer(FieldReportEnumDisplayMixin, ModelSerializer):
    countries = serializers.SerializerMethodField()
    districts = serializers.SerializerMethodField()
    regions = serializers.SerializerMethodField()
    dtype = DisasterTypeSerializer()
    event = MiniEventSerializer()
    actions_taken = serializers.SerializerMethodField("get_actions_taken_for_organization")

    @staticmethod
    def get_countries(obj):
        return get_merged_items_by_fields(obj.countries.all(), ["id", "name"])

    @staticmethod
    def get_districts(obj):
        return get_merged_items_by_fields(obj.districts.all(), ["id", "name"])

    @staticmethod
    def get_regions(obj):
        return get_merged_items_by_fields(obj.regions.all(), ["id", "region_name"])

    @staticmethod
    def get_actions_taken_for_organization(obj):
        actions_data = {}
        actions_taken = obj.actions_taken.all()
        for action in actions_taken:
            if action.organization not in actions_data:
                actions_data[action.organization] = []
            this_action = {
                "actions_name": [a.name for a in action.actions.all()],
                "actions_id": [a.id for a in action.actions.all()],
            }
            actions_data[action.organization] = {"action": json.dumps(this_action), "summary": action.summary}
        return actions_data

    class Meta:
        model = FieldReport
        fields = "__all__"


class ListFieldReportCsvSerializer(FieldReportEnumDisplayMixin, ModelSerializer):
    countries = serializers.SerializerMethodField()
    districts = serializers.SerializerMethodField()
    regions = serializers.SerializerMethodField()
    dtype = DisasterTypeSerializer()
    event = MiniEventSerializer()
    actions_taken = serializers.SerializerMethodField("get_actions_taken_for_organization")

    @staticmethod
    def get_countries(obj):
        return get_merged_items_by_fields(obj.countries.all(), ["id", "name", "iso", "iso3", "society_name"])

    @staticmethod
    def get_districts(obj):
        return get_merged_items_by_fields(obj.districts.all(), ["id", "name"])

    @staticmethod
    def get_regions(obj):
        return get_merged_items_by_fields(obj.regions.all(), ["id", "region_name"])

    @staticmethod
    def get_actions_taken_for_organization(obj):
        actions_data = {}
        actions_taken = obj.actions_taken.all()
        for action in actions_taken:
            if action.organization not in actions_data:
                actions_data[action.organization] = []
            this_action = {
                "actions_name": [a.name for a in action.actions.all()],
                "actions_id": [a.id for a in action.actions.all()],
            }
            actions_data[action.organization] = {"action": json.dumps(this_action), "summary": action.summary}
        return actions_data

    class Meta:
        model = FieldReport
        fields = "__all__"


class DetailFieldReportSerializer(FieldReportEnumDisplayMixin, ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for i, field in enumerate(
            [
                "num_affected",
                "gov_num_affected",
                "other_num_affected",
                "num_potentially_affected",
                "gov_num_potentially_affected",
                "other_num_potentially_affected",
            ]
        ):
            # We allow only 1 of these _affected values ^, pointed by RecentAffected. The other 5 gets 0 on client side.
            # About "recent_affected - 1" as index see (¤) in other code parts:
            if self.instance and self.instance.recent_affected - 1 != i:
                self.fields.pop(field)

    user = UserSerializer()
    dtype = DisasterTypeSerializer()
    contacts = FieldReportContactSerializer(many=True)
    actions_taken = ActionsTakenSerializer(many=True)
    sources = SourceSerializer(many=True)
    event = MiniEventSerializer()
    countries = MiniCountrySerializer(many=True)
    districts = MiniDistrictSerializer(many=True)
    external_partners = ExternalPartnerSerializer(many=True)
    supported_activities = SupportedActivitySerializer(many=True)
    regions = RegionSerializer(many=True)
    visibility_display = serializers.CharField(source="get_visibility_display", read_only=True)

    class Meta:
        model = FieldReport
        exclude = ()


class FieldReportMiniUserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")


class FieldReportSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    ModelSerializer,
):
    epi_figures_source_display = serializers.CharField(source="get_epi_figures_source_display", read_only=True)
    visibility_display = serializers.CharField(source="get_visibility_display", read_only=True)
    bulletin_display = serializers.CharField(source="get_bulletin_display", read_only=True)
    dref_display = serializers.CharField(source="get_dref_display", read_only=True)
    appeal_display = serializers.CharField(source="get_appeal_display", read_only=True)
    imminent_dref_display = serializers.CharField(source="get_imminent_dref_display", read_only=True)
    forecast_based_action_display = serializers.CharField(source="get_forecast_based_action_display", read_only=True)
    rdrt_display = serializers.CharField(source="get_rdrt_display", read_only=True)
    fact_display = serializers.CharField(source="get_fact_display", read_only=True)
    emergency_response_unit_display = serializers.CharField(source="get_emergency_response_unit_display", read_only=True)
    eru_base_camp_display = serializers.CharField(source="get_eru_base_camp_display", read_only=True)
    eru_basic_health_care_display = serializers.CharField(source="get_eru_basic_health_care_display", read_only=True)
    eru_it_telecom_display = serializers.CharField(source="get_eru_it_telecom_display", read_only=True)
    eru_logistics_display = serializers.CharField(source="get_eru_logistics_display", read_only=True)
    eru_deployment_hospital_display = serializers.CharField(source="get_eru_deployment_hospital_display", read_only=True)
    eru_referral_hospital_display = serializers.CharField(source="get_eru_referral_hospital_display", read_only=True)
    eru_relief_display = serializers.CharField(source="get_eru_relief_display", read_only=True)
    eru_water_sanitation_15_display = serializers.CharField(source="get_eru_water_sanitation_15_display", read_only=True)
    eru_water_sanitation_40_display = serializers.CharField(source="get_eru_water_sanitation_40_display", read_only=True)
    eru_water_sanitation_20_display = serializers.CharField(source="get_eru_water_sanitation_20_display", read_only=True)
    actions_taken = ActionsTakenSerializer(many=True, required=False)
    contacts = FieldReportContactSerializer(many=True, required=False)
    sources = SourceSerializer(many=True, required=False)
    countries_details = MiniCountrySerializer(source="countries", many=True, read_only=True)
    districts_details = MiniDistrictSerializer(source="districts", many=True, read_only=True)
    regions_details = RegionSerializer(source="regions", many=True, read_only=True)
    event_details = MiniEventSerializer(source="event", read_only=True)
    dtype_details = DisasterTypeSerializer(source="dtype", read_only=True)
    external_partners_details = ExternalPartnerSerializer(source="external_partners", many=True, read_only=True)
    supported_activities_details = SupportedActivitySerializer(source="supported_activities", many=True, read_only=True)
    user_details = FieldReportMiniUserSerializer(source="user", read_only=True)

    class Meta:
        model = FieldReport
        fields = "__all__"
        read_only_fields = ("summary",)

    def create_event(self, report):
        event = Event.objects.create(
            name=report.summary,
            dtype=report.dtype,
            summary=report.description or "",
            disaster_start_date=report.start_date,
            auto_generated=True,
            auto_generated_source=SOURCES["new_report"],
            visibility=report.visibility,
            **{TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME: django_get_language()},
        )
        event.countries.add(*report.countries.all())
        event.districts.add(*report.districts.all())
        event.regions.add(*report.regions.all())
        FieldReportSerializer.trigger_field_translation(event)
        report.event = event
        report.save(update_fields=["event"])

    def validate(self, data):
        # Set RecentAffected according to the sent _affected key – see (¤) in other code parts
        if "status" in data and data["status"] == FieldReport.Status.EW:  # Early Warning
            if "num_potentially_affected" in data:
                data["recent_affected"] = FieldReport.RecentAffected.RCRC_POTENTIALLY
            elif "gov_num_potentially_affected" in data:
                data["recent_affected"] = FieldReport.RecentAffected.GOVERNMENT_POTENTIALLY
            elif "other_num_potentially_affected" in data:
                data["recent_affected"] = FieldReport.RecentAffected.OTHER_POTENTIALLY
        else:  # Event related
            if "num_affected" in data:
                data["recent_affected"] = FieldReport.RecentAffected.RCRC
            elif "gov_num_affected" in data:
                data["recent_affected"] = FieldReport.RecentAffected.GOVERNMENT
            elif "other_num_affected" in data:
                data["recent_affected"] = FieldReport.RecentAffected.OTHER
        return data

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        countries = validated_data["countries"]
        field_report = super().create(validated_data)
        # also add regions for the coutries selected
        field_report.regions.add(*[country.region for country in countries if (country.region is not None)])
        if field_report.event is None:
            self.create_event(field_report)
        return field_report

    def update(self, instance, validated_data):
        # NOTE: Set fr_num to None if event is changed
        if validated_data.get("event") != instance.event:
            instance.fr_num = None
        validated_data["user"] = self.context["request"].user
        return super().update(instance, validated_data)


class FieldReportGenerateTitleSerializer(serializers.ModelSerializer):
    dtype = serializers.PrimaryKeyRelatedField(queryset=DisasterType.objects.all())
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all(), required=False)
    title = serializers.CharField(required=True)
    id = serializers.IntegerField(required=False)

    class Meta:
        model = FieldReport
        fields = (
            "id",
            "countries",
            "dtype",
            "title",
            "event",
            "start_date",
            "is_covid_report",
        )


class FieldReportGeneratedTitleSerializer(serializers.Serializer):
    title = serializers.CharField()


class MainContactSerializer(ModelSerializer):
    class Meta:
        model = MainContact
        fields = "__all__"


class NsSerializer(ModelSerializer):
    class Meta:
        model = Country
        fields = ("url_ifrc",)


class GoHistoricalSerializer(ModelSerializer):
    appeals = RelatedAppealSerializer(many=True, read_only=True)
    countries = MiniCountrySerializer(many=True)
    dtype = DisasterTypeSerializer()

    class Meta:
        model = Event
        fields = (
            "id",
            "name",
            "dtype",
            "countries",
            "num_affected",
            "disaster_start_date",
            "created_at",
            "appeals",
        )


class CountryOfFieldReportToReviewSerializer(ModelSerializer):
    class Meta:
        model = CountryOfFieldReportToReview
        fields = "__all__"


class AggregateHeaderFiguresInputSerializer(serializers.Serializer):
    iso3 = serializers.IntegerField(required=False)
    country = serializers.IntegerField(required=False)
    region = serializers.IntegerField(required=False)
    date = serializers.DateTimeField(required=False)


class AggregateHeaderFiguresSerializer(serializers.Serializer):
    active_drefs = serializers.IntegerField()
    active_appeals = serializers.IntegerField()
    total_appeals = serializers.IntegerField()
    target_population = serializers.IntegerField()
    amount_requested = serializers.IntegerField()
    amount_requested_dref_included = serializers.IntegerField()
    amount_funded = serializers.IntegerField()
    amount_funded_dref_included = serializers.IntegerField()


# SearchPage Serializer
class SearchRegionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    score = serializers.FloatField()


class SearchDistrictSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    country = serializers.CharField()
    country_id = serializers.IntegerField()
    score = serializers.FloatField()


class SearchCountrySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    society_name = serializers.CharField()
    iso3 = serializers.CharField()
    score = serializers.FloatField()


class SearchMiniCountrySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class SearchMiniAppealSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    atype = serializers.CharField()


class SearchEmergencySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    disaster_type = serializers.CharField()
    funding_requirements = serializers.CharField()
    funding_coverage = serializers.CharField()
    start_date = serializers.DateTimeField()
    countries = SearchMiniCountrySerializer(many=True)
    # countries_id = serializers.ListField(child=serializers.IntegerField())
    # iso3 = serializers.ListField(child=serializers.CharField())
    severity_level_display = serializers.CharField()
    appeals = SearchMiniAppealSerializer(many=True)
    score = serializers.FloatField()
    severity_level = serializers.IntegerField()


class SearchSurgeAlertSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    keywords = serializers.ListField(child=serializers.CharField())
    event_name = serializers.CharField()
    country = serializers.CharField()
    start_date = serializers.DateTimeField()
    alert_date = serializers.DateTimeField()
    event_id = serializers.IntegerField()
    status = serializers.CharField()
    deadline = serializers.CharField()
    surge_type = serializers.CharField()
    country_id = serializers.IntegerField()
    score = serializers.FloatField()


class SearchProjectsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    event_name = serializers.CharField()
    national_society = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField())
    sector = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    regions = serializers.ListField(child=serializers.CharField())
    people_targeted = serializers.IntegerField()
    event_id = serializers.IntegerField()
    national_society_id = serializers.IntegerField()
    score = serializers.FloatField()


class SearchSurgeDeploymentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    event_name = serializers.CharField()
    deployed_country = serializers.CharField()
    type = serializers.CharField()
    owner = serializers.CharField()
    personnel_units = serializers.IntegerField()
    equipment_units = serializers.IntegerField()
    event_id = serializers.IntegerField()
    deployed_country_id = serializers.IntegerField()
    deployed_country_name = serializers.CharField()
    score = serializers.FloatField()


class SearchRapidResponseDeploymentsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    event_name = serializers.CharField()
    event_id = serializers.IntegerField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    position = serializers.CharField(allow_null=True)
    type = serializers.CharField()
    deploying_country_name = serializers.CharField()
    deploying_country_id = serializers.IntegerField()
    deployed_to_country_name = serializers.CharField()
    deployed_to_country_id = serializers.IntegerField()
    score = serializers.FloatField()


class SearchReportSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    created_at = serializers.DateTimeField()
    type = serializers.CharField()
    score = serializers.FloatField()


class SearchInputSerializer(serializers.Serializer):
    keyword = serializers.CharField(required=True)


class SearchSerializer(serializers.Serializer):
    regions = SearchRegionSerializer(many=True, required=False, allow_null=True)
    district_province_response = SearchDistrictSerializer(many=True, required=False, allow_null=True)
    countries = SearchCountrySerializer(many=True, required=False, allow_null=True)
    emergencies = SearchEmergencySerializer(many=True, required=False, allow_null=True)
    surge_alerts = SearchSurgeAlertSerializer(many=True, required=False, allow_null=True)
    projects = SearchProjectsSerializer(many=True, required=False, allow_null=True)
    surge_deployments = SearchSurgeDeploymentSerializer(many=True, required=False, allow_null=True)
    rapid_response_deployments = SearchRapidResponseDeploymentsSerializer(many=True, required=False, allow_null=True)
    reports = SearchReportSerializer(many=True, required=False, allow_null=True)


class ProjectPrimarySectorsSerializer(serializers.Serializer):
    key = serializers.IntegerField()
    label = serializers.CharField()
    color = serializers.CharField()
    is_deprecated = serializers.BooleanField()


class ProjectSecondarySectorsSerializer(serializers.Serializer):
    key = serializers.IntegerField()
    label = serializers.CharField()
    color = serializers.CharField()
    is_deprecated = serializers.BooleanField()


class AggregateByTimeSeriesInputSerializer(serializers.Serializer):
    unit = serializers.CharField(required=False)
    start_date = serializers.DateTimeField(required=False)
    mtype = serializers.CharField(required=False)
    country = serializers.IntegerField(required=False)
    region = serializers.IntegerField(required=False)


class AggregateByTimeSeriesSerializer(serializers.Serializer):
    timespan = serializers.DateTimeField()
    count = serializers.IntegerField()
    beneficiaries = serializers.IntegerField(allow_null=True)
    amount_funded = serializers.FloatField(allow_null=True)


class AreaAggregateSerializer(serializers.Serializer):
    num_beneficiaries = serializers.IntegerField()
    amount_requested = serializers.FloatField()
    amount_funded = serializers.FloatField()
    count = serializers.IntegerField()


class AggregateByDtypeSerializer(serializers.Serializer):
    dtype = serializers.IntegerField()
    count = serializers.IntegerField()


class CountryKeyFigureInputSerializer(serializers.Serializer):
    start_date_from = serializers.DateField(required=False)
    start_date_to = serializers.DateField(required=False)
    dtype = serializers.IntegerField(required=False)


class CountryKeyClimateInputSerializer(serializers.Serializer):
    year = serializers.IntegerField(required=False)


class CountryKeyFigureSerializer(serializers.Serializer):
    active_drefs = serializers.IntegerField()
    active_appeals = serializers.IntegerField()
    amount_requested = serializers.IntegerField()
    target_population = serializers.IntegerField()
    amount_requested_dref_included = serializers.IntegerField()
    amount_funded = serializers.IntegerField()
    amount_funded_dref_included = serializers.IntegerField()
    emergencies = serializers.IntegerField()


class CountryDisasterTypeCountSerializer(serializers.Serializer):
    disaster_name = serializers.CharField()
    count = serializers.IntegerField()
    disaster_id = serializers.IntegerField()


class CountryDisasterTypeMonthlySerializer(serializers.Serializer):
    date = serializers.DateTimeField()
    targeted_population = serializers.IntegerField()
    disaster_name = serializers.CharField()
    disaster_id = serializers.IntegerField()


class HistoricalDisasterSerializer(serializers.Serializer):
    date = serializers.DateTimeField()
    targeted_population = serializers.IntegerField()
    disaster_name = serializers.CharField()
    disaster_id = serializers.IntegerField()
    amount_funded = serializers.FloatField()
    amount_requested = serializers.FloatField()


class ExportSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    # NOTE: is_pga is used to determine if the export contains PGA or not
    is_pga = serializers.BooleanField(default=False, required=False, write_only=True)
    # NOTE: diff is used to determine if the export is requested for diff view or not
    # Currently only used for EAP exports
    diff = serializers.BooleanField(default=False, required=False, write_only=True)
    # NOTE: Version of a EAP export being requested, only applicable for full and simplified EAP exports
    version = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = Export
        fields = "__all__"
        read_only_fields = ("pdf_file", "token", "requested_at", "completed_at", "status", "requested_by", "url")

    def validate_pdf_file(self, pdf_file):
        validate_file_type(pdf_file)
        return pdf_file

    def create(self, validated_data):
        language = django_get_language()
        export_id = validated_data.get("export_id")
        export_type = validated_data.get("export_type")
        country_id = validated_data.get("per_country")
        version = validated_data.get("version", None)
        if export_type == Export.ExportType.DREF:
            title = Dref.objects.filter(id=export_id).first().title
        elif export_type == Export.ExportType.OPS_UPDATE:
            title = DrefOperationalUpdate.objects.filter(id=export_id).first().title
        elif export_type == Export.ExportType.FINAL_REPORT:
            title = DrefFinalReport.objects.filter(id=export_id).first().title
        elif export_type == Export.ExportType.PER:
            overview = Overview.objects.filter(id=export_id).first()
            title = f"{overview.country.name}-preparedness-{overview.get_phase_display()}"
        elif export_type == Export.ExportType.SIMPLIFIED_EAP:
            if version:
                simplified_eap = (
                    SimplifiedEAP.objects.filter(eap_registration__id=export_id, version=version).order_by("-version").first()
                )
            else:
                simplified_eap = SimplifiedEAP.objects.filter(eap_registration__id=export_id).order_by("-version").first()
            title = (
                f"{simplified_eap.eap_registration.national_society.name}-{simplified_eap.eap_registration.disaster_type.name}"
            )
        elif export_type == Export.ExportType.FULL_EAP:
            if version:
                full_eap = FullEAP.objects.filter(eap_registration__id=export_id, version=version).order_by("-version").first()
            else:
                full_eap = FullEAP.objects.filter(eap_registration__id=export_id).order_by("-version").first()
            title = f"{full_eap.eap_registration.national_society.name}-{full_eap.eap_registration.disaster_type.name}"
        else:
            title = "Export"
        user = self.context["request"].user

        if export_type == Export.ExportType.PER:
            validated_data["url"] = f"{settings.GO_WEB_INTERNAL_URL}/countries/{country_id}/{export_type}/{export_id}/export/"

        if export_type in [
            Export.ExportType.SIMPLIFIED_EAP,
            Export.ExportType.FULL_EAP,
        ]:
            validated_data["url"] = f"{settings.GO_WEB_INTERNAL_URL}/eap/{export_id}/{export_type}/export/"
            # NOTE: EAP exports with diff view only for EAPs exports
            diff = validated_data.pop("diff")
            if diff:
                validated_data["url"] += "?diff=true"
            if version:
                validated_data["url"] += f"&version={version}" if diff else f"?version={version}"

        else:
            validated_data["url"] = f"{settings.GO_WEB_INTERNAL_URL}/{export_type}/{export_id}/export/"

        # Adding is_pga to the url
        is_pga = validated_data.pop("is_pga")
        if is_pga:
            validated_data["url"] += "?is_pga=true"
        validated_data["requested_by"] = user
        export = super().create(validated_data)
        if export.url:
            export.status = Export.ExportStatus.PENDING
            export.requested_at = timezone.now()
            export.save(update_fields=["status", "requested_at"])

            transaction.on_commit(lambda: generate_url.delay(export.url, export.id, user.id, title, language))
        return export

    def update(self, instance, validated_data):
        raise serializers.ValidationError("Update is not allowed")


class CountrySupportingPartnerSerializer(serializers.ModelSerializer):
    supporting_type_display = serializers.CharField(source="get_supporting_type_display", read_only=True)

    class Meta:
        model = CountrySupportingPartner
        fields = "__all__"
