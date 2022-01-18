from modeltranslation.translator import register, TranslationOptions
from .models import (
    SurgeAlert,
)


@register(SurgeAlert)
class SurgeAlertTO(TranslationOptions):
    fields = ('operation', 'message')
