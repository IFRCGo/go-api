import factory
from factory import fuzzy
import datetime
import pytz

from deployments.models import (
    EmergencyProject,
    EmergencyProjectActivity,
    ERU,
    ERUOwner,
    EmergencyProjectActivitySector,
    EmergencyProjectActivityAction
)
from api.factories.event import EventFactory, AppealFactory
from api.factories.country import CountryFactory


class ERUOwnerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ERUOwner
    national_society_country = factory.SubFactory(CountryFactory)


class EruFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ERU
    deployed_to = factory.SubFactory(CountryFactory)
    event = factory.SubFactory(EventFactory)
    eru_owner = factory.SubFactory(ERUOwnerFactory)
    appeal = factory.SubFactory(AppealFactory)


class EmergencyProjectActivitySectorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmergencyProjectActivitySector
    title = fuzzy.FuzzyText(length=50, prefix='title-')


class EmergencyProjectActivityActionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmergencyProjectActivityAction
    sector = factory.SubFactory(EmergencyProjectActivitySectorFactory)
    title = title = fuzzy.FuzzyText(length=50, prefix='title-')


class EmergencyProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmergencyProject

    title = fuzzy.FuzzyText(length=50, prefix='emergency-project-')
    event = factory.SubFactory(EventFactory)
    reporting_ns = factory.SubFactory(CountryFactory)
    deployed_eru = factory.SubFactory(EruFactory)
    status = fuzzy.FuzzyChoice(EmergencyProject.ActivityStatus)
    start_date = fuzzy.FuzzyDate(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc).date())
    country = factory.SubFactory(CountryFactory)

    @factory.post_generation
    def districts(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for district in extracted:
                self.districts.add(district)


class EmergencyProjectActivityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmergencyProjectActivity
    sector = factory.SubFactory(EmergencyProjectActivitySectorFactory)
    action = factory.SubFactory(EmergencyProjectActivityActionFactory)
    project = factory.SubFactory(EmergencyProjectFactory)

    @factory.post_generation
    def points(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for point in extracted:
                self.points.add(point)
