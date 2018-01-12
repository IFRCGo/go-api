from tastypie import fields
from tastypie.resources import ModelResource, ALL_WITH_RELATIONS
from api.authentication import ExpiringApiKeyAuthentication
from api.resources import (
    CountryResource,
    RegionResource,
    EventResource,
    DisasterTypeResource,
)
from .models import (
    ERUOwner,
    ERU,
    Heop,
    Fact,
    Rdit,
)


class ERUOwnerResource(ModelResource):
    eru_set = fields.ToManyField('deployments.resources.ERUResource', 'eru_set', null=True, full=True)
    class Meta:
        queryset = ERUOwner.objects.all()
        authentication = ExpiringApiKeyAuthentication()
        resource_name = 'eru_owner'
        allowed_methods = ['get']
        filtering = {
            'country': ('exact', 'in'),
        }


class RelatedERUOwnerResource(ModelResource):
    country = fields.ForeignKey(CountryResource, 'country', full=True)
    class Meta:
        queryset = ERUOwner.objects.all()
        allowed_methods = ['get']


class ERUResource(ModelResource):
    countries = fields.ToManyField(CountryResource, 'countries', full=True, null=True)
    eru_owner = fields.ForeignKey(RelatedERUOwnerResource, 'eru_owner', full=True)
    class Meta:
        queryset = ERU.objects.all()
        authentication = ExpiringApiKeyAuthentication()
        filtering = {
            'eru_owner': ALL_WITH_RELATIONS,
            'type': ('exact', 'in'),
            'countries': ('in'),
        }
        allowed_methods = ['get']


class HeopResource(ModelResource):
    country = fields.ForeignKey(CountryResource, 'country', full=True)
    region = fields.ForeignKey(RegionResource, 'region', full=True)
    event = fields.ForeignKey(EventResource, 'event', null=True)
    dtype = fields.ForeignKey(DisasterTypeResource, 'dtype', null=True, full=True)
    class Meta:
        queryset = Heop.objects.all()
        allowed_methods = ['get']
        authentication = ExpiringApiKeyAuthentication()
        filtering = {
            'start_date': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'end_date': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'country': ('exact', 'in'),
            'region': ('exact', 'in'),
            'event': ('exact', 'in'),
            'dtype': ('exact', 'in'),
            'person': ('exact', 'in'),
            'role': ('exact', 'in'),
        }
        ordering = [
            'start_date',
            'end_date',
            'country',
            'region',
            'event',
            'dtype',
            'person',
            'role',
        ]


class FactResource(ModelResource):
    country = fields.ForeignKey(CountryResource, 'country', full=True)
    region = fields.ForeignKey(RegionResource, 'region', full=True)
    event = fields.ForeignKey(EventResource, 'event', null=True)
    dtype = fields.ForeignKey(DisasterTypeResource, 'dtype', null=True, full=True)
    class Meta:
        queryset = Fact.objects.all()
        allowed_methods = ['get']
        authentication = ExpiringApiKeyAuthentication()
        filtering = {
            'start_date': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'end_date': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'country': ('exact', 'in'),
            'region': ('exact', 'in'),
            'event': ('exact', 'in'),
            'dtype': ('exact', 'in'),
            'person': ('exact', 'in'),
            'role': ('exact', 'in'),
        }
        ordering = [
            'start_date',
            'end_date',
            'country',
            'region',
            'event',
            'dtype',
            'person',
            'role',
        ]


class RditResource(ModelResource):
    country = fields.ForeignKey(CountryResource, 'country', full=True)
    region = fields.ForeignKey(RegionResource, 'region', full=True)
    event = fields.ForeignKey(EventResource, 'event', null=True)
    dtype = fields.ForeignKey(DisasterTypeResource, 'dtype', null=True, full=True)
    class Meta:
        queryset = Rdit.objects.all()
        allowed_methods = ['get']
        authentication = ExpiringApiKeyAuthentication()
        filtering = {
            'start_date': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'end_date': ('gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day'),
            'country': ('exact', 'in'),
            'region': ('exact', 'in'),
            'event': ('exact', 'in'),
            'dtype': ('exact', 'in'),
            'person': ('exact', 'in'),
            'role': ('exact', 'in'),
        }
        ordering = [
            'start_date',
            'end_date',
            'country',
            'region',
            'event',
            'dtype',
            'person',
            'role',
        ]
