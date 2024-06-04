import factory
from django.core.files.base import ContentFile
from factory import fuzzy

from api.factories.country import CountryFactory
from dref.models import (
    Dref,
    DrefFile,
    DrefFinalReport,
    DrefOperationalUpdate,
    IdentifiedNeed,
    NationalSocietyAction,
    PlannedIntervention,
    PlannedInterventionIndicators,
)


class DrefFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Dref

    title = fuzzy.FuzzyText(length=50, prefix="title-")
    type_of_onset = fuzzy.FuzzyChoice(Dref.OnsetType)
    type_of_dref = fuzzy.FuzzyChoice(Dref.DrefType)
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

    @factory.post_generation
    def images(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for image in extracted:
                self.images.add(image)


class DrefFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DrefFile

    file = factory.LazyAttribute(
        lambda _: ContentFile(factory.django.ImageField()._make_data({"width": 1024, "height": 768}), "dref.jpg")
    )


class PlannedInterventionIndicatorsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlannedInterventionIndicators

    title = fuzzy.FuzzyText(length=50, prefix="title-")


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

    title = fuzzy.FuzzyText(length=50, prefix="title-")
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


class DrefFinalReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DrefFinalReport

    title = fuzzy.FuzzyText(length=50, prefix="Final-Report-")
    type_of_onset = fuzzy.FuzzyChoice(Dref.OnsetType)
    disaster_category = fuzzy.FuzzyChoice(Dref.DisasterCategory)
    national_society = factory.SubFactory(CountryFactory)
    dref = factory.SubFactory(DrefFactory)

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
