import logging

from django.conf import settings
from django.db import transaction
from django.utils.translation import get_language as django_get_language
from django.utils.translation import gettext
from modeltranslation.manager import get_translatable_fields_for_model
from modeltranslation.translator import translator
from modeltranslation.utils import build_localized_fieldname
from rest_framework import serializers

from api.utils import get_model_name
from main.translation import (
    TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME,
    skip_auto_translation,
)

from .models import String
from .tasks import translate_model_fields, translate_model_fields_in_bulk

logger = logging.getLogger(__name__)


class StringSerializer(serializers.ModelSerializer):
    class Meta:
        model = String
        fields = "__all__"


class LanguageBulkActionSerializer(serializers.Serializer):
    SET = "set"
    DELETE = "delete"

    ACTION_CHOICES = (
        (SET, "Set"),
        (DELETE, "Delete"),
    )

    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    key = serializers.CharField()
    value = serializers.CharField(required=False)
    hash = serializers.CharField(max_length=32, required=False)
    page_name = serializers.CharField(required=False)


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

    TRANSLATION_REGISTERED_MODELS = set(translator.get_registered_models(abstract=False))

    @classmethod
    def _get_included_excluded_fields(cls, model, selected_fields=None):
        requested_lang = django_get_language()

        excluded_langs = [lang for lang, _ in settings.LANGUAGES if lang != requested_lang]
        excluded_fields = set()
        additional_fields = []
        included_fields_lang = {}
        for f in get_translatable_fields_for_model(model) or []:
            requested_lang_field = build_localized_fieldname(f, requested_lang)
            if selected_fields and f not in selected_fields:
                continue
            excluded_fields.add(f)
            if selected_fields and requested_lang_field not in selected_fields:
                additional_fields.append(requested_lang_field)
            for lang in excluded_langs:
                excluded_fields.add(build_localized_fieldname(f, lang))
            included_fields_lang[f] = requested_lang_field
        return included_fields_lang, excluded_fields, additional_fields

    @classmethod
    def _get_translated_searchfields_list(cls, model, orig_searchfields=[]):
        """
        Add translatable fieldnames to search if the original field is in search
        """
        field_list = []
        for field in get_translatable_fields_for_model(model) or []:
            if field in orig_searchfields:
                field_list.extend([f"{field}_en", f"{field}_es", f"{field}_fr", f"{field}_ar"])
        return field_list

    @classmethod
    def _get_language_clear_validated_data(cls, instance, validated_data, included_fields_lang):
        """
        Clear value for other languages for fields if single language is specified
        """
        cleared = False
        for field, current_lang_field in included_fields_lang.items():
            old_value = getattr(instance, current_lang_field) or ""
            if isinstance(validated_data, dict):
                new_value = validated_data.get(current_lang_field) or validated_data.get(field) or ""
            else:  # NOTE: Assuming it's model instance
                new_value = getattr(validated_data, current_lang_field, getattr(validated_data, field, None)) or ""
            if old_value == new_value:
                continue
            for lang, _ in settings.LANGUAGES:
                lang_field = build_localized_fieldname(field, lang)
                if lang_field == current_lang_field:
                    continue
                if isinstance(validated_data, dict):
                    validated_data[lang_field] = ""
                else:  # NOTE: Assuming it's model instance
                    setattr(validated_data, lang_field, "")
                cleared = True
        return cleared

    @classmethod
    def trigger_field_translation(cls, instance):
        if skip_auto_translation(instance):
            # Skip translation
            return
        transaction.on_commit(lambda: translate_model_fields.delay(get_model_name(type(instance)), instance.pk))

    @classmethod
    def trigger_field_translation_in_bulk(cls, model, instances):
        pks = [instance.pk for instance in instances if not skip_auto_translation(instance)]
        if pks:
            transaction.on_commit(lambda: translate_model_fields_in_bulk.delay(get_model_name(model), pks))

    @classmethod
    def reset_and_trigger_translation_fields(cls, instance, created=False):
        """
        To be used directly for a Model instance to reset (if value is changed) and trigger translation.
        """
        if skip_auto_translation(instance):
            # Skip translation
            return
        if created:
            cls.trigger_field_translation(instance)
        # For existing check if translation trigger is required
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
        fields = super().get_field_names(declared_fields, info)
        if not self.is_translate_model:
            return fields
        (
            self.included_fields_lang,
            excluded_fields,
            additional_fields,
        ) = self._get_included_excluded_fields(self.Meta.model, selected_fields=fields)
        return [f for f in fields if f not in excluded_fields] + additional_fields

    def get_fields(self, *args, **kwargs):
        """
        Overwrite Serializer get_fields to include active language on translated fields
        """
        fields = super().get_fields(*args, **kwargs)
        if not self.is_translate_model:
            return fields

        for field, lang_field in self.included_fields_lang.items():
            fields[field] = fields.pop(lang_field)
            # Commented out, hopefully makes the fallback work
            # fields[field].source = lang_field

        return {
            **fields,
            "translation_module_original_language": serializers.ChoiceField(choices=settings.LANGUAGES, read_only=True),
        }

    @property
    def is_translate_model(self):
        return self.Meta.model in self.TRANSLATION_REGISTERED_MODELS

    def run_validation(self, data):
        if self.instance and self.is_translate_model:
            entity_original_language = getattr(self.instance, TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME)
            if entity_original_language != django_get_language():
                raise serializers.ValidationError(
                    {"non_field_errors": gettext("Only original langauge is supported: %s" % (entity_original_language))}
                )
        return super().run_validation(data)

    def create(self, validated_data):
        if self.is_translate_model:
            validated_data[TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME] = django_get_language()
        instance = super().create(validated_data)
        if self.is_translate_model:
            self.trigger_field_translation(instance)
        return instance

    def update(self, instance, validated_data):
        if self.is_translate_model and self._get_language_clear_validated_data(
            instance, validated_data, self.included_fields_lang
        ):
            self.trigger_field_translation(instance)
        return super().update(instance, validated_data)


class ModelSerializer(TranslatedModelSerializerMixin, serializers.ModelSerializer):
    """
    Custom ModelSerializer with translaion logic (Also works for normal models)
    """

    pass


class LanguageCodeTitleSerializer(serializers.Serializer):
    code = serializers.CharField()
    title = serializers.CharField()


class LanguageListSerializer(serializers.Serializer):
    count = serializers.IntegerField(required=False, allow_null=True)
    results = LanguageCodeTitleSerializer(many=True, required=False, allow_null=True)


class LanguageRetriveSerializer(serializers.Serializer):
    code = serializers.CharField(required=False, allow_null=True)
    title = serializers.CharField(required=False, allow_null=True)
    strings = StringSerializer(many=True, required=False, allow_null=True)


class LanguageBulkActionResponseSerializer(serializers.Serializer):
    new_strings = StringSerializer(many=True, required=False, allow_null=True)
    updated_strings = StringSerializer(many=True, required=False, allow_null=True)
    deleted_string_ids = serializers.ListField(allow_null=True, required=False)
