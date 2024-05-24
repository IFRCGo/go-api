from modeltranslation.translator import register, TranslationOptions
from .models import (
    FormArea,
    FormComponent,
    FormAnswer,
    FormQuestion,
    FormData,
    AssessmentType,
    FormQuestionGroup,
    Overview,
    FormComponentResponse,
    FormComponentQuestionAndAnswer,
    PerAssessment,
    AreaResponse,
    FormPrioritizationComponent,
    PerWorkPlanComponent,
    CustomPerWorkPlanComponent,
    PerComponentRating,
)


@register(FormArea)
class FormAreaTO(TranslationOptions):
    fields = ("title",)


@register(FormComponent)
class FormComponentTO(TranslationOptions):
    fields = ("title", "description")


@register(FormAnswer)
class FormAnswerTO(TranslationOptions):
    fields = ("text",)


@register(FormQuestion)
class FormQuestionTO(TranslationOptions):
    fields = ("question", "description")


@register(FormData)
class FormDataTO(TranslationOptions):
    fields = ("notes",)


@register(AssessmentType)
class AssessmentTypeTO(TranslationOptions):
    fields = ("name",)


@register(FormQuestionGroup)
class FormQuestionGroup(TranslationOptions):
    fields = ("title", "description")


@register(Overview)
class OverviewTO(TranslationOptions):
    pass


@register(FormComponentResponse)
class FormComponentResponseTO(TranslationOptions):
    fields = (
        'urban_considerations',
        'epi_considerations',
        'climate_environmental_considerations',
        'notes'
    )


@register(PerComponentRating)
class PerComponentRatingTO(TranslationOptions):
    fields = ("title",)


@register(FormComponentQuestionAndAnswer)
class FormComponentQuestionAndAnswerTO(TranslationOptions):
    fields = (
        'notes',
    )


@register(PerAssessment)
class PerAssessmentTO(TranslationOptions):
    pass


@register(AreaResponse)
class AreaResponseTO(TranslationOptions):
    pass


@register(FormPrioritizationComponent)
class FormPrioritizationComponentTO(TranslationOptions):
    fields = (
        'justification_text',
    )


@register(PerWorkPlanComponent)
class PerWorkPlanComponentTo(TranslationOptions):
    fields = (
        'actions',
    )


@register(CustomPerWorkPlanComponent)
class CustomPerWorkPlanComponentTO(TranslationOptions):
    fields = (
        'actions',
    )
