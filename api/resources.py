
from tastypie.resources import ModelResource
from .models import DisasterType, Event, Country, FieldReport


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
