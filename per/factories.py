import factory
import datetime

from per.models import (
    Overview,
    PerWorkPlan,
    PerWorkPlanComponent,
    FormArea,
    FormComponent,
    AssessmentType,
    FormAnswer,
    FormQuestion,
    Form,
    FormData
)


class AssessmentTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AssessmentType


class OverviewFactory(factory.django.DjangoModelFactory):
    date_of_assessment = factory.fuzzy.FuzzyNaiveDateTime(datetime.datetime(2023, 1, 1))
    type_of_assessment = factory.SubFactory(AssessmentTypeFactory)

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


class FormAnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FormAnswer


class FormQuestionFactory(factory.django.DjangoModelFactory):
    component = factory.SubFactory(FormComponentFactory)

    class Meta:
        model = FormQuestion


class FormFactory(factory.django.DjangoModelFactory):
    overview = factory.SubFactory(OverviewFactory)

    class Meta:
        model = Form


class FormDataFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)
    question = factory.SubFactory(FormQuestionFactory)
    selected_answer = factory.SubFactory(FormAnswerFactory)

    class Meta:
        model = FormData
