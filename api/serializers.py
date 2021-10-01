import json
import datetime
from rest_framework import serializers
from django.contrib.auth.models import User
from enumfields.drf.serializers import EnumSupportSerializerMixin

from main.utils import get_merged_items_by_fields
from lang.serializers import ModelSerializer
from lang.models import String

from .models import (
    DisasterType,
    ExternalPartner,
    SupportedActivity,

    Region,
    Country,
    District,
    CountryKeyFigure,
    RegionKeyFigure,
    CountrySnippet,
    RegionSnippet,
    RegionEmergencySnippet,
    RegionProfileSnippet,
    RegionPreparednessSnippet,
    CountryLink,
    RegionLink,
    CountryContact,
    RegionContact,

    KeyFigure,
    Snippet,
    EventContact,
    Event,
    SituationReportType,
    SituationReport,
    EventFeaturedDocument,
    EventLink,

    Appeal,
    AppealDocument,
    AppealHistory,
    Profile,

    FieldReportContact,
    ActionsTaken,
    Action,
    Source,
    FieldReport,
    MainContact
)
from notifications.models import Subscription
from deployments.models import Personnel


class DisasterTypeSerializer(ModelSerializer):
    class Meta:
        model = DisasterType
        fields = ('name', 'summary', 'id',)


class RegionSerializer(EnumSupportSerializerMixin, ModelSerializer):
    class Meta:
        model = Region
        fields = ('name', 'id', 'region_name', 'label',)


class RegionGeoSerializer(EnumSupportSerializerMixin, ModelSerializer):
    bbox = serializers.SerializerMethodField()

    def get_bbox(self, region):
        return region.bbox and json.loads(region.bbox.geojson)

    class Meta:
        model = Region
        fields = ('name', 'id', 'region_name', 'bbox', 'label',)


class CountryTableauSerializer(EnumSupportSerializerMixin, ModelSerializer):
    region = RegionSerializer()
    record_type_display = serializers.CharField(source='get_record_type_display', read_only=True)

    class Meta:
        model = Country
        fields = (
            'name', 'iso', 'iso3', 'society_name', 'society_url', 'region', 'overview', 'key_priorities',
            'inform_score', 'id', 'url_ifrc', 'record_type', 'record_type_display',
        )


class CountrySerializer(EnumSupportSerializerMixin, ModelSerializer):
    record_type_display = serializers.CharField(source='get_record_type_display', read_only=True)

    class Meta:
        model = Country
        fields = (
            'name', 'iso', 'iso3', 'society_name', 'society_url', 'region', 'overview', 'key_priorities', 'inform_score',
            'id', 'url_ifrc', 'record_type', 'record_type_display', 'independent', 'is_deprecated', 'fdrs',
        )


class CountryGeoSerializer(EnumSupportSerializerMixin, ModelSerializer):
    bbox = serializers.SerializerMethodField()
    centroid = serializers.SerializerMethodField()
    record_type_display = serializers.CharField(source='get_record_type_display', read_only=True)

    def get_bbox(self, country):
        return country.bbox and json.loads(country.bbox.geojson)

    def get_centroid(self, country):
        return country.centroid and json.loads(country.centroid.geojson)

    class Meta:
        model = Country
        fields = (
            'name', 'iso', 'iso3', 'society_name', 'society_url', 'region', 'overview', 'key_priorities', 'inform_score',
            'id', 'url_ifrc', 'record_type', 'record_type_display', 'bbox', 'centroid', 'independent', 'is_deprecated', 'fdrs',
        )


class MiniCountrySerializer(EnumSupportSerializerMixin, ModelSerializer):
    record_type_display = serializers.CharField(source='get_record_type_display', read_only=True)

    class Meta:
        model = Country
        fields = (
            'name', 'iso', 'iso3', 'society_name', 'id', 'record_type', 'record_type_display',
            'region', 'independent', 'is_deprecated', 'fdrs',
        )


class MicroCountrySerializer(ModelSerializer):
    class Meta:
        model = Country
        fields = ('id', 'name', 'iso', 'iso3', 'society_name')


class RegoCountrySerializer(ModelSerializer):
    class Meta:
        model = Country
        fields = ('name', 'society_name', 'region', 'id',)


