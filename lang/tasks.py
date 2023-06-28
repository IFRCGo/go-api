import logging
# from celery import shared_task
from modeltranslation.translator import translator
from modeltranslation.utils import build_localized_fieldname
from modeltranslation import settings as mt_settings
from django.apps import apps as django_apps
from django.db.models.functions import Length
from django.db.models import Sum
from django.db.models import Q
from django.conf import settings
from functools import reduce

from main.translation import TRANSLATOR_SKIP_FIELD_NAME
# from main.celery import Queues
from .translation import (
    AmazonTranslate,
    AVAILABLE_LANGUAGES,
)


logger = logging.getLogger(__name__)


class ModelTranslator():
    def __init__(self):
        self.aws_translator = AmazonTranslate()

    @property
    def translator(self):
        return self.aws_translator

    def translate_fields_object(self, obj, field):
        initial_value = ''
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

            field_max_length = type(obj)._meta.get_field(field).max_length
            if field_max_length and len(new_value) > field_max_length:
                logger.warning(f'Greater then max_length found for Model ({type(obj)}<{lang_field}>) pk: ({obj.pk})')
                new_value = new_value[:field_max_length]

            setattr(obj, lang_field, new_value)
            yield lang_field

    @classmethod
    def _get_filter(cls, translation_fields):
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
        if getattr(obj, TRANSLATOR_SKIP_FIELD_NAME):
            return
        translatable_fields = translatable_fields or self.get_translatable_fields(type(obj))
        update_fields = []
        for field in translatable_fields:
            update_fields.extend(
                list(self.translate_fields_object(obj, field))
            )
        obj.save(update_fields=update_fields)

    @classmethod
    def show_characters_counts(cls):
        """
        Retrive and search for fields to be translated and show total character count
        """
        translatable_models = cls.get_translatable_models()
        logger.info(f'Languages: {AVAILABLE_LANGUAGES}')
        logger.info(f'Default language: {mt_settings.DEFAULT_LANGUAGE}')
        logger.info(f'Number of models: {len(translatable_models)}')

        total_count = 0
        for model in translatable_models:
            logger.info(f'Processing for Model: {model._meta.verbose_name.title()}')

            translatable_fields = cls.get_translatable_fields(model)
            if not translatable_fields:
                continue

            qs = model.objects.filter(cls._get_filter(translatable_fields))
            logger.info(f'\tFields: {translatable_fields}')
            logger.info('\tTotal characters:')

            for field in translatable_fields:
                count = qs.annotate(text_length=Length(field))\
                    .aggregate(total_text_length=Sum('text_length'))['total_text_length'] or 0
                total_count += count
                logger.info(f'\t\t {field} - {count}')
        logger.info(f'Total Count: {total_count}')
        logger.info(f'Estimated Cost: {(len(AVAILABLE_LANGUAGES) -1) * total_count * 0.000015}')

    def run(self, batch_size=None):
        """
        Retrive and search for fields to be translated
        batch_size: how many instances to translate for each model. None will be all
        """
        translatable_models = self.get_translatable_models()
        logger.info(f'Languages: {AVAILABLE_LANGUAGES}')
        logger.info(f'Default language: {mt_settings.DEFAULT_LANGUAGE}')
        logger.info(f'Number of models: {len(translatable_models)}')

        for model in translatable_models:
            logger.info(f'Processing for Model: {model._meta.verbose_name.title()}')

            translatable_fields = self.get_translatable_fields(model)
            if not translatable_fields:
                continue

            # Process recent entities first
            qs = model.objects.filter(
                self._get_filter(translatable_fields),
                # Skip which are flagged by user
                **{TRANSLATOR_SKIP_FIELD_NAME: False},
            ).order_by('-id')
            qs_count = qs.count()
            index = 1
            logger.info(f'\tFields: {translatable_fields}')
            logger.info(f'\tTotal instances: {qs_count}')

            if batch_size is not None:
                logger.info(f'\tProcessing instances: {min(qs_count, batch_size)}')
                qs = qs.all()[:batch_size]
            else:
                qs = qs.all()

            for obj in qs.iterator():
                # Skip if it is flagged as skip by user # TODO: Remove this later
                assert getattr(obj, TRANSLATOR_SKIP_FIELD_NAME) is False
                logger.info(f'\t\t ({index}/{qs_count}) - {obj}')
                self.translate_model_fields(obj, translatable_fields)
                index += 1


# @shared_task(queue=Queues.CRONJOB) NOTE: Not used right now.
def translate_remaining_models_fields():
    # Disabled in DEBUG/Development
    if settings.DEBUG:
        logger.warning('DEGUB is enabled.. Skipping translate_remaining_models_fields')
        return
    ModelTranslator().run(batch_size=100)


# @shared_task(queue=Queues.DEFAULT) NOTE: Not used right now.
def translate_model_fields(model_name, pk):
    model = django_apps.get_model(model_name)
    obj = model.objects.get(pk=pk)
    ModelTranslator().translate_model_fields(obj)


# @shared_task(queue=Queues.HEAVY) NOTE: Not used right now.
def translate_model_fields_in_bulk(model_name, pks):
    model = django_apps.get_model(model_name)
    qs = model.objects.filter(
        pk__in=pks,
        **{TRANSLATOR_SKIP_FIELD_NAME: False},
    )
    for obj in qs:
        ModelTranslator().translate_model_fields(obj)
