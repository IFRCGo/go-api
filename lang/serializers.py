import logging
from rest_framework import serializers
from django.db import transaction
from django.conf import settings
from django.utils.translation import get_language as django_get_language
from modeltranslation.utils import build_localized_fieldname
from modeltranslation.manager import (
    get_translatable_fields_for_model,
)

from api.utils import get_model_name

from .tasks import translate_model_fields, translate_model_fields_in_bulk
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
    @classmethod
    def _get_included_excluded_fields(cls, model):
        requested_lang = django_get_language()

        excluded_langs = [lang for lang, _ in settings.LANGUAGES if lang != requested_lang]
        excluded_fields = set()
        included_fields_lang = {}
        for f in get_translatable_fields_for_model(model):
            excluded_fields.add(f)
            for lang in excluded_langs:
                excluded_fields.add(build_localized_fieldname(f, lang))
            included_fields_lang[f] = build_localized_fieldname(f, requested_lang)
        return included_fields_lang, excluded_fields

    @classmethod
    def _get_language_clear_validated_data(cls, instance, validated_data, included_fields_lang):
        """
        Clear value for other languages for fields if single language is specified
        """
        cleared = False
        for field, current_lang_field in included_fields_lang.items():
            old_value = getattr(instance, current_lang_field) or ''
            if type(validated_data) == dict:
                new_value = validated_data.get(current_lang_field) or validated_data.get(field) or ''
            else:  # NOTE: Assuming it's model instance
                new_value = getattr(validated_data, current_lang_field, getattr(validated_data, field, None)) or ''
            if old_value == new_value:
                continue
            for lang, _ in settings.LANGUAGES:
                lang_field = build_localized_fieldname(field, lang)
                if lang_field == current_lang_field:
                    continue
                if type(validated_data) == dict:
                    validated_data[lang_field] = None
                else:  # NOTE: Assuming it's model instance
                    setattr(validated_data, lang_field, None)
                cleared = True
        return cleared

    @classmethod
    def trigger_field_translation(cls, instance):
        if not settings.TESTING:
            transaction.on_commit(
                lambda: translate_model_fields.delay(get_model_name(type(instance)), instance.pk)
            )
        else:
            # NOTE: For test case run the process directly (Translator will mock the generated text)
            transaction.on_commit(
                lambda: translate_model_fields(get_model_name(type(instance)), instance.pk)
            )

    @classmethod
    def trigger_field_translation_in_bulk(cls, model, instances):
        pks = [instance.pk for instance in instances]
        if not settings.TESTING:
            transaction.on_commit(
                lambda: translate_model_fields_in_bulk.delay(get_model_name(model), pks)
            )
        else:
            # NOTE: For test case run the process directly (Translator will mock the generated text)
            transaction.on_commit(
                lambda: translate_model_fields_in_bulk(get_model_name(model), pks)
            )

    @classmethod
    def reset_and_trigger_translation_fields(cls, instance, created=False):
        """
        To be used directly for a Model instance to reset (if value is changed) and trigger translation.
        """
        if created:
            cls.trigger_field_translation(instance)
        # For exisiting check if translation trigger is required
        current_instance = type(instance).objects.get(pk=instance.pk)
        if cls._get_language_clear_validated_data(
            current_instance,
            instance,
            cls._get_included_excluded_fields(type(instance))[0],
        ):
            cls.trigger_field_translation(instance)

    def get_field_names(self, declared_fields, info):
        """
        Overwrite Serializer get_fields_names to exclude non-active language fields
        """
        self.included_fields_lang, excluded_fields = self._get_included_excluded_fields(self.Meta.model)
        fields = super().get_field_names(declared_fields, info)
        return [
            f for f in fields if f not in excluded_fields
        ]

    def get_fields(self, *args, **kwargs):
        """
        Overwrite Serializer get_fields to include active language on translated fields
        """
        fields = super().get_fields(*args, **kwargs)
        for field, lang_field in self.included_fields_lang.items():
            fields[field] = fields.pop(lang_field)
            fields[field].source = lang_field
        return fields

    def create(self, validated_data):
        instance = super().create(validated_data)
        self.trigger_field_translation(instance)
        return instance

    def update(self, instance, validated_data):
        if self._get_language_clear_validated_data(instance, validated_data, self.included_fields_lang):
            self.trigger_field_translation(instance)
        return super().update(instance, validated_data)
