from haystack import indexes

from deployments.models import Project, ERU, Personnel


class ProjectIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.EdgeNgramField(model_attr='name')
    event_name = indexes.CharField(model_attr='event__name')
    start_date = indexes.DateTimeField(model_attr='start_date', null=True)
    end_date = indexes.DateTimeField(model_attr='end_date', null=True)
    reporting_ns = indexes.CharField(model_attr='reporting_ns__name')
    project_districts = indexes.MultiValueField()
    sector = indexes.CharField(model_attr='primary_sector__title')
    tags = indexes.MultiValueField(model_attr='secondary_sectors__title')
    target_total = indexes.IntegerField(model_attr='target_total', null=True)
    event_id = indexes.IntegerField(model_attr='event__id', null=True)
    reporting_ns_id = indexes.IntegerField(model_attr='reporting_ns__id')
    iso3 = indexes.CharField(model_attr='reporting_ns__iso3', null=True)
    visibility = indexes.CharField(model_attr='get_visibility_display', null=True)

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
    iso3 = indexes.CharField(model_attr='deployed_to__iso3', null=True)
    visibility = indexes.CharField(model_attr='event__get_visibility_display', null=True)

    def get_model(self):
        return ERU

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class PersonnelIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name', null=True)
    start_date = indexes.DateTimeField(model_attr='start_date', null=True)
    end_date = indexes.DateTimeField(model_attr='end_date', null=True)
    position = indexes.CharField(model_attr='role', null=True)
    type = indexes.CharField(model_attr='get_type_display', null=True)
    deploying_country_name = indexes.CharField(model_attr='country_from__society_name', null=True)
    deploying_country_id = indexes.IntegerField(model_attr='country_from__id', null=True)
    deployed_to_country_name = indexes.CharField(model_attr='country_to__name', null=True)
    deployed_to_country_id = indexes.IntegerField(model_attr='country_to__id', null=True)
    event_name = indexes.EdgeNgramField(model_attr='deployment__event_deployed_to__name')
    event_id = indexes.IntegerField(model_attr='deployment__event_deployed_to__id', null=True)
    visibility = indexes.CharField(model_attr='deployment__event_deployed_to__get_visibility_display', null=True)

    def get_model(self):
        return Personnel

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
