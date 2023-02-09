from haystack import indexes

from api.models import (
    Country,
    Event,
    Appeal,
    FieldReport,
    Region,
    District,
)

class RegionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.EdgeNgramField(model_attr='get_name_display')

    def get_model(self):
        return Region

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class CountryIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.EdgeNgramField(model_attr='name')
    society_name = indexes.CharField(model_attr='society_name', null=True)

    def get_model(self):
        return Country

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class DistrictIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.EdgeNgramField(model_attr='name')
    country_name = indexes.CharField(model_attr='country__name', null=True)
    country_id = indexes.CharField(model_attr='country__id', null=True)

    def get_model(self):
        return District

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class AppealIndex(indexes.Indexable, indexes.SearchIndex):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.EdgeNgramField(model_attr='name')
    visibility = indexes.CharField(model_attr='event__visibility', null=True)
    appeal_type = indexes.CharField(model_attr='get_atype_display')
    code = indexes.CharField(model_attr='code')
    event_name = indexes.CharField(model_attr='event__name', null=True)
    country_name = indexes.CharField(model_attr='country__name')
    start_date = indexes.DateTimeField(model_attr='start_date', null=True)
    country_id = indexes.IntegerField(model_attr='country__id')
    event_id = indexes.IntegerField(model_attr='event__id', null=True)

    def get_model(self):
        return Appeal

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

class EmergenciesIndex(indexes.Indexable, indexes.SearchIndex):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.EdgeNgramField(model_attr='name')
    visibility = indexes.CharField(model_attr='visibility', null=True)
    countries = indexes.MultiValueField(null=True,)
    disaster_start_date = indexes.DateTimeField(model_attr='disaster_start_date', null=True)
    amount_requested = indexes.CharField(model_attr='appeals__amount_requested', null=True)
    amount_funded = indexes.CharField(model_attr='appeals__amount_funded', null=True)
    disaster_type = indexes.CharField(model_attr='dtype__name', null=True)
    countries_id = indexes.MultiValueField(null=True,)

    def get_model(self):
        return Event

    def prepare_countries(self, obj):
        return [country.name for country in obj.countries.all()]

    def prepare_countries_id(self, obj):
        return [country.id for country in obj.countries.all()]

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class FieldReportIndex(indexes.Indexable, indexes.SearchIndex):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.EdgeNgramField(model_attr='summary')
    visibility = indexes.CharField(model_attr='visibility', null=True)
    countries = indexes.MultiValueField(null=True)
    event_name = indexes.CharField(model_attr='event__name', null=True)
    created_at = indexes.DateTimeField(model_attr='created_at')
    event_id = indexes.IntegerField(model_attr='event__id', null=True)
    countries_id = indexes.MultiValueField(null=True,)

    def get_model(self):
        return FieldReport

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_countries(self, obj):
        return [country.name for country in obj.countries.all()]

    def prepare_countries_id(self, obj):
        return [country.id for country in obj.countries.all()]
