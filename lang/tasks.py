import logging
from celery import shared_task
from modeltranslation.translator import translator
from modeltranslation.utils import build_localized_fieldname
from django.apps import apps as django_apps
from django.db.models import Q
from django.conf import settings
from functools import reduce

from main.celery import Queues
from .translation import (
    AmazonTranslate,
    AVAILABLE_LANGUAGES,
    DEFAULT_LANGUAGE,
)


logger = logging.getLogger(__name__)


class ModelTranslator():
    def __init__(self):
        # TODO: Handle error if access credentials are not provided or are invalid
        self.aws_translator = AmazonTranslate()

    @property
    def translator(self):
        return self.aws_translator

    def translate_fields_object(self, obj, field):
        initial_value = None
        initial_lang = None
        for lang in AVAILABLE_LANGUAGES:
            initial_value = getattr(obj, build_localized_fieldname(field, lang), None)
            initial_lang = lang
            if initial_value:
                break
        if not initial_value or not initial_lang:
            return

        for lang in AVAILABLE_LANGUAGES:
            lang_field = build_localized_fieldname(field, lang)
            value = getattr(obj, lang_field, None)
            if value:
                continue

            new_value = self.translator.translate_text(
                initial_value,
                lang,
                source_language=initial_lang,
            )

            setattr(obj, lang_field, new_value)
            yield lang_field

    def _get_filter(self, translation_fields):
        def _get_not_empty_query(field, lang):
            return (
                Q(**{f"{build_localized_fieldname(field, lang)}__isnull": True}) |
                Q(**{f"{build_localized_fieldname(field, lang)}__exact": ""})
            )
        # Generate filters to fetch only rows with missing translations
        return reduce(
            lambda acc, f: acc | f,
            [
                (
                    # All field shouldn't be empty
                    ~Q(reduce(
                        lambda acc, f: acc & f,
                        [_get_not_empty_query(field, lang) for lang in AVAILABLE_LANGUAGES]
                    )) &
                    # One or more field should be empty
                    reduce(
                        lambda acc, f: acc | f,
                        [_get_not_empty_query(field, lang) for lang in AVAILABLE_LANGUAGES]
                    )
                )
                for field in translation_fields
            ]
        )

    @classmethod
    def get_translatable_models(cls):
        # return all models excluding proxy- and not managed models
        return [
            m for m in translator.get_registered_models(abstract=False)
            if not m._meta.proxy and m._meta.managed
        ]

    @classmethod
    def get_translatable_fields(cls, model):
        return list(translator.get_options_for_model(model).fields.keys())

    def translate_model_fields(self, obj, translatable_fields=None):
        translatable_fields = translatable_fields or self.get_translatable_fields(type(obj))
        update_fields = []
        for field in translatable_fields:
            update_fields.extend(
                list(self.translate_fields_object(obj, field))
            )
        obj.save(update_fields=update_fields)

    def run(self, batch_size):
        """
        Retrive and search for fields to be translated
        batch_size: how many instances to translate for each model. None will be all
        """
        translatable_models = self.get_translatable_models()
        logger.info(f'Languages: {AVAILABLE_LANGUAGES}')
        logger.info(f'Default language: {DEFAULT_LANGUAGE}')
        logger.info(f'Number of models: {len(translatable_models)}')

        for model in translatable_models:
            logger.info(f'Processing for Model: {model._meta.verbose_name.title()}')

            translatable_fields = self.get_translatable_fields(model)
            if not translatable_fields:
                continue

            qs = model.objects.filter(self._get_filter(translatable_fields))
            qs_count = qs.count()
            index = 1
            logger.info(f'\tFields: {translatable_fields}')
            logger.info(f'\tTotal instances: {qs_count}')

            qs = qs.all()[:batch_size]

            for obj in qs.iterator():
                logger.info(f'\t\t ({index}/{qs_count}) - {obj}')
                self.translate_model_fields(obj, translatable_fields)
                index += 1


@shared_task(queue=Queues.CRONJOB)
def translate_remaining_models_fields():
    # Disabled in DEBUG/Development
    if settings.DEBUG:
        logger.warning('DEGUB is enabled.. Skipping translate_remaining_models_fields')
        return
    ModelTranslator().run(batch_size=100)


@shared_task(queue=Queues.DEFAULT)
def translate_model_fields(model_name, pk):
    model = django_apps.get_model(model_name)
    obj = model.objects.get(pk=pk)
    ModelTranslator().translate_model_fields(obj)


@shared_task(queue=Queues.HEAVY)
def translate_model_fields_in_bulk(model_name, pks):
    model = django_apps.get_model(model_name)
    for obj in model.objects.filter(pk__in=pks):
        ModelTranslator().translate_model_fields(obj)
