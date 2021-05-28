from modeltranslation.admin import (
    TranslationAdmin as O_TranslationAdmin,
    TranslationInlineModelAdmin as O_TranslationInlineModelAdmin,
)
from modeltranslation.utils import build_localized_fieldname
from modeltranslation.translator import translator
from modeltranslation.manager import (
    MultilingualQuerySet,
    FallbackValuesIterable,
    append_fallback,
)

from django.utils.translation import ugettext
from django.contrib import admin
from django.urls import reverse
from django.shortcuts import redirect
from django.urls import path
from django.utils.translation import get_language

# from middlewares.middlewares import get_signal_request

from .translation import AVAILABLE_LANGUAGES
from .serializers import TranslatedModelSerializerMixin

from .models import (
    String,
)


class TranslationAdminMixin():
    SHOW_ALL_LANGUAGE_TOGGLE_SESSION_NAME = 'GO__TRANS_SHOW_ALL_LANGUAGE_IN_FORM'

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
        return exclude + tuple([
            build_localized_fieldname(field, lang)
            for field in self.trans_opts.fields.keys()
            for lang in AVAILABLE_LANGUAGES if lang != current_lang
        ])


class TranslationAdmin(TranslationAdminMixin, O_TranslationAdmin):
    TRANSLATION_REGISTERED_MODELS = set(translator.get_registered_models(abstract=False))

    def get_url_namespace(self, name, absolute=True):
        meta = self.model._meta
        namespace = f'{meta.app_label}_{meta.model_name}_{name}'
        return f'admin:{namespace}' if absolute else namespace

    def get_additional_addlinks(self, request):
        url = reverse(self.get_url_namespace('toggle_edit_all_language')) + f'?next={request.get_full_path()}'
        label = ugettext('hide all language') if self._go__show_all_language_in_form() else ugettext('show all language')
        return [{'url': url, 'label': label}]

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['additional_addlinks'] = extra_context.get('additional_addlinks') or []
        # extra_context['additional_addlinks'].extend(self.get_additional_addlinks(request))
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['additional_addlinks'] = extra_context.get('additional_addlinks') or []
        # extra_context['additional_addlinks'].extend(self.get_additional_addlinks(request))
        return super().add_view(request, form_url, extra_context=extra_context)

    def get_urls(self):
        return [
            path(
                'toggle-edit-all-language/', self.admin_site.admin_view(self.toggle_edit_all_language),
                name=self.get_url_namespace('toggle_edit_all_language', False)
            ),
        ] + super().get_urls()

    def toggle_edit_all_language(self, request):
        request.session[self.SHOW_ALL_LANGUAGE_TOGGLE_SESSION_NAME] = not request.session.get(
            self.SHOW_ALL_LANGUAGE_TOGGLE_SESSION_NAME, False
        )
        return redirect(request.GET.get('next'))

    def save_model(self, request, obj, form, change):
        # To trigger translate
        super().save_model(request, obj, form, change)
        TranslatedModelSerializerMixin.trigger_field_translation(obj)

    def save_formset(self, request, form, formset, change):
        # To trigger translate for inline models
        instances = formset.save()
        if instances and formset.model in self.TRANSLATION_REGISTERED_MODELS:
            TranslatedModelSerializerMixin.trigger_field_translation_in_bulk(formset.model, instances)

    def get_search_fields(self, request):
        # Ex. 'name' is translatable - add 'name_fr', 'name_es', etc
        concated_search = (
            list(self.search_fields) + TranslatedModelSerializerMixin._get_translated_searchfields_list(
                self.model, self.search_fields
            )
        )
        return concated_search


class TranslationInlineModelAdmin(TranslationAdminMixin, O_TranslationInlineModelAdmin):
    pass


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


@admin.register(String)
class StringAdmin(admin.ModelAdmin):
    search_fields = ('language', 'value',)
    list_display = ('key', 'language', 'value')
    list_filter = ('language',)
