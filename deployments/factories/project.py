import factory
from factory import fuzzy
import datetime
import pytz
from random import randrange

from .. import models
from . import user, regional_project
from api.factories import country, event, disaster_type

class ProjectFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Project

    modified_at = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    user = factory.SubFactory(user.UserFactory)
    reporting_ns = factory.SubFactory(country.CountryFactory)
    project_country = factory.SubFactory(country.CountryFactory)

    @factory.post_generation
    def project_districts(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for project_district in extracted:
                self.project_districts.add(project_district)

    event = factory.SubFactory(event.EventFactory)
    dtype = factory.SubFactory(disaster_type.DisasterTypeFactory)
    name = fuzzy.FuzzyText(length=500)
    programme_type = fuzzy.FuzzyChoice(models.ProgrammeTypes)
    primary_sector = fuzzy.FuzzyChoice(models.Sectors)
    secondary_sectors = factory.List([
        fuzzy.FuzzyChoice(models.SectorTags) for _ in range(randrange(5))
    ])
    operation_type = fuzzy.FuzzyChoice(models.OperationTypes)
    start_date = factory.LazyFunction(datetime.date.today)
    end_date = factory.LazyFunction(datetime.date.today)
    budget_amount = fuzzy.FuzzyInteger(0)
    actual_expenditure = fuzzy.FuzzyInteger(0)
    status = fuzzy.FuzzyChoice(models.Statuses)

    # Target Metric
    target_male = fuzzy.FuzzyInteger(0)
    target_female = fuzzy.FuzzyInteger(0)
    target_other = fuzzy.FuzzyInteger(0)
    target_total = fuzzy.FuzzyInteger(0)

    # Reached Metric
    reached_male = fuzzy.FuzzyInteger(0)
    reached_female = fuzzy.FuzzyInteger(0)
    reached_other = fuzzy.FuzzyInteger(0)
    reached_total = fuzzy.FuzzyInteger(0)

    regional_project = factory.SubFactory(regional_project.RegionalProjectFactory)
    visibility = fuzzy.FuzzyChoice(models.VisibilityCharChoices.CHOICES)
