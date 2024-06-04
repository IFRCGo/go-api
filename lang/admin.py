from django.contrib import admin
from django.db import models
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.translation import get_language, gettext
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override as translation_override
from modeltranslation.admin import TranslationAdmin as O_TranslationAdmin
from modeltranslation.admin import (
    TranslationInlineModelAdmin as O_TranslationInlineModelAdmin,
)
from modeltranslation.manager import (
    FallbackValuesIterable,
    MultilingualQuerySet,
    append_fallback,
)
from modeltranslation.translator import translator
from modeltranslation.utils import build_localized_fieldname

from main.translation import (
    TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME,
    TRANSLATOR_SKIP_FIELD_NAME,
)

from .models import String
from .serializers import TranslatedModelSerializerMixin
from .translation import AVAILABLE_LANGUAGES

# from middlewares.middlewares import get_signal_request


class TranslationAdminMixin:
    SHOW_ALL_LANGUAGE_TOGGLE_SESSION_NAME = "GO__TRANS_SHOW_ALL_LANGUAGE_IN_FORM"

    def _go__show_all_language_in_form(self):
        # return get_signal_request().session.get(self.SHOW_ALL_LANGUAGE_TOGGLE_SESSION_NAME, False)
        return True  # temporarily always show all languages

    # Overwrite TranslationBaseModelAdmin _exclude_original_fields to only show current language field in Admin panel
    def _exclude_original_fields(self, exclude=None):
        exclude = super()._exclude_original_fields(exclude)
        if self._go__show_all_language_in_form():
            return exclude
        current_lang = get_language()
        # Exclude other languages
        return exclude + tuple(
            [
                build_localized_fieldname(field, lang)
                for field in self.trans_opts.fields.keys()
                for lang in AVAILABLE_LANGUAGES
                if lang != current_lang
            ]
        )


class TranslationAdmin(TranslationAdminMixin, O_TranslationAdmin):
    TRANSLATION_REGISTERED_MODELS = set(translator.get_registered_models(abstract=False))

    def get_url_namespace(self, name, absolute=True):
        meta = self.model._meta
        namespace = f"{meta.app_label}_{meta.model_name}_{name}"
        return f"admin:{namespace}" if absolute else namespace

    def get_additional_addlinks(self, request):
        url = reverse(self.get_url_namespace("toggle_edit_all_language")) + f"?next={request.get_full_path()}"
        label = gettext("hide all language") if self._go__show_all_language_in_form() else gettext("show all language")
        return [{"url": url, "label": label}]

    def get_list_filter(self, request):
        return [
            *super().get_list_filter(request),
            TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME,
            TRANSLATOR_SKIP_FIELD_NAME,
        ]

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["additional_addlinks"] = extra_context.get("additional_addlinks") or []
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def add_view(self, request, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["additional_addlinks"] = extra_context.get("additional_addlinks") or []
        return super().add_view(request, form_url, extra_context=extra_context)

    def get_urls(self):
        return [
            path(
                "toggle-edit-all-language/",
                self.admin_site.admin_view(self.toggle_edit_all_language),
                name=self.get_url_namespace("toggle_edit_all_language", False),
            ),
        ] + super().get_urls()

    def toggle_edit_all_language(self, request):
        request.session[self.SHOW_ALL_LANGUAGE_TOGGLE_SESSION_NAME] = not request.session.get(
            self.SHOW_ALL_LANGUAGE_TOGGLE_SESSION_NAME, False
        )
        return redirect(request.GET.get("next"))

    def save_model(self, request, obj, form, change):
        # To trigger translate
        entity_original_language = getattr(obj, TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME)
        with translation_override(entity_original_language):
            if obj.pk is None:
                TranslatedModelSerializerMixin.trigger_field_translation(obj)
            else:
                TranslatedModelSerializerMixin.reset_and_trigger_translation_fields(obj)
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        # To trigger translate for inline models
        # commit=False as we will be changing per the translation need
        instances = formset.save(commit=False)
        # Need to manually delete deleted_objects
        for obj in formset.deleted_objects:
            obj.delete()

        # Manually trigger translation
        for instance in instances:
            if type(instance) in self.TRANSLATION_REGISTERED_MODELS:
                entity_original_language = getattr(instance, TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME)
                with translation_override(entity_original_language):
                    if instance.pk is None:
                        TranslatedModelSerializerMixin.trigger_field_translation(instance)
                    else:
                        TranslatedModelSerializerMixin.reset_and_trigger_translation_fields(instance)
            instance.save()
        formset.save_m2m()

    def get_search_fields(self, request):
        # Ex. 'name' is translatable - add 'name_fr', 'name_es', etc
        concated_search = list(self.search_fields) + TranslatedModelSerializerMixin._get_translated_searchfields_list(
            self.model, self.search_fields
        )
        return concated_search


class TranslationInlineModelAdmin(TranslationAdminMixin, O_TranslationInlineModelAdmin): ...


# NOTE: Fixing modeltranslation Queryset to support experssions in Queryset values()
# https://github.com/deschler/django-modeltranslation/issues/517
def multilingual_queryset__values(self, *original, prepare=False, **expressions):
    if not prepare:
        return super(MultilingualQuerySet, self)._values(*original, **expressions)
    new_fields, translation_fields = append_fallback(self.model, original)
    clone = super(MultilingualQuerySet, self)._values(*list(new_fields), **expressions)
    clone.original_fields = tuple(original)
    clone.translation_fields = translation_fields
    clone.fields_to_del = new_fields - set(original)
    return clone


def multilingual_queryset_values(self, *fields, **expressions):
    fields += tuple(expressions)
    if not self._rewrite:
        return super(MultilingualQuerySet, self).values(*fields, **expressions)
    if not fields:
        # Emulate original queryset behaviour: get all fields that are not translation fields
        fields = self._get_original_fields()
    clone = self._values(*fields, prepare=True, **expressions)
    clone._iterable_class = FallbackValuesIterable
    return clone


MultilingualQuerySet._values = multilingual_queryset__values
MultilingualQuerySet.values = multilingual_queryset_values


class StringStaleFilter(admin.SimpleListFilter):
    title = _("Stale strings")
    parameter_name = "is_stale"

    def lookups(self, *_):
        return [
            (True, "True"),
        ]

    def queryset(self, _, queryset):
        value = self.value()
        if value is None:
            return queryset
        queryset = queryset.exclude(language="en").annotate(
            en_value_hash=models.Subquery(
                String.objects.filter(
                    page_name=models.OuterRef("page_name"),
                    key=models.OuterRef("key"),
                    language="en",
                ).values(
                    "hash"
                )[:1],
                output_field=models.CharField(),
            ),
        )
        return queryset.exclude(hash=models.F("en_value_hash"))


@admin.register(String)
class StringAdmin(admin.ModelAdmin):
    search_fields = (
        "key",
        "page_name",
        "value",
        "hash",
    )
    list_display = (
        "page_name",
        "key",
        "language",
        "value",
        "hash",
    )
    list_filter = (
        "language",
        StringStaleFilter,
    )
    readonly_fields = (
        "language",
        "page_name",
        "key",
        "hash",
    )

    def has_add_permission(self, *_):
        return False

    def has_change_permission(self, _, obj=None):
        if obj and obj.language == "en":
            return False
        return True

    def has_delete_permission(self, *_):
        return False

    def save_model(self, request, obj, form, change):
        """
        Update hash to use main language value
        NOTE: Save will be treated as stale fixed
        """
        obj.hash = String.objects.get(
            page_name=obj.page_name,
            key=obj.key,
            language="en",
        ).hash
        super().save_model(request, obj, form, change)
