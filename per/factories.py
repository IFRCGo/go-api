import factory
import datetime

from per.models import (
    Overview,
    PerWorkPlan,
    PerWorkPlanComponent,
    FormArea,
    FormComponent,
)


class OverviewFactory(factory.django.DjangoModelFactory):
    date_of_assessment = factory.fuzzy.FuzzyNaiveDateTime(datetime.datetime(2023, 1, 1))

    class Meta:
        model = Overview


class PerWorkPlanComponentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PerWorkPlanComponent


class PerWorkPlanFactory(factory.django.DjangoModelFactory):
    overview = factory.SubFactory(OverviewFactory)

    class Meta:
        model = PerWorkPlan

    @factory.post_generation
    def workplan_component(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for workplan in extracted:
                self.workplan_component.add(workplan)


class FormAreaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FormArea


class FormComponentFactory(factory.django.DjangoModelFactory):
    area = factory.SubFactory(FormAreaFactory)

    class Meta:
        model = FormComponent
