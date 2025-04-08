import datetime

import factory
import pytz
from factory import fuzzy

from api.factories.country import CountryFactory
from api.factories.event import AppealFactory, EventFactory
from deployments.models import (
    ERU,
    EmergencyProject,
    EmergencyProjectActivity,
    EmergencyProjectActivityAction,
    EmergencyProjectActivitySector,
    ERUOwner,
    ERUReadiness,
    ERUReadinessType,
    ERUType,
)


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

    title = fuzzy.FuzzyText(length=50, prefix="title-")


class EmergencyProjectActivityActionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmergencyProjectActivityAction

    sector = factory.SubFactory(EmergencyProjectActivitySectorFactory)
    title = fuzzy.FuzzyText(length=50, prefix="title-")


class EmergencyProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmergencyProject

    title = fuzzy.FuzzyText(length=50, prefix="emergency-project-")
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


class ERUReadinessFactory(factory.django.DjangoModelFactory):
    eru_owner = factory.SubFactory(ERUOwnerFactory)

    class Meta:
        model = ERUReadiness

    @factory.post_generation
    def eru_types(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for eru_type in extracted:
                self.eru_types.add(eru_type)


class ERUReadinessTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ERUReadinessType

    type = fuzzy.FuzzyChoice(ERUType)
    equipment = fuzzy.FuzzyChoice(ERUReadinessType.ReadinessStatus)
    people = fuzzy.FuzzyChoice(ERUReadinessType.ReadinessStatus)
    funding = fuzzy.FuzzyChoice(ERUReadinessType.ReadinessStatus)
    comment = fuzzy.FuzzyText(length=10, prefix="comment-")
