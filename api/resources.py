from tastypie import fields
from tastypie.resources import ModelResource, ALL_WITH_RELATIONS
from tastypie.authorization import Authorization
from django.contrib.auth.models import User
from .models import (
    DisasterType,
    KeyFigure,
    Snippet,
    Event,
    EventContact,
    SituationReport,
    Country,
    Region,
    Appeal,
    AppealDocument,
    FieldReport,
    FieldReportContact,
    Profile,
    ActionsTaken,
    Action,
)
from .authentication import ExpiringApiKeyAuthentication
from .authorization import FieldReportAuthorization, UserProfileAuthorization
from .public_resource import PublicModelResource


# Duplicate resources that do not query 's related objects.
# https://stackoverflow.com/questions/11570443/django-tastypie-throws-a-maximum-recursion-depth-exceeded-when-full-true-on-re
class RelatedAppealResource(ModelResource):
    class Meta:
        queryset = Appeal.objects.all()
        filtering = {
            'status': ('exact', 'iexact', 'in'),
            'atype': ('exact', 'in'),
            'country': ('exact', 'in'),
        }


class RelatedEventResource(ModelResource):
    class Meta:
        queryset = Event.objects.all()
        filtering = {
            'eid': ('exact', 'in'),
        }
        authorization = Authorization()


class RelatedFieldReportResource(ModelResource):
    class Meta:
        queryset = FieldReport.objects.all()


class RelatedUserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        allowed_methods = ['get']
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        authentication = ExpiringApiKeyAuthentication()
        authorization = Authorization()


class DisasterTypeResource(ModelResource):
    class Meta:
        queryset = DisasterType.objects.all()
        resource_name = 'disaster_type'
        allowed_methods = ['get']
        authorization = Authorization()


class RegionResource(ModelResource):
    class Meta:
        queryset = Region.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()


class CountryResource(ModelResource):
    class Meta:
        queryset = Country.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()


class KeyFigureResource(ModelResource):
    class Meta:
        queryset = KeyFigure.objects.all()
        resource_name = 'key_figure'


class SnippetResource(ModelResource):
    class Meta:
        queryset = Snippet.objects.all()


class EventContactResource(ModelResource):
    class Meta:
        queryset = EventContact.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()
        authentication = ExpiringApiKeyAuthentication()


class EventResource(PublicModelResource):
    dtype = fields.ForeignKey(DisasterTypeResource, 'dtype', null=True, full=True)
    appeals = fields.ToManyField(RelatedAppealResource, 'appeals', null=True, full=True)
    field_reports = fields.ToManyField(RelatedFieldReportResource, 'field_reports', null=True, full=True)
    countries = fields.ToManyField(CountryResource, 'countries', full=True)
    regions = fields.ToManyField(RegionResource, 'regions', null=True, full=True, use_in='detail')
    contacts = fields.ToManyField(EventContactResource, 'eventcontact_set', full=True, null=True, use_in='detail')
    key_figures = fields.ToManyField(KeyFigureResource, 'keyfigure_set', full=True, null=True, use_in='detail')
    snippets = fields.ToManyField(SnippetResource, 'snippet_set', full=True, null=True, use_in='detail')

    # Don't return field reports if the user isn't authenticated
    def dehydrate_field_reports(self, bundle):
        if self.has_valid_api_key(bundle.request):
            return bundle.data['field_reports']
        else:
            return None

    # Attach data from model instance methods
    def dehydrate(self, bundle):
        bundle.data['start_date'] = bundle.obj.start_date()
        bundle.data['end_date'] = bundle.obj.end_date()
        return bundle

    class Meta:
        queryset = Event.objects.select_related().all()
        allowed_methods = ['get']
        authorization = Authorization()
        filtering = {
            'disaster_start_date': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'created_at': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'name': ('exact', 'iexact'),
            'dtype': ('exact', 'in'),
            'appeals': ALL_WITH_RELATIONS,
            'eid': ('exact', 'in'),
            'id': ('exact', 'in'),
            'countries': ('exact', 'in'),
            'regions': ('exact', 'in'),
        }
        ordering = [
            'disaster_start_date',
            'created_at',
            'name',
            'dtype',
            'eid',
            'summary',
            'num_affected',
            'auto_generated',
        ]


class SituationReportResource(ModelResource):
    event = fields.ForeignKey(EventResource, 'event', null=True)
    class Meta:
        queryset = SituationReport.objects.all()
        resource_name = 'situation_report'
        allowed_methods = ['get']
        filtering = {
            'event': ALL_WITH_RELATIONS,
            'created_at': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'name': ('exact', 'in'),
            'document_url': ('exact', 'iexact'),
        }


