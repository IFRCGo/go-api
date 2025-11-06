import logging
import typing
from functools import reduce

from celery import shared_task
from django.apps import apps as django_apps
from django.conf import settings
from django.db import models
from django.db.models import Q, Sum
from django.db.models.functions import Length
from modeltranslation import settings as mt_settings
from modeltranslation.translator import translator
from modeltranslation.utils import build_localized_fieldname

from main.celery import Queues
from main.lock import RedisLockKey, redis_lock
from main.translation import (
    TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME,
    TRANSLATOR_SKIP_FIELD_NAME,
    skip_auto_translation,
)

from .translation import AVAILABLE_LANGUAGES, get_translator_class

logger = logging.getLogger(__name__)


class ModelTranslator:
    def __init__(self):
        self.default_translator = get_translator_class()()

    @property
    def translator(self):
        return self.default_translator

    def translate_fields_object(self, obj, field):
        initial_lang = getattr(obj, TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME)
        initial_value = getattr(obj, build_localized_fieldname(field, initial_lang), None)
        if not initial_value or not initial_lang:
            return

        for lang in AVAILABLE_LANGUAGES:
            lang_field = build_localized_fieldname(field, lang)
            value = getattr(obj, lang_field, None)
            if value:
                continue

            model = type(obj)
            app_label = model._meta.app_label
            model_name = model._meta.model_name
            table_field = f"{app_label}:{model_name}:{field}"

            new_value = self.translator.translate_text(
                initial_value,
                lang,
                source_language=initial_lang,
                table_field=table_field,
            )

            field_max_length = model._meta.get_field(field).max_length
            if field_max_length and len(new_value) > field_max_length:
                logger.warning(f"Greater then max_length found for Model ({type(obj)}<{lang_field}>) pk: ({obj.pk})")
                new_value = new_value[:field_max_length]

            setattr(obj, lang_field, new_value)
            yield lang_field

    @staticmethod
    def _get_filter(translation_fields):
        def _get_not_empty_query(field, lang):
            return Q(**{f"{build_localized_fieldname(field, lang)}__isnull": True}) | Q(
                **{f"{build_localized_fieldname(field, lang)}__exact": ""}
            )

        # Generate filters to fetch only rows with missing translations
        return reduce(
            lambda acc, f: acc | f,
            [
                (
                    # All field shouldn't be empty
                    ~Q(reduce(lambda acc, f: acc & f, [_get_not_empty_query(field, lang) for lang in AVAILABLE_LANGUAGES]))
                    &
                    # One or more field should be empty
                    reduce(lambda acc, f: acc | f, [_get_not_empty_query(field, lang) for lang in AVAILABLE_LANGUAGES])
                )
                for field in translation_fields
            ],
        )

    @classmethod
    def get_translatable_models(cls, only_models: typing.Optional[typing.List[models.Model]] = None):
        # return all models excluding proxy- and not managed models
        all_translatable_models = [
            m for m in translator.get_registered_models(abstract=False) if not m._meta.proxy and m._meta.managed
        ]
        if only_models:
            translatable_models = list(set(only_models).intersection(set(all_translatable_models)))
            assert len(only_models) == len(
                translatable_models
            ), f"Translation is not set for this models: {set(only_models).difference(set(translatable_models))}"
            return translatable_models
        return all_translatable_models

    @classmethod
    def get_translatable_fields(cls, model):
        translation_options = translator.get_options_for_model(model)
        # NOTE: Some skipped fields are handled manually.
        skipped_fields = set(getattr(translation_options, "skip_fields", []))
        return [field for field in translation_options.fields.keys() if field not in skipped_fields]

    def translate_model_fields(self, obj, translatable_fields=None):
        if skip_auto_translation(obj):
            return
        translatable_fields = translatable_fields or self.get_translatable_fields(type(obj))
        update_fields = []
        for field in translatable_fields:
            update_fields.extend(list(self.translate_fields_object(obj, field)))
        obj.save(update_fields=update_fields)

    @classmethod
    def show_characters_counts(cls, only_models: typing.Optional[typing.List[models.Model]] = None):
        """
        Retrive and search for fields to be translated and show total character count
        """
        translatable_models = cls.get_translatable_models(only_models=only_models)
        logger.info(f"Languages: {AVAILABLE_LANGUAGES}")
        logger.info(f"Default language: {mt_settings.DEFAULT_LANGUAGE}")
        logger.info(f"Number of models: {len(translatable_models)}")

        total_count = 0
        for model in translatable_models:
            logger.info(f"Processing for Model: {model._meta.verbose_name.title()}")

            translatable_fields = cls.get_translatable_fields(model)
            if not translatable_fields:
                continue

            qs = model.objects.filter(cls._get_filter(translatable_fields))
            logger.info(f"\tFields: {translatable_fields}")
            logger.info("\tTotal characters:")

            for field in translatable_fields:
                count = (
                    qs.annotate(text_length=Length(field)).aggregate(total_text_length=Sum("text_length"))["total_text_length"]
                    or 0
                )
                total_count += count
                logger.info(f"\t\t {field} - {count}")
        logger.info(f"Total Count: {total_count}")
        logger.info(f"Estimated Cost (AWS): {(len(AVAILABLE_LANGUAGES) - 1) * total_count * 0.000015}")

    def run(self, batch_size=None, only_models: typing.Optional[typing.List[models.Model]] = None):
        """
        Retrive and search for fields to be translated
        batch_size: how many instances to translate for each model. None will be all
        """
        translatable_models = self.get_translatable_models(only_models=only_models)
        logger.info(f"Languages: {AVAILABLE_LANGUAGES}")
        logger.info(f"Default language: {mt_settings.DEFAULT_LANGUAGE}")
        logger.info(f"Number of models: {len(translatable_models)}")

        for model in translatable_models:
            logger.info(f"Processing for Model: {model._meta.verbose_name.title()}")

            translatable_fields = self.get_translatable_fields(model)
            if not translatable_fields:
                continue

            # Process recent entities first
            qs = model.objects.filter(
                self._get_filter(translatable_fields),
                # Skip which are flagged by user
                **{TRANSLATOR_SKIP_FIELD_NAME: False},
            ).order_by("-id")
            qs_count = qs.count()
            index = 1
            logger.info(f"\tFields: {translatable_fields}")
            logger.info(f"\tTotal instances: {qs_count}")

            if batch_size is not None:
                logger.info(f"\tProcessing instances: {min(qs_count, batch_size)}")
                qs = qs.all()[:batch_size]
            else:
                qs = qs.all()

            for obj in qs.iterator():
                # Skip if it is flagged as skip by user # TODO: Remove this later
                assert skip_auto_translation(obj) is False
                logger.info(f"\t\t ({index}/{qs_count}) - {obj}")
                self.translate_model_fields(obj, translatable_fields)
                index += 1


@shared_task(queue=Queues.CRONJOB)
def translate_remaining_models_fields():
    # Disabled in DEBUG/Development
    if settings.DEBUG:
        logger.warning("DEGUB is enabled.. Skipping translate_remaining_models_fields")
        return
    ModelTranslator().run(batch_size=100)


@shared_task(queue=Queues.DEFAULT)
def translate_model_fields(model_name, pk):
    model = django_apps.get_model(model_name)
    obj = model.objects.get(pk=pk)

    with redis_lock(key=RedisLockKey.MODEL_TRANSLATION, id=pk, model_name=model_name) as acquired:
        if not acquired:
            logger.warning(f"Translation is already in progress for {model_name} with pk={pk}.")
            return
        ModelTranslator().translate_model_fields(obj)
        logger.info(f"Translation success for {model_name} with pk={pk}.")


@shared_task(queue=Queues.HEAVY)
def translate_model_fields_in_bulk(model_name, pks):
    model = django_apps.get_model(model_name)
    qs = model.objects.filter(
        pk__in=pks,
        **{TRANSLATOR_SKIP_FIELD_NAME: False},
    )
    for obj in qs:
        ModelTranslator().translate_model_fields(obj)
