from modeltranslation.translator import register, TranslationOptions

from .models import InformalUpdate


@register(InformalUpdate)
class InformalUpdateTO(TranslationOptions):
    fields = ('title', 'situational_overview',)
