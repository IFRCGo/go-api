from django.conf import settings
from django.db import models
from django.db.models.base import ModelBase
from django.utils.translation import gettext_lazy as _
from modeltranslation.translator import Translator

original_translator_register = Translator.register


TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME = "translation_module_original_language"
TRANSLATOR_SKIP_FIELD_NAME = "translation_module_skip_auto_translation"


def custom_translation_register(self, model_or_iterable, opts_class=None, **options):
    original_translator_register(self, model_or_iterable, opts_class=opts_class, **options)
    if not isinstance(model_or_iterable, ModelBase):
        _models = model_or_iterable
    else:
        _models = [model_or_iterable]
    for model in _models:
        if any(
            [(hasattr(_class, "_meta") and _class.__dict__.get(TRANSLATOR_SKIP_FIELD_NAME, None)) for _class in model.__mro__]
        ):
            # Skip if the field is already attached to that model
            continue

        original_language_field = models.CharField(
            max_length=2,
            default="en",
            choices=settings.LANGUAGES,
            verbose_name=_("Entity Original language"),
            help_text=_("Language used to create this entity"),
        )
        skip_auto_translation_field = models.BooleanField(
            verbose_name=_("Skip auto translation"),
            default=False,
            help_text=_("Skip auto translation operation for this entity?"),
        )
        model.add_to_class(TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME, original_language_field)
        model.add_to_class(TRANSLATOR_SKIP_FIELD_NAME, skip_auto_translation_field)


def skip_auto_translation(instance):
    return getattr(instance, TRANSLATOR_SKIP_FIELD_NAME)


Translator.register = custom_translation_register
