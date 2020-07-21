import logging
import boto3

from modeltranslation.admin import TranslationAdmin as O_TranslationAdmin
from modeltranslation.utils import build_localized_fieldname
from modeltranslation import settings as mt_settings
from modeltranslation.manager import (
    MultilingualQuerySet,
    FallbackValuesIterable,
    append_fallback,
)

from django.utils.translation import ugettext
from django.urls import reverse
from django.shortcuts import redirect
from django.urls import path
from django.utils.translation import get_language
from django.conf import settings

from middlewares.middlewares import get_signal_request


logger = logging.getLogger(__name__)

# Array of language : ['en', 'es', 'fr', ....]
DJANGO_AVAILABLE_LANGUAGES = set([lang[0] for lang in settings.LANGUAGES])
AVAILABLE_LANGUAGES = mt_settings.AVAILABLE_LANGUAGES
DEFAULT_LANGUAGE = mt_settings.DEFAULT_LANGUAGE


class TranslationAdmin(O_TranslationAdmin):
    SHOW_ALL_LANGUAGE_TOGGLE_SESSION_NAME = 'GO__TRANS_SHOW_ALL_LANGUAGE_IN_FORM'

    def _go__show_all_language_in_form(self):
        return get_signal_request().session.get(self.SHOW_ALL_LANGUAGE_TOGGLE_SESSION_NAME, False)

    def get_url_namespace(self, name, absolute=True):
        meta = self.model._meta
        namespace = f'{meta.app_label}_{meta.model_name}_{name}'
        return f'admin:{namespace}' if absolute else namespace

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        url = reverse(self.get_url_namespace('toggle_edit_all_language')) + f'?next={request.get_full_path()}'
        label = ugettext('hide all language') if self._go__show_all_language_in_form() else ugettext('show all language')
        extra_context['additional_addlinks'] = [{'url': url, 'label': label}]
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

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
            for lang in AVAILABLE_LANGUAGES
            if lang != current_lang
        ])


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


class AmazonTranslate(object):
    """
    Amazon Translate helper
    """
    def __init__(self, client=None):
        self.translate = client or boto3.client(
            'translate',
            aws_access_key_id=settings.AWS_TRANSLATE_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_TRANSLATE_SECRET_KEY,
            region_name=settings.AWS_TRANSLATE_REGION,
        )

    def translate_text(self, text, dest_language, source_language='auto'):
        # NOTE: using 'auto' as source_language will cost extra. Language Detection: https://aws.amazon.com/comprehend/pricing/
        return self.translate.translate_text(
            Text=text,
            SourceLanguageCode=source_language,
            TargetLanguageCode=dest_language
        )
