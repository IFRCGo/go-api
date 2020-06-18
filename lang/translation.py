import logging
import boto3

from modeltranslation.admin import TranslationBaseModelAdmin
from modeltranslation.utils import build_localized_fieldname
from modeltranslation import settings as mt_settings
from modeltranslation.manager import get_translatable_fields_for_model
from django.utils.translation import get_language as django_get_language

from rest_framework import serializers
from django.utils.translation import get_language
from django.conf import settings

logger = logging.getLogger(__name__)

# Array of language : ['en', 'es', 'fr', ....]
DJANGO_AVAILABLE_LANGUAGES = set([lang[0] for lang in settings.LANGUAGES])
AVAILABLE_LANGUAGES = mt_settings.AVAILABLE_LANGUAGES
DEFAULT_LANGUAGE = mt_settings.DEFAULT_LANGUAGE


class AmazonTranslate(object):
    def __init__(self, client=None):
        self.translate = client or boto3.client(
            'translate',
            aws_access_key_id=settings.AWS_TRANSLATE_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_TRANSLATE_SECRET_KEY,
            region_name=settings.AWS_TRANSLATE_REGION,
        )

    def translate_text(self, text, source_language, dest_language):
        return self.translate.translate_text(
            Text=text,
            SourceLanguageCode=source_language,
            TargetLanguageCode=dest_language
        )


# Overwrite TranslationBaseModelAdmin _exclude_original_fields to only show current language field in Admin panel
o__exclude_original_fields = TranslationBaseModelAdmin._exclude_original_fields
def _exclude_original_fields(self, exclude=None):  # noqa: E302
    current_lang = get_language()
    exclude = o__exclude_original_fields(self, exclude)
    # Exclude other languages
    return exclude + tuple([
        build_localized_fieldname(field, lang)
        for field in self.trans_opts.fields.keys()
        for lang in AVAILABLE_LANGUAGES
        if lang != current_lang
    ])


TranslationBaseModelAdmin._exclude_original_fields = _exclude_original_fields


class TranslatedModelSerializerMixin(serializers.ModelSerializer):
    def get_field_names(self, declared_fields, info):
        fields = super().get_field_names(declared_fields, info)

        requested_langs = []
        if 'request' in self.context:
            lang_param = self.context['request'].query_params.get('lang') or django_get_language()
        else:
            logger.warn('Request is not passed using context. This can cause unexcepted behavior for translation')
            lang_param = django_get_language()

        if lang_param == 'all':
            requested_langs = AVAILABLE_LANGUAGES
        else:
            requested_langs = lang_param.split(',') if lang_param else []

        excluded_langs = [lang for lang in AVAILABLE_LANGUAGES if lang not in requested_langs]
        included_langs = [lang for lang in AVAILABLE_LANGUAGES if lang in requested_langs]
        exclude_fields = []
        included_fields_lang = {}
        for f in get_translatable_fields_for_model(self.Meta.model):
            exclude_fields.append(f)
            for lang in excluded_langs:
                exclude_fields.append(build_localized_fieldname(f, lang))
            included_fields_lang[f] = []
            for lang in included_langs:
                included_fields_lang[f].append(build_localized_fieldname(f, lang))

        self.included_fields_lang = included_fields_lang
        exclude_fields = set(exclude_fields)
        return [
            f for f in fields if f not in exclude_fields
        ]

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        for field, lang_fields in self.included_fields_lang.items():
            if len(lang_fields) != 1:
                break
            lang_field = lang_fields[0]
            fields[field] = fields.pop(lang_field)
            fields[field].source = lang_field
        return fields
