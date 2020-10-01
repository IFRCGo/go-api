import json
from rest_framework import serializers
from django.contrib.auth.models import User
from enumfields.drf.serializers import EnumSupportSerializerMixin

from lang.serializers import ModelSerializer
from .models import (
    DisasterType,

    Region,
    Country,
    District,
    CountryKeyFigure,
    RegionKeyFigure,
    CountrySnippet,
    RegionSnippet,
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

    Appeal,
    AppealType,
    AppealDocument,

    Profile,

    FieldReportContact,
    ActionsTaken,
    Action,
    Source,
    FieldReport,
)
from notifications.models import Subscription


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
            'id', 'url_ifrc', 'record_type', 'record_type_display', 'independent', 'is_deprecated'
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
            'id', 'url_ifrc', 'record_type', 'record_type_display', 'bbox', 'centroid', 'independent', 'is_deprecated',
        )


class MiniCountrySerializer(EnumSupportSerializerMixin, ModelSerializer):
    record_type_display = serializers.CharField(source='get_record_type_display', read_only=True)

    class Meta:
        model = Country
        fields = (
            'name', 'iso', 'iso3', 'society_name', 'id', 'record_type', 'record_type_display',
            'region', 'independent', 'is_deprecated',
        )


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
        fields = ('name', 'code', 'country', 'country_iso', 'country_name', 'id', 'is_deprecated',)


class MiniDistrictSerializer(ModelSerializer):
    class Meta:
        model = District
        fields = ('name', 'code', 'country_iso', 'country_name', 'id', 'is_enclave', 'is_deprecated',)


class MiniDistrictGeoSerializer(ModelSerializer):
    bbox = serializers.SerializerMethodField()
    centroid = serializers.SerializerMethodField()

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
        fields = ('name', 'code', 'country_iso', 'country_name', 'id', 'is_enclave', 'bbox', 'centroid', 'is_deprecated',)


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
        fields = ('title', 'url', 'id',)


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

    class Meta:
        model = Region
        fields = ('links', 'contacts', 'name', 'region_name', 'id',)


class CountryRelationSerializer(ModelSerializer):
    links = CountryLinkSerializer(many=True, read_only=True)
    contacts = CountryContactSerializer(many=True, read_only=True)

    class Meta:
        model = Country
        fields = (
            'links', 'contacts', 'name', 'iso', 'society_name', 'society_url', 'region',
            'overview', 'key_priorities', 'inform_score', 'id', 'url_ifrc',
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
            'epi_figures_source', 'epi_figures_source_display',
            'visibility', 'visibility_display',
        )


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
            'field_reports', 'updated_at', 'id', 'slug', 'parent_event',
        )


class ListEventTableauSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    appeals = serializers.SerializerMethodField()
    field_reports = serializers.SerializerMethodField()
    countries = serializers.SerializerMethodField()
    dtype = DisasterTypeSerializer()
    ifrc_severity_level_display = serializers.CharField(source='get_ifrc_severity_level_display', read_only=True)

    def get_countries(self, obj):
        country_fields = {}
        countries = obj.countries.all()
        if countries.exists():
            country_fields['id'] = ', '.join([str(id) for id in countries.values_list('id', flat=True)])
            country_fields['name'] = ', '.join(countries.values_list('name', flat=True))
        else:
            country_fields['id'] = ''
            country_fields['name'] = ''
        return country_fields

    def get_field_reports(self, obj):
        field_reports_fields = {}
        field_reports = obj.field_reports.all()
        if len(field_reports) > 0:
            field_reports_fields['id'] = ', '.join([str(field_reports.id) for field_reports in field_reports])
        else:
            field_reports_fields['id'] = ''
        return field_reports_fields

    def get_appeals(self, obj):
        appeals_fields = {}
        appeals = obj.appeals.all()
        if len(appeals) > 0:
            appeals_fields['id'] = ', '.join([str(appeals.id) for appeals in appeals])
        else:
            appeals_fields['id'] = ''
        return appeals_fields

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
        country_fields = {
            'id': '',
            'name': '',
            'iso': '',
            'iso3': ''
        }
        countries = obj.countries.all()
        if countries.exists():
            country_fields['id'] = ', '.join([str(id) for id in countries.values_list('id', flat=True)])
            country_fields['name'] = ', '.join(countries.values_list('name', flat=True))
            country_fields['iso'] = ', '.join([str(country.iso) for country in countries])
            country_fields['iso3'] = ', '.join([str(country.iso3) for country in countries])
        return country_fields

    def get_field_reports(self, obj):
        field_reports_fields = {}
        field_reports = obj.field_reports.all()
        if len(field_reports) > 0:
            field_reports_fields['id'] = ', '.join([str(field_reports.id) for field_reports in field_reports])
        else:
            field_reports_fields['id'] = ''
        return field_reports_fields

    def get_appeals(self, obj):
        appeals_fields = {}
        appeals = obj.appeals.all()
        if len(appeals) > 0:
            appeals_fields['id'] = ', '.join([str(appeals.id) for appeals in appeals])
        else:
            appeals_fields['id'] = ''
        return appeals_fields

    class Meta:
        model = Event
        fields = (
            'name', 'dtype', 'countries', 'summary', 'num_affected', 'ifrc_severity_level', 'ifrc_severity_level_display',
            'glide', 'disaster_start_date', 'created_at', 'auto_generated', 'appeals', 'is_featured', 'is_featured_region',
            'field_reports', 'updated_at', 'id', 'slug', 'parent_event',
        )


class ListEventDeploymentsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    deployments = serializers.IntegerField()


class DetailEventSerializer(EnumSupportSerializerMixin, ModelSerializer):
    appeals = RelatedAppealSerializer(many=True, read_only=True)
    contacts = EventContactSerializer(many=True, read_only=True)
    key_figures = KeyFigureSerializer(many=True, read_only=True)
    districts = MiniDistrictSerializer(many=True)
    countries = MiniCountrySerializer(many=True)
    field_reports = MiniFieldReportSerializer(many=True, read_only=True)
    ifrc_severity_level_display = serializers.CharField(source='get_ifrc_severity_level_display', read_only=True)

    class Meta:
        model = Event
        fields = (
            'name', 'dtype', 'countries', 'districts', 'summary', 'num_affected', 'tab_two_title', 'tab_three_title',
            'disaster_start_date', 'created_at', 'auto_generated', 'appeals', 'contacts', 'key_figures', 'is_featured',
            'is_featured_region', 'field_reports', 'hide_attached_field_reports', 'updated_at', 'id', 'slug', 'tab_one_title',
            'ifrc_severity_level', 'ifrc_severity_level_display', 'parent_event', 'glide',
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
            'num_beneficiaries', 'amount_requested', 'amount_funded', 'start_date', 'end_date', 'created_at',
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
            'num_beneficiaries', 'amount_requested', 'amount_funded', 'start_date', 'end_date', 'created_at',
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
        instance.save()
        return instance

    def get_is_ifrc_admin(self, obj):
        return obj.groups.filter(name__iexact="IFRC Admins").exists()


class UserMeSerializer(UserSerializer):
    is_admin_for_countries = serializers.SerializerMethodField()
    is_admin_for_regions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + ('is_admin_for_countries', 'is_admin_for_regions')

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


class ActionSerializer(ModelSerializer):
    class Meta:
        model = Action
        fields = ('name', 'id', 'organizations', 'field_report_types', 'category',)


class ActionsTakenSerializer(ModelSerializer):
    actions = ActionSerializer(many=True)

    class Meta:
        model = ActionsTaken
        fields = ('organization', 'actions', 'summary', 'id',)


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
        country_fields = {
            'id': '',
            'name': ''
        }
        countries = obj.countries.all()
        if len(countries) > 0:
            country_fields['id'] = ', '.join([str(country.id) for country in countries])
            country_fields['name'] = ', '.join([str(country.name) for country in countries])
        return country_fields

    def get_districts(self, obj):
        district_fields = {
            'id': '',
            'name': ''
        }
        districts = obj.districts.all()
        if len(districts) > 0:
            district_fields['id'] = ', '.join([str(district.id) for district in districts])
            district_fields['name'] = ', '.join([str(district.name) for district in districts])
        return district_fields

    def get_regions(self, obj):
        region_fields = {
            'id': '',
            'region_name': ''
        }
        regions = obj.regions.all()
        if len(regions) > 0:
            region_fields['id'] = ', '.join([str(region.id) for region in regions])
            region_fields['region_name'] = ', '.join([str(region.region_name) for region in regions])
        return region_fields

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
        country_fields = {
            'id': '',
            'name': '',
            'iso': '',
            'iso3': ''
        }
        countries = obj.countries.all()
        if len(countries) > 0:
            country_fields['id'] = ', '.join([str(country.id) for country in countries])
            country_fields['name'] = ', '.join([str(country.name) for country in countries])
            country_fields['iso'] = ', '.join([str(country.iso) for country in countries])
            country_fields['iso3'] = ', '.join([str(country.iso3) for country in countries])
        return country_fields

    def get_districts(self, obj):
        district_fields = {
            'id': '',
            'name': ''
        }
        districts = obj.districts.all()
        if len(districts) > 0:
            district_fields['id'] = ', '.join([str(district.id) for district in districts])
            district_fields['name'] = ', '.join([str(district.name) for district in districts])
        return district_fields

    def get_regions(self, obj):
        region_fields = {
            'id': '',
            'region_name': ''
        }
        regions = obj.regions.all()
        if len(regions) > 0:
            region_fields['id'] = ', '.join([str(region.id) for region in regions])
            region_fields['region_name'] = ', '.join([str(region.region_name) for region in regions])
        return region_fields

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

    class Meta:
        model = FieldReport
        fields = '__all__'


class CreateFieldReportSerializer(FieldReportEnumDisplayMixin, ModelSerializer):
    class Meta:
        model = FieldReport
        fields = '__all__'