class NotCountrySerializer(ModelSerializer):  # fake serializer for a short data response for PER
    class Meta:
        model = Country
        fields = ('id',)


class DistrictSerializer(ModelSerializer):
    country = MiniCountrySerializer()

    class Meta:
        model = District
        fields = ('name', 'code', 'country', 'id', 'is_deprecated',)


class MiniDistrictSerializer(ModelSerializer):
    class Meta:
        model = District
        fields = ('name', 'code', 'id', 'is_enclave', 'is_deprecated',)


class MiniDistrictGeoSerializer(ModelSerializer):
    bbox = serializers.SerializerMethodField()
    centroid = serializers.SerializerMethodField()
    country_name = serializers.CharField(source='country.name', read_only=True)
    country_iso = serializers.CharField(source='country.iso', read_only=True)
    country_iso3 = serializers.CharField(source='country.iso3', read_only=True)

    def get_bbox(self, district):
        if district.bbox:
            return json.loads(district.bbox.geojson)
        else:
            return None

    def get_centroid(self, district):
        if district.centroid:
            return json.loads(district.centroid.geojson)
        else:
            return None

    class Meta:
        model = District
        fields = (
            'id', 'name', 'code', 'country_name', 'country_iso', 'country_iso3',
            'is_enclave', 'bbox', 'centroid', 'is_deprecated',
        )


class RegionKeyFigureSerializer(ModelSerializer):
    class Meta:
        model = RegionKeyFigure
        fields = ('region', 'figure', 'deck', 'source', 'visibility', 'id',)


class CountryKeyFigureSerializer(ModelSerializer):
    class Meta:
        model = CountryKeyFigure
        fields = ('country', 'figure', 'deck', 'source', 'visibility', 'id',)


class RegionSnippetTableauSerializer(EnumSupportSerializerMixin, ModelSerializer):
    region = RegionSerializer()
    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)

    class Meta:
        model = RegionSnippet
        fields = ('region', 'snippet', 'image', 'visibility', 'visibility_display', 'id',)


class RegionSnippetSerializer(EnumSupportSerializerMixin, ModelSerializer):
    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)

    class Meta:
        model = RegionSnippet
        fields = ('region', 'snippet', 'image', 'visibility', 'visibility_display', 'id',)


class RegionEmergencySnippetSerializer(EnumSupportSerializerMixin, ModelSerializer):

    class Meta:
        model = RegionEmergencySnippet
        fields = ('region', 'title', 'snippet', 'id',)


class RegionProfileSnippetSerializer(EnumSupportSerializerMixin, ModelSerializer):

    class Meta:
        model = RegionProfileSnippet
        fields = ('region', 'title', 'snippet', 'id',)


class RegionPreparednessSnippetSerializer(EnumSupportSerializerMixin, ModelSerializer):

    class Meta:
        model = RegionPreparednessSnippet
        fields = ('region', 'title', 'snippet', 'id',)


class CountrySnippetTableauSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    country = CountrySerializer()
    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)

    class Meta:
        model = CountrySnippet
        fields = ('country', 'snippet', 'image', 'visibility', 'visibility_display', 'id',)


class CountrySnippetSerializer(EnumSupportSerializerMixin, ModelSerializer):
    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)

    class Meta:
        model = CountrySnippet
        fields = ('country', 'snippet', 'image', 'visibility', 'visibility_display', 'id',)


class RegionLinkSerializer(ModelSerializer):
    class Meta:
        model = RegionLink
        fields = ('title', 'url', 'id', 'show_in_go',)


class CountryLinkSerializer(ModelSerializer):
    class Meta:
        model = CountryLink
        fields = ('title', 'url', 'id',)


class RegionContactSerializer(ModelSerializer):
    class Meta:
        model = RegionContact
        fields = ('ctype', 'name', 'title', 'email', 'id',)


class CountryContactSerializer(ModelSerializer):
    class Meta:
        model = CountryContact
        fields = ('ctype', 'name', 'title', 'email', 'id',)


