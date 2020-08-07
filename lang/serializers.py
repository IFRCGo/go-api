import logging
from rest_framework import serializers
from django.db import transaction
from django.conf import settings
from django.utils.translation import get_language as django_get_language
from rest_framework.request import Request as DrfRequest
from modeltranslation.utils import build_localized_fieldname
from modeltranslation.manager import (
    get_translatable_fields_for_model,
)

from middlewares.middlewares import get_signal_request
from api.utils import get_model_name

from .translation import AVAILABLE_LANGUAGES
from .tasks import translate_model_fields
from .models import (
    String,
)


logger = logging.getLogger(__name__)


class StringSerializer(serializers.ModelSerializer):
    class Meta:
        model = String
        fields = '__all__'


class LanguageBulkActionSerializer(serializers.Serializer):
    SET = 'set'
    DELETE = 'delete'

    ACTION_CHOICES = (
        (SET, 'Set'),
        (DELETE, 'Delete'),
    )

    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    key = serializers.CharField()
    value = serializers.CharField(required=False)
    hash = serializers.CharField(max_length=32, required=False)


class LanguageBulkActionsSerializer(serializers.Serializer):
    actions = LanguageBulkActionSerializer(many=True)


class TranslatedModelSerializerMixin(serializers.ModelSerializer):
    """
    Translation mixin for serializer
    - Using header/GET Params to detect languge
    - Assign original field name to requested field_<language>

    Not feasible:
    - Provide fields for multiple langauge if multiple languages is specified. eg: field_en, field_es
    """
    def get_field_names(self, declared_fields, info):
        fields = super().get_field_names(declared_fields, info)

        requested_langs = []
        request = self.context.get('request') or (get_signal_request() and DrfRequest(get_signal_request()))
        if request is None:
            logger.warn('Request is not available using context/middleware. This can cause unexcepted behavior for translation')
        lang_param = django_get_language()
        requested_langs = [lang_param]

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

    def _get_language_clear_validated_data(self, instance, validated_data):
        """
        Clear value for other languages for fields if single language is specified
        """
        cleared = False
        for field, lang_fields in self.included_fields_lang.items():
            if len(lang_fields) != 1:
                break
            current_lang_field = lang_fields[0]
            old_value = getattr(instance, current_lang_field) or ''
            new_value = validated_data.get(current_lang_field) or validated_data.get(field) or ''
            if old_value == new_value:
                continue
            for lang in AVAILABLE_LANGUAGES:
                lang_field = build_localized_fieldname(field, lang)
                if lang_field == current_lang_field:
                    continue
                validated_data[lang_field] = None
                cleared = True
        return cleared

    @classmethod
    def trigger_field_translation(cls, instance):
        if not settings.TESTING:
            transaction.on_commit(
                lambda: translate_model_fields.delay(get_model_name(cls.Meta.model), instance.pk)
            )
        else:
            # NOTE: For test case run the process directly (Translator will mock the generated text)
            transaction.on_commit(
                lambda: translate_model_fields(get_model_name(cls.Meta.model), instance.pk)
            )

    def create(self, validated_data):
        instance = super().create(validated_data)
        self.trigger_field_translation(instance)
        return instance

    def update(self, instance, validated_data):
        if self._get_language_clear_validated_data(instance, validated_data):
            self.trigger_field_translation(instance)
        return super().update(instance, validated_data)
