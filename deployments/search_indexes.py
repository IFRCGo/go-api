from haystack import indexes

from deployments.models import Project, ERU


class ProjectIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.EdgeNgramField(model_attr='name')
    event_name = indexes.CharField(model_attr='event__name')
    start_date = indexes.DateTimeField(model_attr='start_date', null=True)
    reporting_ns = indexes.CharField(model_attr='reporting_ns__name')
    project_districts = indexes.MultiValueField()
    sector = indexes.CharField(model_attr='get_primary_sector_display')
    tags = indexes.MultiValueField(model_attr='get_secondary_sectors_display')
    target_total = indexes.IntegerField(model_attr='target_total', null=True)
    event_id = indexes.IntegerField(model_attr='event__id', null=True)
    reporting_ns_id = indexes.IntegerField(model_attr='reporting_ns__id')

    def get_model(self):
        return Project

    def prepare_project_districts(self, obj):
        return [district.name for district in obj.project_districts.all()]

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class ERUIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    event_name = indexes.EdgeNgramField(model_attr='event__name')
    country = indexes.CharField(model_attr='deployed_to__name')
    personnel_units = indexes.IntegerField(model_attr='units', null=True)
    equipment_units = indexes.IntegerField(model_attr='equipment_units', null=True)
    eru_type = indexes.CharField(model_attr='get_type_display')
    eru_owner = indexes.CharField(model_attr='eru_owner__national_society_country__society_name')
    event_id = indexes.IntegerField(model_attr='event__id', null=True)
    country_id = indexes.IntegerField(model_attr='deployed_to__id')

    def get_model(self):
        return ERU

    def index_queryset(self, using=None):
        return self.get_model().objects.all()