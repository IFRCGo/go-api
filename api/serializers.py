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
    class Meta:
        model = Event
        fields = ('name', 'dtype', 'countries', 'summary', 'num_affected', 'alert_level', 'glide', 'disaster_start_date', 'created_at', 'auto_generated', 'appeals', 'id',)

class DetailEventSerializer(serializers.ModelSerializer):
    appeals = RelatedAppealSerializer(many=True, read_only=True)
    contacts = EventContactSerializer(many=True, read_only=True)
    key_figures = KeyFigureSerializer(many=True, read_only=True)
    snippets = SnippetSerializer(many=True, read_only=True)
    class Meta:
        model = Event
        fields = ('name', 'dtype', 'countries', 'summary', 'num_affected', 'alert_level', 'glide', 'disaster_start_date', 'created_at', 'auto_generated', 'appeals', 'contacts', 'key_figures', 'snippets', 'id',)

class SituationReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SituationReport
        fields = ('created_at', 'name', 'document', 'document_url', 'event', 'id',)

class AppealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appeal
        fields = ('aid', 'name', 'dtype', 'atype', 'status', 'code', 'sector', 'num_beneficiaries', 'amount_requested', 'amount_funded', 'start_date', 'end_date', 'created_at', 'modified_at', 'event', 'country', 'region', 'id',)

class AppealDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppealDocument
        fields = ('created_at', 'name', 'document', 'document_url', 'appeal', 'id',)

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('country', 'org', 'org_type', 'city', 'department', 'position', 'phone_number')

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'profile',)

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
    event = ListEventSerializer()
    class Meta:
        model = FieldReport
        fields = ('created_at', 'summary', 'event', 'dtype', 'countries', 'id',)

class DetailFieldReportSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    dtype = DisasterTypeSerializer()
    contacts = FieldReportContactSerializer(many=True)
    actions_taken = ActionsTakenSerializer(many=True)
    sources = SourceSerializer(many=True)
    class Meta:
        model = FieldReport
        fields = '__all__'
