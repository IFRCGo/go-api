from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    DisasterType,
    Region,
    Country,

    KeyFigure,
    Snippet,
    EventContact,
    Event,
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
        fields = ('name', 'id',)

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('name', 'iso', 'society_name', 'society_url', 'region', 'id',)

class MiniCountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('name', 'iso', 'society_name', 'id',)

class RelatedAppealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appeal
        fields = ('aid', 'num_beneficiaries', 'amount_requested', 'amount_funded', 'id',)

class KeyFigureSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyFigure
        fields = ('number', 'deck', 'source', 'id',)

class SnippetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snippet
        fields = ('snippet', 'id',)

class EventContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventContact
        fields = ('ctype', 'name', 'title', 'email', 'event', 'id',)

# The list serializer can include a smaller subset of the to-many fields.
# Also include a very minimal one for linking, and no other related fields.
class MiniEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('name', 'dtype', 'id',)

class ListEventSerializer(serializers.ModelSerializer):
    appeals = RelatedAppealSerializer(many=True, read_only=True)
    countries = MiniCountrySerializer(many=True)
    class Meta:
        model = Event
        fields = ('name', 'dtype', 'countries', 'summary', 'num_affected', 'alert_level', 'glide', 'disaster_start_date', 'created_at', 'auto_generated', 'appeals', 'id',)

class DetailEventSerializer(serializers.ModelSerializer):
    appeals = RelatedAppealSerializer(many=True, read_only=True)
    contacts = EventContactSerializer(many=True, read_only=True)
    key_figures = KeyFigureSerializer(many=True, read_only=True)
    snippets = SnippetSerializer(many=True, read_only=True)
    countries = MiniCountrySerializer(many=True)
    class Meta:
        model = Event
        fields = ('name', 'dtype', 'countries', 'summary', 'num_affected', 'alert_level', 'glide', 'disaster_start_date', 'created_at', 'auto_generated', 'appeals', 'contacts', 'key_figures', 'snippets', 'id',)

class SituationReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SituationReport
        fields = ('created_at', 'name', 'document', 'document_url', 'event', 'id',)

class AppealSerializer(serializers.ModelSerializer):
    country = MiniCountrySerializer()
    class Meta:
        model = Appeal
        fields = ('aid', 'name', 'dtype', 'atype', 'status', 'code', 'sector', 'num_beneficiaries', 'amount_requested', 'amount_funded', 'start_date', 'end_date', 'created_at', 'modified_at', 'event', 'country', 'region', 'id',)

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
        fields = ('stype', 'rtype', 'country', 'region', 'dtype', 'lookup_id',)

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

class FieldReportContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldReportContact
        fields = ('ctype', 'name', 'title', 'email', 'id',)

class ActionsTakenSerializer(serializers.ModelSerializer):
    actions = serializers.SlugRelatedField(many=True, slug_field='name', read_only=True)
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
    class Meta:
        model = FieldReport
        fields = ('created_at', 'summary', 'event', 'dtype', 'countries', 'visibility', 'id',)

class DetailFieldReportSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    dtype = DisasterTypeSerializer()
    contacts = FieldReportContactSerializer(many=True)
    actions_taken = ActionsTakenSerializer(many=True)
    sources = SourceSerializer(many=True)
    class Meta:
        model = FieldReport
        fields = '__all__'
