import factory
from factory import fuzzy

from api.factories.country import CountryFactory
from dref.models import (
    Dref,
    PlannedIntervention,
    IdentifiedNeed,
    NationalSocietyAction,
    DrefFile,
    DrefOperationalUpdate,
    PlannedInterventionIndicators
)


class DrefFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Dref

    title = fuzzy.FuzzyText(length=50, prefix='title-')
    type_of_onset = fuzzy.FuzzyChoice(Dref.OnsetType)
    disaster_category = fuzzy.FuzzyChoice(Dref.DisasterCategory)
    status = fuzzy.FuzzyChoice(Dref.Status)
    national_society = factory.SubFactory(CountryFactory)

    @factory.post_generation
    def planned_interventions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for planned_intervention in extracted:
                self.planned_interventions.add(planned_intervention)

    @factory.post_generation
    def needs_identified(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for need_identified in extracted:
                self.needs_identified.add(need_identified)

    @factory.post_generation
    def national_society_actions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for national_society_action in extracted:
                self.national_society_actions.add(national_society_action)

    @factory.post_generation
    def users(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.users.add(user)


class DrefFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DrefFile


class PlannedInterventionIndicatorsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlannedInterventionIndicators
    title = fuzzy.FuzzyText(length=50, prefix='title-')


class PlannedInterventionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlannedIntervention

    title = fuzzy.FuzzyChoice(PlannedIntervention.Title)

    @factory.post_generation
    def indicators(self, extracted, create, **kwargs):
        if not create:
            return

        if extracted:
            for indicator in extracted:
                self.indicators.add(indicator)


class IdentifiedNeedFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IdentifiedNeed

    title = fuzzy.FuzzyChoice(IdentifiedNeed.Title)


class NationalSocietyActionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NationalSocietyAction

    title = fuzzy.FuzzyChoice(NationalSocietyAction.Title)


class DrefOperationalUpdateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DrefOperationalUpdate
    title = fuzzy.FuzzyText(length=50, prefix='title-')
    type_of_onset = fuzzy.FuzzyChoice(Dref.OnsetType)
    disaster_category = fuzzy.FuzzyChoice(Dref.DisasterCategory)
    national_society = factory.SubFactory(CountryFactory)

    @factory.post_generation
    def planned_interventions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for planned_intervention in extracted:
                self.planned_interventions.add(planned_intervention)

    @factory.post_generation
    def needs_identified(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for need_identified in extracted:
                self.needs_identified.add(need_identified)

    @factory.post_generation
    def national_society_actions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for national_society_action in extracted:
                self.national_society_actions.add(national_society_action)