class AppealResource(ModelResource):
    dtype = fields.ForeignKey(DisasterTypeResource, 'dtype', full=True)
    event = fields.ForeignKey(RelatedEventResource, 'event', full=True, null=True)
    country = fields.ForeignKey(CountryResource, 'country', full=True, null=True)
    region = fields.ForeignKey(RegionResource, 'region', full=True, null=True, use_in='detail')
    class Meta:
        queryset = Appeal.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()
        filtering = {
            'event': ALL_WITH_RELATIONS,
            'aid': ('exact', 'in'),
            'id': ('exact', 'in'),
            'status': ('exact', 'iexact', 'in'),
            'code': ('exact', 'in'),
            'amount_requested': ('gt', 'gte', 'lt', 'lte', 'range'),
            'amount_funded': ('gt', 'gte', 'lt', 'lte', 'range'),
            'num_beneficiaries': ('gt', 'gte', 'lt', 'lte', 'range'),
            'atype': ('exact', 'in'),
            'dtype': ('exact', 'in'),
            'country': ('exact', 'in'),
            'region': ('exact', 'in'),
            'created_at': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'start_date': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'end_date': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
        }
        ordering = [
            'start_date',
            'end_date',

            'name',
            'aid',
            'atype',
            'dtype',

            'num_beneficiaries',
            'amount_requested',
            'amount_funded',

            'event',
            'country',
            'region',
            'status',
            'code',
            'sector',
        ]


class AppealDocumentResource(ModelResource):
    appeal = fields.ForeignKey(AppealResource, 'appeal', null=True)
    class Meta:
        queryset = AppealDocument.objects.all()
        authentication = ExpiringApiKeyAuthentication()
        resource_name = 'appeal_document'
        allowed_methods = ['get']
        filtering = {
            'appeal': ALL_WITH_RELATIONS,
            'created_at': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'name': ('exact', 'in'),
            'document_url': ('exact', 'iexact'),
        }


class UserResource(ModelResource):
    profile = fields.ToOneField('api.resources.ProfileResource', 'profile', full=True)
    subscription = fields.ToManyField('notifications.resources.SubscriptionResource', 'subscription', full=True)
    class Meta:
        queryset = User.objects.all()
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get', 'post', 'put', 'patch']
        filtering = {
            'username': ('exact', 'startswith'),
        }
        authentication = ExpiringApiKeyAuthentication()
        authorization = UserProfileAuthorization()


class ProfileResource(ModelResource):
    class Meta:
        queryset = Profile.objects.all()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        authentication = ExpiringApiKeyAuthentication()
        authorization = UserProfileAuthorization()


class FieldReportResource(ModelResource):
    user = fields.ForeignKey(RelatedUserResource, 'user', full=True, null=True)
    dtype = fields.ForeignKey(DisasterTypeResource, 'dtype', full=True)
    countries = fields.ToManyField(CountryResource, 'countries', full=True)
    regions = fields.ToManyField(RegionResource, 'regions', null=True, full=True, use_in='detail')
    event = fields.ForeignKey(RelatedEventResource, 'event', full=True, null=True)
    contacts = fields.ToManyField('api.resources.FieldReportContactResource', 'fieldreportcontact_set',
                                  related_name='field_report',
                                  full=True, null=True, use_in='detail')
    actions_taken = fields.ToManyField('api.resources.ActionsTakenResource', 'actionstaken_set',
                                       related_name='field_report',
                                       full=True, null=True, use_in='detail')
    class Meta:
        queryset = FieldReport.objects.all()
        resource_name = 'field_report'
        always_return_data = True
        authentication = ExpiringApiKeyAuthentication()
        authorization = FieldReportAuthorization()
        filtering = {
            'event': ALL_WITH_RELATIONS,
            'user': ALL_WITH_RELATIONS,
            'created_at': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'summary': ('exact', 'in'),
            'dtype': ('exact', 'in'),
            'id': ('exact', 'in'),
            'rid': ('exact', 'in'),
            'countries': ('exact', 'in'),
            'regions': ('exact', 'in'),
            'status': ('exact', 'in'),
            'request_assistance': ('exact')
        }
        ordering = [
            'created_at',
            'summary',
            'event',
            'dtype',
            'status',
            'request_assistance',

            'num_injured',
            'num_dead',
            'num_missing',
            'num_affected',
            'num_displaced',
            'num_assisted',
            'num_localstaff',
            'num_volunteers',
            'num_xpats_delegates',

            'gov_num_injured',
            'gov_num_dead',
            'gov_num_missing',
            'gov_num_affected',
            'gov_num_displaced',
            'gov_num_assisted',
        ]


class FieldReportContactResource(ModelResource):
    field_report = fields.ForeignKey(FieldReportResource, 'field_report')
    class Meta:
        queryset = FieldReportContact.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()
        authentication = ExpiringApiKeyAuthentication()


class ActionResource(ModelResource):
    class Meta:
        queryset = Action.objects.all()
        authorization = Authorization()
        allowed_methods = ['get']


class ActionsTakenResource(ModelResource):
    actions = fields.ToManyField(ActionResource, 'actions', full=True, null=True)
    field_report = fields.ForeignKey(FieldReportResource, 'field_report')
    class Meta:
        queryset = ActionsTaken.objects.all()
        resource_name = 'actions_taken'
        allowed_methods = ['get']
        authorization = Authorization()
