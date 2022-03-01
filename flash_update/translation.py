from modeltranslation.translator import register, TranslationOptions

from .models import FlashUpdate


@register(FlashUpdate)
class FlashUpdateTO(TranslationOptions):
    fields = ('title', 'situational_overview',)
