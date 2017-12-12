from tastypie import fields
from tastypie.resources import ModelResource, ALL_WITH_RELATIONS
from tastypie.authorization import Authorization
from django.contrib.auth.models import User
from .models import (
    DisasterType,
    Event,
    Country,
    Region,
    Appeal,
    FieldReport,
    Profile,
    Contact,
    ActionsTaken,
    Action
)
from .authentication import ExpiringApiKeyAuthentication
from .authorization import FieldReportAuthorization, UserProfileAuthorization


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
        authentication = ExpiringApiKeyAuthentication()
        authorization = Authorization()


class DisasterTypeResource(ModelResource):
    class Meta:
        queryset = DisasterType.objects.all()
        resource_name = 'disaster_type'
        allowed_methods = ['get']
        authorization = Authorization()


class ContactResource(ModelResource):
    class Meta:
        queryset = Contact.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()
        authentication = ExpiringApiKeyAuthentication()


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


class ActionResource(ModelResource):
    class Meta:
        queryset = Action.objects.all()
        authorization = Authorization()
        allowed_methods = ['get']


class ActionsTakenResource(ModelResource):
    actions = fields.ToManyField(ActionResource, 'actions', full=True, null=True)
    class Meta:
        queryset = ActionsTaken.objects.all()
        resource_name = 'actions_taken'
        allowed_methods = ['get']
        authorization = Authorization()


class EventResource(ModelResource):
    dtype = fields.ForeignKey(DisasterTypeResource, 'dtype', full=True)
    appeals = fields.ToManyField(RelatedAppealResource, 'appeals', null=True, full=True)
    field_reports = fields.ToManyField(RelatedFieldReportResource, 'field_reports', null=True, full=True)
    countries = fields.ToManyField(CountryResource, 'countries', full=True)
    contacts = fields.ToManyField(ContactResource, 'contacts', full=True, null=True)

    # Don't return field reports if the user isn't authenticated
    def dehydrate_field_reports(self, bundle):
        if self.is_authenticated(bundle.request):
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
            'name': ('exact', 'iexact'),
            'appeals': ALL_WITH_RELATIONS,
            'eid': ('exact', 'in'),
            'created_at': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'disaster_start_date': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
        }
        ordering = ['disaster_start_date']


class AppealResource(ModelResource):
    dtype = fields.ForeignKey(DisasterTypeResource, 'dtype', full=True)
    event = fields.ForeignKey(RelatedEventResource, 'event', full=True, null=True)
    country = fields.ForeignKey(CountryResource, 'country', full=True, null=True)
    class Meta:
        queryset = Appeal.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()
        filtering = {
            'event': ALL_WITH_RELATIONS,
            'aid': ('exact', 'in'),
            'status': ('exact', 'iexact', 'in'),
            'code': ('exact', 'in'),
            'amount_requested': ('gt', 'gte', 'lt', 'lte', 'range'),
            'amount_funded': ('gt', 'gte', 'lt', 'lte', 'range'),
            'num_beneficiaries': ('gt', 'gte', 'lt', 'lte', 'range'),
            'atype': ('exact', 'in'),
            'country': ('exact', 'in'),
            'created_at': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'start_date': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'end_date': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
        }
        ordering = ['start_date', 'end_date']


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
    event = fields.ForeignKey(RelatedEventResource, 'event', full=True, null=True)
    contacts = fields.ToManyField(ContactResource, 'contacts', full=True, null=True)
    actions_taken = fields.ToManyField(ActionsTakenResource, 'actions_taken', full=True, null=True)
    class Meta:
        queryset = FieldReport.objects.all()
        resource_name = 'field_report'
        always_return_data = True
        authentication = ExpiringApiKeyAuthentication()
        authorization = FieldReportAuthorization()
        filtering = {
            'created_at': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'id': ('exact', 'in'),
            'rid': ('exact', 'in'),
            'status': ('exact', 'in'),
            'request_assistance': ('exact')
        }

