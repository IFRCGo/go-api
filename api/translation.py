from modeltranslation.translator import register, TranslationOptions
from .models import FieldReport


# Field Report Translation Options
@register(FieldReport)
class FieldReportTO(TranslationOptions):
    fields = ('summary', 'description')
