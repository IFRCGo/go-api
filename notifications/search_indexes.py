from haystack import indexes

from notifications.models import SurgeAlert


class SurgeIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.EdgeNgramField(model_attr="message")
    molnix_tag = indexes.MultiValueField(null=True)
    event_name = indexes.CharField(model_attr="event__name")
    country_name = indexes.CharField(model_attr="country__name")
    start_date = indexes.DateTimeField(model_attr="start", null=True)
    alert_date = indexes.DateTimeField(model_attr="opens", null=True)
    event_id = indexes.IntegerField(model_attr="event__id", null=True)
    deadline = indexes.DateTimeField(model_attr="closes", null=True)
    surge_type = indexes.CharField(model_attr="get_atype_display")
    status = indexes.CharField(model_attr="molnix_status", null=True)
    country_id = indexes.IntegerField(model_attr="country__id")
    iso3 = indexes.CharField(model_attr="country__iso3", null=True)
    visibility = indexes.CharField(model_attr="event__get_visibility_display", null=True)

    def get_model(self):
        return SurgeAlert

    def prepare_molnix_tag(self, obj):
        return [molnix.name for molnix in obj.molnix_tags.all()]

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
