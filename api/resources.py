from tastypie import fields
from tastypie.resources import ModelResource, ALL_WITH_RELATIONS
from tastypie.authorization import DjangoAuthorization
from django.contrib.auth.models import User
from .models import DisasterType, Event, Country, FieldReport, Profile
from .authentication import ExpiringApiKeyAuthentication


class DisasterTypeResource(ModelResource):
    class Meta:
        queryset = DisasterType.objects.all()
        resource_name = 'disaster_type'


class EventResource(ModelResource):
    class Meta:
        queryset = Event.objects.all()
        resource_name = 'event'


class CountryResource(ModelResource):
    class Meta:
        queryset = Country.objects.all()
        resource_name = 'country'


class FieldReportResource(ModelResource):
    class Meta:
        queryset = FieldReport.objects.all()
        resource_name = 'field_report'
        authentication = ExpiringApiKeyAuthentication()


class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        fields = ['username', 'first_name', 'last_name']
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get', 'post', 'put', 'patch']


class ProfileResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')
    class Meta:
        queryset = Profile.objects.all()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get', 'put', 'patch']
        resource_name = 'profile'
        authorization = DjangoAuthorization()
        filtering = {
            'user': ALL_WITH_RELATIONS
        }
