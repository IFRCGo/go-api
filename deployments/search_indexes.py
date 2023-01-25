from haystack import indexes

from deployments.models import Project


class ProjectIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name')
    event_name = indexes.CharField(model_attr='event__name')
    start_date = indexes.DateTimeField(model_attr='start_date', null=True)
    reporting_ns = indexes.CharField(model_attr='reporting_ns__name')
    project_districts = indexes.MultiValueField()
    sector = indexes.CharField(model_attr='get_primary_sector_display')
    tags = indexes.MultiValueField(model_attr='get_secondary_sectors_display')
    target_total = indexes.IntegerField(model_attr='target_total')

    def get_model(self):
        return Project

    def prepare_project_districts(self, obj):
        return [district.name for district in obj.project_districts.all()]

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


