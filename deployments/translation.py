from modeltranslation.translator import register, TranslationOptions
from .models import Project


# Project Options
@register(Project)
class ProjectTO(TranslationOptions):
    fields = ('name',)
