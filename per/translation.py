from modeltranslation.translator import register, TranslationOptions
from .models import FormArea, FormComponent, FormAnswer, FormQuestion, FormData, AssessmentType


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
