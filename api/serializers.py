import json
from rest_framework import serializers
from django.contrib.auth.models import User
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

class DisasterTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisasterType
        fields = ('name', 'summary', 'id',)

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ('name', 'id', 'region_name')


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('name', 'iso', 'society_name', 'society_url', 'region', 'overview', 'key_priorities', 'inform_score', 'id', 'url_ifrc',)

class MiniCountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('name', 'iso', 'society_name', 'id', 'record_type',)

class RegoCountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('name', 'society_name', 'region', 'id',)

class NotCountrySerializer(serializers.ModelSerializer): # fake serializer for a short data response for PER
    class Meta:
        model = Country
        fields = ('id',)

class DistrictSerializer(serializers.ModelSerializer):
    country = MiniCountrySerializer()
    class Meta:
        model = District
        fields = ('name', 'code', 'country', 'country_iso', 'country_name', 'id',)

class MiniDistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ('name', 'code', 'country_iso', 'country_name', 'id', 'is_enclave',)


class RegionKeyFigureSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegionKeyFigure
        fields = ('region', 'figure', 'deck', 'source', 'visibility', 'id',)

class CountryKeyFigureSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryKeyFigure
        fields = ('country', 'figure', 'deck', 'source', 'visibility', 'id',)

class RegionSnippetSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegionSnippet
        fields = ('region', 'snippet', 'image', 'visibility', 'id',)

class CountrySnippetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountrySnippet
        fields = ('country', 'snippet', 'image', 'visibility', 'id',)

class RegionLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegionLink
        fields = ('title', 'url', 'id',)

class CountryLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryLink
        fields = ('title', 'url', 'id',)

class RegionContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegionContact
        fields = ('ctype', 'name', 'title', 'email', 'id',)

class CountryContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryContact
        fields = ('ctype', 'name', 'title', 'email', 'id',)

class RegionRelationSerializer(serializers.ModelSerializer):
    links = RegionLinkSerializer(many=True, read_only=True)
    contacts = RegionContactSerializer(many=True, read_only=True)
    class Meta:
        model = Region
        fields = ('links', 'contacts', 'name', 'id',)

class CountryRelationSerializer(serializers.ModelSerializer):
    links = CountryLinkSerializer(many=True, read_only=True)
    contacts = CountryContactSerializer(many=True, read_only=True)
    class Meta:
        model = Country
        fields = ('links', 'contacts', 'name', 'iso', 'society_name', 'society_url', 'region', 'overview', 'key_priorities', 'inform_score', 'id', 'url_ifrc',)

class RelatedAppealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appeal
        fields = ('aid', 'num_beneficiaries', 'amount_requested', 'amount_funded', 'status', 'start_date', 'id',)

class KeyFigureSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyFigure
        fields = ('number', 'deck', 'source', 'id',)

class SnippetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snippet
        fields = ('event', 'snippet', 'image', 'visibility', 'position', 'tab', 'id',)

class EventContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventContact
        fields = ('ctype', 'name', 'title', 'email', 'phone', 'event', 'id',)

class FieldReportContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldReportContact
        fields = ('ctype', 'name', 'title', 'email', 'phone', 'id',)

class MiniFieldReportSerializer(serializers.ModelSerializer):
    contacts = FieldReportContactSerializer(many=True)
    class Meta:
        model = FieldReport
        fields = (
            'summary', 'status', 'description', 'contacts', 'created_at', 'updated_at', 'report_date', 'id',
            'num_injured', 'num_dead', 'num_missing', 'num_affected', 'num_displaced', 'num_assisted', 'num_localstaff', 'num_volunteers', 'num_expats_delegates',
            'gov_num_injured', 'gov_num_dead', 'gov_num_missing', 'gov_num_affected', 'gov_num_displaced',  'gov_num_assisted',
            'other_num_injured', 'other_num_dead', 'other_num_missing', 'other_num_affected', 'other_num_displaced', 'other_num_assisted',
            'num_potentially_affected', 'gov_num_potentially_affected', 'other_num_potentially_affected', 'num_highest_risk', 'gov_num_highest_risk', 'other_num_highest_risk', 'affected_pop_centres', 'gov_affected_pop_centres', 'other_affected_pop_centres',
            'health_min_cases', 'health_min_suspected_cases', 'health_min_probable_cases', 'health_min_confirmed_cases', 'health_min_num_dead',
            'who_cases', 'who_suspected_cases', 'who_probable_cases', 'who_confirmed_cases', 'who_num_dead',
            'other_cases', 'other_suspected_cases', 'other_probable_cases', 'other_confirmed_cases',
        )

