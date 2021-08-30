import factory
from factory import fuzzy

from dref.models import (
    Dref,
    PlannedIntervention,
    IdentifiedNeed,
    NationalSocietyAction,
    DrefFile
)


class DrefFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Dref

    title = fuzzy.FuzzyText(length=50, prefix='title-')
    type_of_onset = fuzzy.FuzzyChoice(Dref.OnsetType)
    disaster_category = fuzzy.FuzzyChoice(Dref.DisasterCategory)
    status = fuzzy.FuzzyChoice(Dref.Status)

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


class DrefFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DrefFile


class PlannedInterventionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlannedIntervention

    title = fuzzy.FuzzyChoice(PlannedIntervention.Title)


class IdentifiedNeedFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IdentifiedNeed

    title = fuzzy.FuzzyChoice(IdentifiedNeed.Title)


class NationalSocietyActionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NationalSocietyAction

    title = fuzzy.FuzzyChoice(NationalSocietyAction.Title)
