from modeltranslation.translator import TranslationOptions, register

from .models import (
    AreaResponse,
    AssessmentType,
    CustomPerWorkPlanComponent,
    FormAnswer,
    FormArea,
    FormComponent,
    FormComponentQuestionAndAnswer,
    FormComponentResponse,
    FormData,
    FormPrioritizationComponent,
    FormQuestion,
    FormQuestionGroup,
    OpsLearning,
    OpsLearningCacheResponse,
    OpsLearningComponentCacheResponse,
    OpsLearningSectorCacheResponse,
    Overview,
    PerAssessment,
    PerComponentRating,
    PerWorkPlanComponent,
)


@register(FormArea)
class FormAreaTO(TranslationOptions):
    fields = ("title",)


@register(FormComponent)
class FormComponentTO(TranslationOptions):
    fields = (
        "title",
        "description",
        "urban_considerations_guidance",
        "epi_considerations_guidance",
        "climate_environmental_considerations_guidance",
    )


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
    fields = ("urban_considerations", "epi_considerations", "climate_environmental_considerations", "notes")


@register(PerComponentRating)
class PerComponentRatingTO(TranslationOptions):
    fields = ("title",)


@register(FormComponentQuestionAndAnswer)
class FormComponentQuestionAndAnswerTO(TranslationOptions):
    fields = ("notes",)


@register(PerAssessment)
class PerAssessmentTO(TranslationOptions):
    pass


@register(AreaResponse)
class AreaResponseTO(TranslationOptions):
    pass


@register(FormPrioritizationComponent)
class FormPrioritizationComponentTO(TranslationOptions):
    fields = ("justification_text",)


@register(PerWorkPlanComponent)
class PerWorkPlanComponentTo(TranslationOptions):
    fields = ("actions",)


@register(CustomPerWorkPlanComponent)
class CustomPerWorkPlanComponentTO(TranslationOptions):
    fields = ("actions",)


@register(OpsLearning)
class OpsLearningTO(TranslationOptions):
    fields = (
        "learning",
        "learning_validated",
    )


@register(OpsLearningCacheResponse)
class OpsLearningCacheResponseTO(TranslationOptions):
    fields = (
        "insights1_title",
        "insights2_title",
        "insights3_title",
        "insights1_content",
        "insights2_content",
        "insights3_content",
    )


@register(OpsLearningSectorCacheResponse)
class OpsLearningSectorCacheResponseTO(TranslationOptions):
    fields = ("content",)


@register(OpsLearningComponentCacheResponse)
class OpsLearningComponentCacheResponseTO(TranslationOptions):
    fields = ("content",)
