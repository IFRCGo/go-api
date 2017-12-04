from tastypie import fields
from tastypie.resources import ModelResource, ALL_WITH_RELATIONS
from tastypie.authorization import Authorization, DjangoAuthorization
from django.contrib.auth.models import User
from .models import (
    DisasterType,
    Event,
    Country,
    Appeal,
    FieldReport,
    Profile,
    Contact,
    ActionsTaken,
    Action
)
from .authentication import ExpiringApiKeyAuthentication
from .authorization import FieldReportAuthorization


# Duplicate resources that do not query 's related objects.
# https://stackoverflow.com/questions/11570443/django-tastypie-throws-a-maximum-recursion-depth-exceeded-when-full-true-on-re
class RelatedAppealResource(ModelResource):
    class Meta:
        queryset = Appeal.objects.all()


class RelatedEventResource(ModelResource):
    class Meta:
        queryset = Event.objects.all()


class RelatedFieldReportResource(ModelResource):
    class Meta:
        queryset = FieldReport.objects.all()


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

    # Don't return field reports if the user isn't authenticated
    def dehydrate_field_reports(self, bundle):
        if self.is_authenticated(bundle.request):
            return bundle.data['field_reports']
        else:
            return None


    # Attach data from model instance methods
    def dehydrate(self, bundle):
        bundle.data['countries'] = bundle.obj.countries()
        bundle.data['start_date'] = bundle.obj.start_date()
        bundle.data['end_date'] = bundle.obj.end_date()
        return bundle

    class Meta:
        queryset = Event.objects.select_related().all()
        allowed_methods = ['get']
        authorization = Authorization()
        filtering = {
            'code': ('exact', 'in'),
            'created_at': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'status': ('iexact'),
        }


class AppealResource(ModelResource):
    event = fields.ForeignKey(RelatedEventResource, 'event', full=True, null=True)
    country = fields.ForeignKey(CountryResource, 'country', full=True, null=True)
    class Meta:
        queryset = Appeal.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()
        filtering = {
            'aid': ('exact', 'in'),
            'amount_requested': ('gt', 'gte', 'lt', 'lte', 'range'),
            'amount_funded': ('gt', 'gte', 'lt', 'lte', 'range'),
            'num_beneficiaries': ('gt', 'gte', 'lt', 'lte', 'range'),
            'atype': ('exact', 'in'),
            'country': ('exact', 'in'),
            'created_at': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'start_date': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'end_date': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
        }


class FieldReportResource(ModelResource):
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


class UserResource(ModelResource):
    profile = fields.ToOneField('api.resources.ProfileResource', 'profile', full=True)
    subscription = fields.ToManyField('notifications.resources.SubscriptionResource', 'subscription', full=True)



    class Meta:
        queryset = User.objects.all()
        fields = ['username', 'first_name', 'last_name', 'email']
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get', 'post', 'put', 'patch']
        filtering = {
            'username': ('exact', 'startswith'),
        }
        authentication = ExpiringApiKeyAuthentication()
        authorization = DjangoAuthorization()


class ProfileResource(ModelResource):
    class Meta:
        queryset = Profile.objects.all()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        authentication = ExpiringApiKeyAuthentication()
        authorization = DjangoAuthorization()
