import datetime

import factory
import pytz
from factory import fuzzy

from api.factories import country, disaster_type, event

from .. import models
from . import regional_project, user


class SectorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Sector

    title = fuzzy.FuzzyText(length=50, prefix="sect-")
    order = fuzzy.FuzzyInteger(0, 19)


class SectorTagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SectorTag

    title = fuzzy.FuzzyText(length=50, prefix="sect-tag-")
    order = fuzzy.FuzzyInteger(0, 19)


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Project

    modified_at = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    user = factory.SubFactory(user.UserFactory)
    reporting_ns = factory.SubFactory(country.CountryFactory)
    project_country = factory.SubFactory(country.CountryFactory)
    # primary_sector = factory.SubFactory(SectorFactory)  # it remains a stub. An id without target. Could you FIXME?

    @factory.post_generation
    def project_districts(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for project_district in extracted:
                self.project_districts.add(project_district)

    event = factory.SubFactory(event.EventFactory)
    dtype = factory.SubFactory(disaster_type.DisasterTypeFactory)
    name = fuzzy.FuzzyText(length=50, prefix="project-")
    programme_type = fuzzy.FuzzyChoice(models.ProgrammeTypes)

    @factory.post_generation
    def secondary_sectors(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for secondary_sector in extracted:
                self.secondary_sectors.add(secondary_sector)

    operation_type = fuzzy.FuzzyChoice(models.OperationTypes)
    start_date = factory.LazyFunction(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc).date)
    end_date = factory.LazyFunction(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc).date)
    budget_amount = fuzzy.FuzzyInteger(0, 10000000, step=10000)
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
    visibility = fuzzy.FuzzyChoice(models.VisibilityCharChoices.choices)
