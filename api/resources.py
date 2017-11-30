from tastypie import fields
from tastypie.resources import ModelResource, ALL_WITH_RELATIONS
from tastypie.authorization import Authorization, DjangoAuthorization
from django.contrib.auth.models import User
from .models import DisasterType, Event, Country, FieldReport, Profile, Contact, ActionsTaken
from .authentication import ExpiringApiKeyAuthentication
from .authorization import FieldReportAuthorization


class DisasterTypeResource(ModelResource):
    class Meta:
        queryset = DisasterType.objects.all()
        resource_name = 'disaster_type'
        allowed_methods = ['get']
        authorization = Authorization()


class EventResource(ModelResource):
    class Meta:
        queryset = Event.objects.all()
        resource_name = 'event'
        alowed_methods = ['get']
        authorization = Authorization()


class ContactResource(ModelResource):
    class Meta:
        queryset = Contact.objects.all()
        resource_name = 'contact'
        allowed_methods = ['get']
        authorization = Authorization()


class CountryResource(ModelResource):
    class Meta:
        queryset = Country.objects.all()
        resource_name = 'country'
        allowed_methods = ['get']
        authorization = Authorization()


class ActionsTakenResource(ModelResource):
    class Meta:
        queryset = ActionsTaken.objects.all()
        resource_name = 'actions_taken'
        allowed_methods = ['get']
        authorization = Authorization()


class FieldReportResource(ModelResource):
    dtype = fields.ForeignKey(DisasterTypeResource, 'dtype', full=True)
    countries = fields.ToManyField(CountryResource, 'countries', full=True)
    event = fields.ForeignKey(EventResource, 'event', full=True, null=True)
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
        resource_name = 'user'
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
        resource_name = 'profile'
        filtering = {
            'user': ALL_WITH_RELATIONS,
        }
        authentication = ExpiringApiKeyAuthentication()
        authorization = DjangoAuthorization()
