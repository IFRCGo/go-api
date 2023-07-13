from haystack import indexes

from dref.models import Dref, DrefOperationalUpdate


class DrefIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.EdgeNgramField(model_attr='title')
    created_at = indexes.DateTimeField(model_attr='created_at')
    code = indexes.CharField(model_attr='appeal_code', null=True)
    country_name = indexes.CharField(model_attr='national_society__name', null=True)
    country_id = indexes.CharField(model_attr='national_society__id', null=True)
    iso3 = indexes.CharField(model_attr='national_society__iso3', null=True)

    def get_model(self):
        return Dref

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class DrefOperationalUpdateIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True, null=True)
    name = indexes.EdgeNgramField(model_attr='title')
    created_at = indexes.DateTimeField(model_attr='created_at')
    code = indexes.CharField(model_attr='appeal_code', null=True)
    country_name = indexes.CharField(model_attr='national_society__name', null=True)
    country_id = indexes.CharField(model_attr='national_society__id', null=True)
    iso3 = indexes.CharField(model_attr='national_society__iso3', null=True)

    def get_model(self):
        return DrefOperationalUpdate

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
