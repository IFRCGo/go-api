import boto3

from modeltranslation.admin import TranslationBaseModelAdmin
from modeltranslation.utils import build_localized_fieldname
from modeltranslation import settings as mt_settings
from modeltranslation.manager import get_translatable_fields_for_model

from rest_framework import serializers
from django.utils.translation import get_language
from django.conf import settings


# Array of language : ['en', 'es', 'fr', ....]
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
            lang_param = self.context['request'].query_params.get('lang') or DEFAULT_LANGUAGE
        else:
            # TODO: Throw warning here
            lang_param = DEFAULT_LANGUAGE

        if lang_param == 'all':
            requested_langs = AVAILABLE_LANGUAGES
        else:
            requested_langs = lang_param.split(',') if lang_param else []

        excluded_langs = [lang for lang in AVAILABLE_LANGUAGES if lang not in requested_langs]
        exclude_fields = []
        for f in get_translatable_fields_for_model(self.Meta.model):
            exclude_fields.append(f)
            for lang in excluded_langs:
                exclude_fields.append(build_localized_fieldname(f, lang))

        exclude_fields = set(exclude_fields)
        return [
            f for f in fields if f not in exclude_fields
        ]
