from modeltranslation.translator import TranslationOptions, register

from .models import FlashUpdate


@register(FlashUpdate)
class FlashUpdateTO(TranslationOptions):
    fields = (
        "title",
        "situational_overview",
    )
