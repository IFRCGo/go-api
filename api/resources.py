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
            return bundle['field_reports']
        else:
            return None

    class Meta:
        queryset = Event.objects.select_related().all()
        allowed_methods = ['get']
        authorization = Authorization()


class AppealResource(ModelResource):
    event = fields.ForeignKey(RelatedEventResource, 'event', full=True, null=True)
    country = fields.ForeignKey(CountryResource, 'country', full=True, null=True)
    class Meta:
        queryset = Appeal.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()


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


class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        fields = ['username', 'first_name', 'last_name', 'email']
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get', 'post', 'put', 'patch']
        filtering = {
            'username': ('exact'),
        }
        authentication = ExpiringApiKeyAuthentication()
        authorization = DjangoAuthorization()


class ProfileResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user', full=True)
    class Meta:
        queryset = Profile.objects.all()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        filtering = {
            'user': ALL_WITH_RELATIONS,
        }
        authentication = ExpiringApiKeyAuthentication()
        authorization = DjangoAuthorization()
