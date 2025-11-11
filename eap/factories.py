from random import random

import factory
from factory import fuzzy

from eap.models import (
    EAPRegistration,
    EAPStatus,
    EAPType,
    EnableApproach,
    OperationActivity,
    PlannedOperation,
    SimplifiedEAP,
)


class EAPRegistrationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EAPRegistration

    status = fuzzy.FuzzyChoice(EAPStatus)
    eap_type = fuzzy.FuzzyChoice(EAPType)

    @factory.post_generation
    def partners(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for partner in extracted:
                self.partners.add(partner)


class SimplifiedEAPFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SimplifiedEAP

    seap_timeframe = fuzzy.FuzzyInteger(2)
    total_budget = fuzzy.FuzzyInteger(1000, 1000000)
    readiness_budget = fuzzy.FuzzyInteger(1000, 1000000)
    pre_positioning_budget = fuzzy.FuzzyInteger(1000, 1000000)
    early_action_budget = fuzzy.FuzzyInteger(1000, 1000000)

    @factory.post_generation
    def enable_approaches(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for approach in extracted:
                self.enable_approaches.add(approach)

    @factory.post_generation
    def planned_operations(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for operation in extracted:
                self.planned_operations.add(operation)


class OperationActivityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OperationActivity

    activity = fuzzy.FuzzyText(length=50, prefix="Activity-")
    timeframe = fuzzy.FuzzyChoice(OperationActivity.TimeFrame)
    time_value = factory.LazyFunction(lambda: [random.randint(1, 12) for _ in range(3)])


class EnableApproachFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EnableApproach

    approach = fuzzy.FuzzyChoice(EnableApproach.Approach)
    budget_per_approach = fuzzy.FuzzyInteger(1000, 1000000)
    ap_code = fuzzy.FuzzyInteger(100, 999)
    indicator_target = fuzzy.FuzzyInteger(10, 1000)

    @factory.post_generation
    def readiness_activities(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for activity in extracted:
                self.readiness_activities.add(activity)

    @factory.post_generation
    def prepositioning_activities(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for activity in extracted:
                self.prepositioning_activities.add(activity)

    @factory.post_generation
    def early_action_activities(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for activity in extracted:
                self.early_action_activities.add(activity)


class PlannedOperationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlannedOperation

    sector = fuzzy.FuzzyChoice(PlannedOperation.Sector)
    people_targeted = fuzzy.FuzzyInteger(100, 100000)
    budget_per_sector = fuzzy.FuzzyInteger(1000, 1000000)
    ap_code = fuzzy.FuzzyInteger(100, 999)

    @factory.post_generation
    def readiness_activities(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for activity in extracted:
                self.readiness_activities.add(activity)

    @factory.post_generation
    def prepositioning_activities(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for activity in extracted:
                self.prepositioning_activities.add(activity)

    @factory.post_generation
    def early_action_activities(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for activity in extracted:
                self.early_action_activities.add(activity)
