from modeltranslation.translator import register, TranslationOptions

from dref.models import Dref


@register(Dref)
class DrefTO(TranslationOptions):
    fields = ("title",)
