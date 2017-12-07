from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization, DjangoAuthorization
from .models import SurgeAlert, Subscription
from api.authentication import ExpiringApiKeyAuthentication
from api.resources import CountryResource, RegionResource, DisasterTypeResource

class SurgeAlertResource(ModelResource):
    def dehydrate_message(self, bundle):
        if self.is_authenticated(bundle.request):
            return bundle.data['summary']
        else:
            return 'You must be logged in to read private notifications'

    class Meta:
        queryset = SurgeAlert.objects.all()
        resource_name = 'surge_alert'
        allowed_methods = ['get']
        authorization = Authorization()


class SubscriptionResource(ModelResource):
    country = fields.ForeignKey(CountryResource, 'country', full=True, null=True)
    region = fields.ForeignKey(RegionResource, 'region', full=True, null=True)
    dtype = fields.ForeignKey(DisasterTypeResource, 'dtype', full=True, null=True)
    class Meta:
        queryset = Subscription.objects.all()
        authorization = DjangoAuthorization()
        authentication = ExpiringApiKeyAuthentication()