class RegionRelationSerializer(EnumSupportSerializerMixin, ModelSerializer):
    links = RegionLinkSerializer(many=True, read_only=True)
    contacts = RegionContactSerializer(many=True, read_only=True)
    snippets = RegionSnippetSerializer(many=True, read_only=True)
    emergency_snippets = RegionEmergencySnippetSerializer(many=True, read_only=True)
    profile_snippets = RegionProfileSnippetSerializer(many=True, read_only=True)
    preparedness_snippets = RegionPreparednessSnippetSerializer(many=True, read_only=True)
    national_society_count = serializers.SerializerMethodField()
    country_cluster_count = serializers.SerializerMethodField()

    def get_national_society_count(self, obj):
        return obj.get_national_society_count()

    def get_country_cluster_count(self, obj):
        return obj.get_country_cluster_count()

    class Meta:
        model = Region
        fields = ('links', 'contacts', 'snippets', 'emergency_snippets',
                  'profile_snippets', 'preparedness_snippets', 'name',
                  'region_name', 'id', 'additional_tab_name',
                  'national_society_count', 'country_cluster_count',)


class CountryRelationSerializer(ModelSerializer):
    links = CountryLinkSerializer(many=True, read_only=True)
    contacts = CountryContactSerializer(many=True, read_only=True)

    class Meta:
        model = Country
        fields = (
            'links', 'contacts', 'name', 'iso', 'society_name', 'society_url', 'region',
            'overview', 'key_priorities', 'inform_score', 'id', 'url_ifrc', 'additional_tab_name',
            'nsi_income', 'nsi_expenditures', 'nsi_branches', 'nsi_staff', 'nsi_volunteers', 'nsi_youth',
            'nsi_trained_in_first_aid', 'nsi_gov_financial_support', 'nsi_domestically_generated_income',
            'nsi_annual_fdrs_reporting', 'nsi_policy_implementation', 'nsi_risk_management_framework',
            'nsi_cmc_dashboard_compliance', 'wash_kit2', 'wash_kit5', 'wash_kit10', 'wash_staff_at_hq',
            'wash_staff_at_branch', 'wash_ndrt_trained', 'wash_rdrt_trained',
        )


class RelatedAppealSerializer(EnumSupportSerializerMixin, ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Appeal
        fields = (
            'aid', 'num_beneficiaries', 'amount_requested', 'amount_funded', 'status', 'status_display', 'start_date', 'id',
        )


class KeyFigureSerializer(ModelSerializer):
    class Meta:
        model = KeyFigure
        fields = ('number', 'deck', 'source', 'id',)


class SnippetSerializer(EnumSupportSerializerMixin, ModelSerializer):
    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)
    position_display = serializers.CharField(source='get_position_display', read_only=True)
    tab_display = serializers.CharField(source='get_tab_display', read_only=True)

    class Meta:
        model = Snippet
        fields = (
            'event', 'snippet', 'image', 'id',
            'visibility', 'visibility_display', 'position', 'position_display', 'tab', 'tab_display',
        )


class EventContactSerializer(ModelSerializer):
    class Meta:
        model = EventContact
        fields = ('ctype', 'name', 'title', 'email', 'phone', 'event', 'id',)


class FieldReportContactSerializer(ModelSerializer):
    class Meta:
        model = FieldReportContact
        fields = ('ctype', 'name', 'title', 'email', 'phone', 'id',)


class MiniFieldReportSerializer(EnumSupportSerializerMixin, ModelSerializer):
    contacts = FieldReportContactSerializer(many=True)
    countries = MiniCountrySerializer(many=True)
    epi_figures_source_display = serializers.CharField(source='get_epi_figures_source_display', read_only=True)
    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)

    class Meta:
        model = FieldReport
        fields = (
            'summary', 'status', 'description', 'contacts', 'countries', 'created_at', 'updated_at', 'report_date', 'id',
            'is_covid_report', 'num_injured', 'num_dead', 'num_missing', 'num_affected', 'num_displaced', 'epi_num_dead',
            'num_assisted', 'num_localstaff', 'num_volunteers', 'num_expats_delegates', 'gov_num_injured', 'gov_num_dead',
            'gov_num_missing', 'gov_num_affected', 'gov_num_displaced', 'gov_num_assisted', 'other_num_injured',
            'other_num_dead', 'other_num_missing', 'other_num_affected', 'other_num_displaced', 'other_num_assisted',
            'num_potentially_affected', 'gov_num_potentially_affected', 'other_num_potentially_affected', 'num_highest_risk',
            'gov_num_highest_risk', 'other_num_highest_risk', 'affected_pop_centres', 'gov_affected_pop_centres',
            'other_affected_pop_centres', 'epi_cases', 'epi_suspected_cases', 'epi_probable_cases', 'epi_confirmed_cases',
            'epi_figures_source', 'epi_figures_source_display', 'epi_cases_since_last_fr', 'epi_deaths_since_last_fr',
            'epi_notes_since_last_fr', 'visibility', 'visibility_display', 'request_assistance', 'ns_request_assistance',
            'notes_health', 'notes_ns', 'notes_socioeco'
        )


