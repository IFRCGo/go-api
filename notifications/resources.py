from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization, DjangoAuthorization
from .models import SurgeAlert, Subscription
from api.authentication import ExpiringApiKeyAuthentication
from api.resources import (
    CountryResource,
    RegionResource,
    DisasterTypeResource,
    RelatedEventResource,
)
from api.public_resource import PublicModelResource

class SurgeAlertResource(PublicModelResource):
    event = fields.ForeignKey(RelatedEventResource, 'event', null=True, full=True)
    def dehydrate(self, bundle):
        if self.has_valid_api_key(bundle.request) or not bundle.data['is_private']:
            return bundle.data
        else:
            result = bundle.data
            result['message'] = 'This is a private alert. You must be logged in to view it.'
            return result

    class Meta:
        queryset = SurgeAlert.objects.all()
        resource_name = 'surge_alert'
        allowed_methods = ['get']
        authorization = Authorization()

        filtering = {
            'atype': ('exact', 'in'),
            'created_at': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'category': ('exact', 'in'),
            'operation': ('exact', 'in'),
            'message': ('exact', 'in'),
            'deployment_needed': ('exact', 'in'),
        }

        ordering = [
            'atype',
            'created_at',
            'category',
            'operation',
            'message',
            'deployment_needed',
        ]


class SubscriptionResource(ModelResource):
    country = fields.ForeignKey(CountryResource, 'country', full=True, null=True)
    region = fields.ForeignKey(RegionResource, 'region', full=True, null=True)
    dtype = fields.ForeignKey(DisasterTypeResource, 'dtype', full=True, null=True)
    class Meta:
        queryset = Subscription.objects.all()
        authorization = DjangoAuthorization()
        authentication = ExpiringApiKeyAuthentication()