# The list serializer can include a smaller subset of the to-many fields.
# Also include a very minimal one for linking, and no other related fields.
class MiniEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('name', 'dtype', 'id', 'slug', 'parent_event',)


class ListMiniEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        # NOTE: Only use fields which are valid in Event.objects.values(<HERE>)
        fields = ('id', 'name', 'slug', 'auto_generated_source')


class ListEventSerializer(serializers.ModelSerializer):
    appeals = RelatedAppealSerializer(many=True, read_only=True)
    countries = MiniCountrySerializer(many=True)
    field_reports = MiniFieldReportSerializer(many=True, read_only=True)
    dtype = DisasterTypeSerializer()
    class Meta:
        model = Event
        fields = ('name', 'dtype', 'countries', 'summary', 'num_affected', 'ifrc_severity_level', 'glide', 'disaster_start_date', 'created_at', 'auto_generated', 'appeals', 'is_featured', 'is_featured_region', 'field_reports', 'updated_at', 'id', 'slug', 'parent_event',)

class ListEventDeploymentsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    deployments = serializers.IntegerField()


class DetailEventSerializer(serializers.ModelSerializer):
    appeals = RelatedAppealSerializer(many=True, read_only=True)
    contacts = EventContactSerializer(many=True, read_only=True)
    key_figures = KeyFigureSerializer(many=True, read_only=True)
    districts = MiniDistrictSerializer(many=True)
    countries = MiniCountrySerializer(many=True)
    field_reports = MiniFieldReportSerializer(many=True, read_only=True)
    class Meta:
        model = Event
        fields = ('name', 'dtype', 'countries', 'districts', 'summary', 'num_affected', 'ifrc_severity_level', 'glide', 'disaster_start_date', 'created_at', 'auto_generated', 'appeals', 'contacts', 'key_figures', 'is_featured', 'is_featured_region', 'field_reports', 'hide_attached_field_reports', 'updated_at', 'id', 'slug', 'tab_one_title', 'tab_two_title', 'tab_three_title', 'parent_event',)
        lookup_field = 'slug'

class SituationReportTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SituationReportType
        fields = ('type', 'id', 'is_primary',)

class SituationReportSerializer(serializers.ModelSerializer):
    type = SituationReportTypeSerializer()
    class Meta:
        model = SituationReport
        fields = ('created_at', 'name', 'document', 'document_url', 'event', 'type', 'id', 'is_pinned',)

class AppealSerializer(serializers.ModelSerializer):
    country = MiniCountrySerializer()
    dtype = DisasterTypeSerializer()
    region = RegionSerializer()
    class Meta:
        model = Appeal
        fields = ('aid', 'name', 'dtype', 'atype', 'status', 'code', 'sector', 'num_beneficiaries', 'amount_requested', 'amount_funded', 'start_date', 'end_date', 'created_at', 'modified_at', 'event', 'needs_confirmation', 'country', 'region', 'id',)

class AppealDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppealDocument
        fields = ('created_at', 'name', 'document', 'document_url', 'appeal', 'id',)

class ProfileSerializer(serializers.ModelSerializer):
    country = MiniCountrySerializer()
    class Meta:
        model = Profile
        fields = ('country', 'org', 'org_type', 'city', 'department', 'position', 'phone_number')

class MiniSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('stype', 'rtype', 'country', 'region', 'event', 'dtype', 'lookup_id',)

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    subscription = MiniSubscriptionSerializer(many=True)
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'profile', 'subscription',)

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


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ('name', 'id', 'organizations', 'field_report_types', 'category',)

class ActionsTakenSerializer(serializers.ModelSerializer):
    actions = ActionSerializer(many=True)
    class Meta:
        model = ActionsTaken
        fields = ('organization', 'actions', 'summary', 'id',)

class SourceSerializer(serializers.ModelSerializer):
    stype = serializers.SlugRelatedField(slug_field='name', read_only=True)
    class Meta:
        model = Source
        fields = ('stype', 'spec', 'id',)

class ListFieldReportSerializer(serializers.ModelSerializer):
    countries = MiniCountrySerializer(many=True)
    dtype = DisasterTypeSerializer()
    event = MiniEventSerializer()
    actions_taken = ActionsTakenSerializer(many=True)
    class Meta:
        model = FieldReport
        fields = '__all__'

class ListFieldReportCsvSerializer(serializers.ModelSerializer):
    countries = MiniCountrySerializer(many=True)
    dtype = DisasterTypeSerializer()
    event = MiniEventSerializer()
    # actions_taken = ActionsTakenSerializer(many=True)
    actions_taken = serializers.SerializerMethodField('get_actions_taken_for_organization')

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

class DetailFieldReportSerializer(serializers.ModelSerializer):
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

class CreateFieldReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldReport
        fields = '__all__'