class EventFeaturedDocumentSerializer(ModelSerializer):
    class Meta:
        model = EventFeaturedDocument
        fields = ('id', 'title', 'description', 'thumbnail', 'file',)


class EventLinkSerializer(ModelSerializer):
    class Meta:
        model = EventLink
        fields = ('id', 'title', 'description', 'url',)


# The list serializer can include a smaller subset of the to-many fields.
# Also include a very minimal one for linking, and no other related fields.
class MiniEventSerializer(ModelSerializer):
    class Meta:
        model = Event
        fields = ('name', 'dtype', 'id', 'slug', 'parent_event',)


class ListMiniEventSerializer(ModelSerializer):
    dtype = DisasterTypeSerializer(read_only=True)

    class Meta:
        model = Event
        fields = ('id', 'name', 'slug', 'dtype', 'auto_generated_source')


class ListEventSerializer(EnumSupportSerializerMixin, ModelSerializer):
    appeals = RelatedAppealSerializer(many=True, read_only=True)
    countries = MiniCountrySerializer(many=True)
    field_reports = MiniFieldReportSerializer(many=True, read_only=True)
    dtype = DisasterTypeSerializer()
    ifrc_severity_level_display = serializers.CharField(source='get_ifrc_severity_level_display', read_only=True)

    class Meta:
        model = Event
        fields = (
            'name', 'dtype', 'countries', 'summary', 'num_affected', 'ifrc_severity_level', 'ifrc_severity_level_display',
            'glide', 'disaster_start_date', 'created_at', 'auto_generated', 'appeals', 'is_featured', 'is_featured_region',
            'field_reports', 'updated_at', 'id', 'slug', 'parent_event', 'tab_one_title', 'tab_two_title', 'tab_three_title',
        )


class ListEventTableauSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    appeals = serializers.SerializerMethodField()
    field_reports = serializers.SerializerMethodField()
    countries = serializers.SerializerMethodField()
    dtype = DisasterTypeSerializer()
    ifrc_severity_level_display = serializers.CharField(source='get_ifrc_severity_level_display', read_only=True)

    def get_countries(self, obj):
        return get_merged_items_by_fields(obj.countries.all(), ['id', 'name'])

    def get_field_reports(self, obj):
        return get_merged_items_by_fields(obj.field_reports.all(), ['id'])

    def get_appeals(self, obj):
        return get_merged_items_by_fields(obj.appeals.all(), ['id'])

    class Meta:
        model = Event
        fields = (
            'name', 'dtype', 'countries', 'summary', 'num_affected', 'ifrc_severity_level', 'ifrc_severity_level_display',
            'glide', 'disaster_start_date', 'created_at', 'auto_generated', 'appeals', 'is_featured', 'is_featured_region',
            'field_reports', 'updated_at', 'id', 'slug', 'parent_event',
        )


class ListEventCsvSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    appeals = serializers.SerializerMethodField()
    field_reports = serializers.SerializerMethodField()
    countries = serializers.SerializerMethodField()
    dtype = DisasterTypeSerializer()
    ifrc_severity_level_display = serializers.CharField(source='get_ifrc_severity_level_display', read_only=True)

    def get_countries(self, obj):
        return get_merged_items_by_fields(obj.countries.all(), ['id', 'name', 'iso', 'iso3', 'society_name'])

    def get_field_reports(self, obj):
        return get_merged_items_by_fields(obj.field_reports.all(), ['id'])

    def get_appeals(self, obj):
        return get_merged_items_by_fields(obj.appeals.all(), ['id'])

    class Meta:
        model = Event
        fields = (
            'name', 'dtype', 'countries', 'summary', 'num_affected', 'ifrc_severity_level', 'ifrc_severity_level_display',
            'glide', 'disaster_start_date', 'created_at', 'auto_generated', 'appeals', 'is_featured', 'is_featured_region',
            'field_reports', 'updated_at', 'id', 'slug', 'parent_event',
        )


class ListEventForPersonnelCsvSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    appeals = serializers.SerializerMethodField()
    field_reports = serializers.SerializerMethodField()
    countries = serializers.SerializerMethodField()
    dtype_name = serializers.SerializerMethodField()

    # NOTE: prefetched at deployments/drf_views.py::PersonnelViewset::get_queryset
    def get_countries(self, obj):
        fields = ['id', 'name', 'iso', 'iso3', 'society_name']
        return get_merged_items_by_fields(obj.countries.all(), fields)

    def get_field_reports(self, obj):
        fields = ['id']
        return get_merged_items_by_fields(obj.field_reports.all(), fields)

    def get_appeals(self, obj):
        fields = ['id', 'status']
        return get_merged_items_by_fields(obj.appeals.all(), fields)

    def get_dtype_name(self, obj):
        return obj.dtype and obj.dtype.name

    class Meta:
        model = Event
        fields = (
            'name', 'dtype_name', 'countries', 'summary', 'num_affected', 'ifrc_severity_level',
            'glide', 'disaster_start_date', 'created_at', 'appeals',
            'field_reports', 'updated_at', 'id', 'parent_event',
        )


class ListEventDeploymentsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    deployments = serializers.IntegerField()


class DeploymentsByEventSerializer(ModelSerializer):
    organizations_from = serializers.SerializerMethodField()
    personnel_count = serializers.IntegerField()

    def get_organizations_from(self, obj):
        deployments = [d for d in obj.personneldeployment_set.all()]
        personnels = []
        for d in deployments:
            for p in d.personnel_set.filter(end_date__gte=datetime.datetime.now(), is_active=True):
                personnels.append(p)
        return list(set([p.country_from.society_name for p in personnels if p.country_from and p.country_from.society_name != '']))

    class Meta:
        model = Event
        fields = (
            'id', 'name', 'personnel_count', 'organizations_from',
        )


class DetailEventSerializer(EnumSupportSerializerMixin, ModelSerializer):
    appeals = RelatedAppealSerializer(many=True, read_only=True)
    contacts = EventContactSerializer(many=True, read_only=True)
    key_figures = KeyFigureSerializer(many=True, read_only=True)
    districts = MiniDistrictSerializer(many=True)
    countries = MiniCountrySerializer(many=True)
    field_reports = MiniFieldReportSerializer(many=True, read_only=True)
    ifrc_severity_level_display = serializers.CharField(source='get_ifrc_severity_level_display', read_only=True)
    featured_documents = EventFeaturedDocumentSerializer(many=True, read_only=True)
    links = EventLinkSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = (
            'name', 'dtype', 'countries', 'districts', 'summary', 'num_affected', 'tab_two_title', 'tab_three_title',
            'disaster_start_date', 'created_at', 'auto_generated', 'appeals', 'contacts', 'key_figures', 'is_featured',
            'is_featured_region', 'field_reports', 'hide_attached_field_reports', 'hide_field_report_map', 'updated_at',
            'id', 'slug', 'tab_one_title', 'ifrc_severity_level', 'ifrc_severity_level_display', 'parent_event', 'glide',
            'featured_documents', 'links',
        )
        lookup_field = 'slug'


class SituationReportTypeSerializer(ModelSerializer):
    class Meta:
        model = SituationReportType
        fields = ('type', 'id', 'is_primary',)


class SituationReportTableauSerializer(EnumSupportSerializerMixin, ModelSerializer):
    type = SituationReportTypeSerializer()
    event = MiniEventSerializer()
    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)

    class Meta:
        model = SituationReport
        fields = (
            'created_at', 'name', 'document', 'document_url', 'event', 'type', 'id', 'is_pinned',
            'visibility', 'visibility_display',
        )


class SituationReportSerializer(EnumSupportSerializerMixin, ModelSerializer):
    type = SituationReportTypeSerializer()
    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)

    class Meta:
        model = SituationReport
        fields = (
            'created_at', 'name', 'document', 'document_url', 'event', 'type', 'id', 'is_pinned',
            'visibility', 'visibility_display',
        )


class AppealTableauSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    country = MiniCountrySerializer()
    dtype = DisasterTypeSerializer()
    region = RegionSerializer()
    event = MiniEventSerializer()
    atype_display = serializers.CharField(source='get_atype_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Appeal
        fields = (
            'aid', 'name', 'dtype', 'atype', 'atype_display', 'status', 'status_display', 'code', 'sector',
            'num_beneficiaries', 'amount_requested', 'amount_funded', 'start_date', 'end_date','real_data_update', 'created_at',
            'modified_at', 'event', 'needs_confirmation', 'country', 'region', 'id',
        )


class AppealHistoryTableauSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    country = MiniCountrySerializer()
    dtype = DisasterTypeSerializer()
    region = RegionSerializer()
    event = MiniEventSerializer()
    atype_display = serializers.CharField(source='get_atype_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    code = serializers.CharField(source='appeal.code', read_only=True)
    sector = serializers.CharField(source='appeal.sector', read_only=True)
    created_at = serializers.CharField(source='appeal.created_at', read_only=True)
    modified_at = serializers.CharField(source='appeal.modified_at', read_only=True)
    real_data_update =  serializers.CharField(source='appeal.real_data_update', read_only=True)
    event = serializers.CharField(source='appeal.event', read_only=True)
    id = serializers.CharField(source='appeal.id', read_only=True)
    name = serializers.CharField(source='appeal.name', read_only=True)

    class Meta:
        model = AppealHistory
        fields = (
            'aid', 'name', 'dtype', 'atype', 'atype_display', 'status', 'status_display', 'code', 'sector',
            'num_beneficiaries', 'amount_requested', 'amount_funded', 'start_date', 'end_date','real_data_update', 'created_at',
            'modified_at', 'event', 'needs_confirmation', 'country', 'region', 'id',
        )


class MiniAppealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appeal
        fields = ('name', 'id', 'code')


class AppealSerializer(EnumSupportSerializerMixin, ModelSerializer):
    country = MiniCountrySerializer()
    dtype = DisasterTypeSerializer()
    region = RegionSerializer()
    atype_display = serializers.CharField(source='get_atype_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Appeal
        fields = (
            'aid', 'name', 'dtype', 'atype', 'atype_display', 'status', 'status_display', 'code', 'sector',
            'num_beneficiaries', 'amount_requested', 'amount_funded', 'start_date', 'end_date','real_data_update', 'created_at',
            'modified_at', 'event', 'needs_confirmation', 'country', 'region', 'id',
        )


class AppealHistorySerializer(EnumSupportSerializerMixin, ModelSerializer):
    country = MiniCountrySerializer()
    dtype = DisasterTypeSerializer()
    region = RegionSerializer()
    atype_display = serializers.CharField(source='get_atype_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    code = serializers.CharField(source='appeal.code', read_only=True)
    sector = serializers.CharField(source='appeal.sector', read_only=True)
    created_at = serializers.CharField(source='appeal.created_at', read_only=True)
    modified_at = serializers.CharField(source='appeal.modified_at', read_only=True)
    real_data_update =  serializers.CharField(source='appeal.real_data_update', read_only=True)
    event = serializers.IntegerField(source='appeal.event_id', read_only=True)
    id = serializers.CharField(source='appeal.id', read_only=True)
    name = serializers.CharField(source='appeal.name', read_only=True)

    class Meta:
        model = AppealHistory
        fields = (
            'aid', 'name', 'dtype', 'atype', 'atype_display', 'status', 'status_display', 'code', 'sector',
            'num_beneficiaries', 'amount_requested', 'amount_funded', 'start_date', 'end_date','real_data_update', 'created_at',
            'modified_at', 'event', 'needs_confirmation', 'country', 'region', 'id',
        )


class AppealDocumentTableauSerializer(serializers.ModelSerializer):
    appeal = MiniAppealSerializer()

    class Meta:
        model = AppealDocument
        fields = ('created_at', 'name', 'document', 'document_url', 'appeal', 'id',)


class AppealDocumentSerializer(ModelSerializer):
    class Meta:
        model = AppealDocument
        fields = ('created_at', 'name', 'document', 'document_url', 'appeal', 'id',)


class ProfileSerializer(ModelSerializer):
    country = MiniCountrySerializer()

    class Meta:
        model = Profile
        fields = ('country', 'org', 'org_type', 'city', 'department', 'position', 'phone_number')


class MiniSubscriptionSerializer(ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('stype', 'rtype', 'country', 'region', 'event', 'dtype', 'lookup_id',)


class UserSerializer(ModelSerializer):
    profile = ProfileSerializer()
    subscription = MiniSubscriptionSerializer(many=True)
    is_ifrc_admin = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'profile', 'subscription', 'is_superuser',
                  'is_ifrc_admin')

    def update(self, instance, validated_data):
        if 'profile' in validated_data:
            profile_data = validated_data.pop('profile')
            profile = Profile.objects.get(user=instance)
            profile.city = profile_data.get('city', profile.city)
            profile.org = profile_data.get('org', profile.org)
            profile.org_type = profile_data.get('org_type', profile.org_type)
            profile.department = profile_data.get('department', profile.department)
            profile.position = profile_data.get('position', profile.position)
            profile.phone_number = profile_data.get('phone_number', profile.phone_number)
            profile.country = profile_data.get('country', profile.country)
            profile.save()
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        return instance

    def get_is_ifrc_admin(self, obj):
        return obj.groups.filter(name__iexact="IFRC Admins").exists()


class UserNameSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name')


class UserMeSerializer(UserSerializer):
    is_admin_for_countries = serializers.SerializerMethodField()
    is_admin_for_regions = serializers.SerializerMethodField()
    lang_permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + (
            'is_admin_for_countries', 'is_admin_for_regions', 'lang_permissions'
        )

    def get_is_admin_for_countries(self, user):
        return set([
            int(permission[18:]) for permission in user.get_all_permissions()
            if ('api.country_admin_' in permission and permission[18:].isdigit())
        ])

    def get_is_admin_for_regions(self, user):
        return set([
            int(permission[17:]) for permission in user.get_all_permissions()
            if ('api.region_admin_' in permission and permission[17:].isdigit())
        ])

    def get_lang_permissions(self, user):
        return String.get_user_permissions_per_language(user)


class ActionSerializer(ModelSerializer):
    class Meta:
        model = Action
        fields = ('name', 'id', 'organizations', 'field_report_types', 'category', 'tooltip_text')


class ActionsTakenSerializer(ModelSerializer):
    actions = ActionSerializer(many=True)

    class Meta:
        model = ActionsTaken
        fields = ('organization', 'actions', 'summary', 'id',)


class ExternalPartnerSerializer(ModelSerializer):
    class Meta:
        model = ExternalPartner
        fields = ('name', 'id')


class SupportedActivitySerializer(ModelSerializer):
    class Meta:
        model = SupportedActivity
        fields = ('name', 'id')


class SourceSerializer(ModelSerializer):
    stype = serializers.SlugRelatedField(slug_field='name', read_only=True)

    class Meta:
        model = Source
        fields = ('stype', 'spec', 'id',)


class FieldReportEnumDisplayMixin(EnumSupportSerializerMixin):
    """
    Use for fields = '__all__'
    """
    epi_figures_source_display = serializers.CharField(source='get_epi_figures_source_display', read_only=True)
    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)
    bulletin_display = serializers.CharField(source='get_bulletin_display', read_only=True)
    dref_display = serializers.CharField(source='get_dref_display', read_only=True)
    appeal_display = serializers.CharField(source='get_appeal_display', read_only=True)
    imminent_dref_display = serializers.CharField(source='get_imminent_dref_display', read_only=True)
    forecast_based_action_display = serializers.CharField(source='get_forecast_based_action_display', read_only=True)
    rdrt_display = serializers.CharField(source='get_rdrt_display', read_only=True)
    fact_display = serializers.CharField(source='get_fact_display', read_only=True)
    ifrc_staff_display = serializers.CharField(source='get_ifrc_staff_display', read_only=True)
    eru_base_camp_display = serializers.CharField(source='get_eru_base_camp_display', read_only=True)
    eru_basic_health_care_display = serializers.CharField(source='get_eru_basic_health_care_display', read_only=True)
    eru_it_telecom_display = serializers.CharField(source='get_eru_it_telecom_display', read_only=True)
    eru_logistics_display = serializers.CharField(source='get_eru_logistics_display', read_only=True)
    eru_deployment_hospital_display = serializers.CharField(source='get_eru_deployment_hospital_display', read_only=True)
    eru_referral_hospital_display = serializers.CharField(source='get_eru_referral_hospital_display', read_only=True)
    eru_relief_display = serializers.CharField(source='get_eru_relief_display', read_only=True)
    eru_water_sanitation_15_display = serializers.CharField(source='get_eru_water_sanitation_15_display', read_only=True)
    eru_water_sanitation_40_display = serializers.CharField(source='get_eru_water_sanitation_40_display', read_only=True)
    eru_water_sanitation_20_display = serializers.CharField(source='get_eru_water_sanitation_20_display', read_only=True)


class ListFieldReportSerializer(FieldReportEnumDisplayMixin, ModelSerializer):
    countries = MiniCountrySerializer(many=True)
    dtype = DisasterTypeSerializer()
    event = MiniEventSerializer()
    actions_taken = ActionsTakenSerializer(many=True)

    class Meta:
        model = FieldReport
        fields = '__all__'


class ListFieldReportTableauSerializer(FieldReportEnumDisplayMixin, ModelSerializer):
    countries = serializers.SerializerMethodField()
    districts = serializers.SerializerMethodField()
    regions = serializers.SerializerMethodField()
    dtype = DisasterTypeSerializer()
    event = MiniEventSerializer()
    actions_taken = serializers.SerializerMethodField('get_actions_taken_for_organization')

    def get_countries(self, obj):
        return get_merged_items_by_fields(obj.countries.all(), ['id', 'name'])

    def get_districts(self, obj):
        return get_merged_items_by_fields(obj.districts.all(), ['id', 'name'])

    def get_regions(self, obj):
        return get_merged_items_by_fields(obj.regions.all(), ['id', 'region_name'])

    def get_actions_taken_for_organization(self, obj):
        actions_data = {}
        actions_taken = obj.actions_taken.all()
        for action in actions_taken:
            if action.organization not in actions_data:
                actions_data[action.organization] = []
            this_action = {
                'actions_name': [a.name for a in action.actions.all()],
                'actions_id': [a.id for a in action.actions.all()]
            }
            actions_data[action.organization] = {
                'action': json.dumps(this_action),
                'summary': action.summary
            }
        return actions_data

    class Meta:
        model = FieldReport
        fields = '__all__'


class ListFieldReportCsvSerializer(FieldReportEnumDisplayMixin, ModelSerializer):
    countries = serializers.SerializerMethodField()
    districts = serializers.SerializerMethodField()
    regions = serializers.SerializerMethodField()
    dtype = DisasterTypeSerializer()
    event = MiniEventSerializer()
    actions_taken = serializers.SerializerMethodField('get_actions_taken_for_organization')

    def get_countries(self, obj):
        return get_merged_items_by_fields(obj.countries.all(), ['id', 'name', 'iso', 'iso3', 'society_name'])

    def get_districts(self, obj):
        return get_merged_items_by_fields(obj.districts.all(), ['id', 'name'])

    def get_regions(self, obj):
        return get_merged_items_by_fields(obj.regions.all(), ['id', 'region_name'])

    def get_actions_taken_for_organization(self, obj):
        actions_data = {}
        actions_taken = obj.actions_taken.all()
        for action in actions_taken:
            if action.organization not in actions_data:
                actions_data[action.organization] = []
            this_action = {
                'actions_name': [a.name for a in action.actions.all()],
                'actions_id': [a.id for a in action.actions.all()]
            }
            actions_data[action.organization] = {
                'action': json.dumps(this_action),
                'summary': action.summary
            }
        return actions_data

    class Meta:
        model = FieldReport
        fields = '__all__'


class DetailFieldReportSerializer(FieldReportEnumDisplayMixin, ModelSerializer):
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

    class Meta:
        model = FieldReport
        fields = '__all__'


class CreateFieldReportSerializer(FieldReportEnumDisplayMixin, ModelSerializer):
    class Meta:
        model = FieldReport
        fields = '__all__'


class MainContactSerializer(ModelSerializer):
    class Meta:
        model = MainContact
        fields = '__all__'


class NsSerializer(ModelSerializer):
    class Meta:
        model = Country
        fields = ('url_ifrc',)
