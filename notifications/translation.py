from modeltranslation.translator import TranslationOptions, register

from .models import SurgeAlert


@register(SurgeAlert)
class SurgeAlertTO(TranslationOptions):
    fields = ("operation", "message")
