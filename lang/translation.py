import hashlib
import logging
import threading

import boto3
import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.db.models import BooleanField, Case, F, Value, When
from django.utils import timezone
from django.utils.module_loading import import_string

from .models import TranslationCache

logger = logging.getLogger(__name__)


# Array of language : ['en', 'es', 'fr', ....]
AVAILABLE_LANGUAGES = [lang for lang, _ in settings.LANGUAGES]

IFRC_TRANSLATION_CALL_COUNT = 0
IFRC_TRANSLATION_CALL_LOCK = threading.Lock()


def sha256_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class BaseTranslator:
    def get_cached_translations(self, text, dest_languages, source_language=None, table_field=""):
        return {}

    def _fake_translation(self, text, dest_language, source_language, table_field=""):
        """
        This is only used for test
        """
        return text + f' translated to "{dest_language}" using source language "{source_language}"'


class DummyTranslator(BaseTranslator):
    def translate_text(self, text, dest_language, source_language="auto", table_field=""):
        return self._fake_translation(text, dest_language, source_language)


class AmazonTranslator(BaseTranslator):
    """
    Amazon Translator helper
    """

    def __init__(self, client=None):
        if settings.TESTING:
            return

        if not settings.AWS_TRANSLATE_ACCESS_KEY or not settings.AWS_TRANSLATE_SECRET_KEY or not settings.AWS_TRANSLATE_REGION:
            raise Exception("Translation configuration missing")

        # NOTE: Service not used for testing
        self._translator = client or boto3.client(
            "translate",
            aws_access_key_id=settings.AWS_TRANSLATE_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_TRANSLATE_SECRET_KEY,
            region_name=settings.AWS_TRANSLATE_REGION,
        )

    def translate_text(self, text, dest_language, source_language="auto"):
        # NOTE: using 'auto' as source_language will cost extra. Language Detection: https://aws.amazon.com/comprehend/pricing/
        if settings.TESTING:
            # NOTE: Mocking for test purpose
            return self._fake_translation(text, dest_language, source_language)
        try:
            return self._translator.translate_text(Text=text, SourceLanguageCode=source_language, TargetLanguageCode=dest_language)[
                "TranslatedText"
            ]
        except Exception:
            logger.warning(
                "Amazon translation API error for %s>%s",
                source_language,
                dest_language,
                extra={
                    "text_length": len(text),
                    "dest_language": dest_language,
                    "source_language": source_language,
                },
                exc_info=True,
            )
            return None


class IfrcTranslator(BaseTranslator):
    """
    IFRC Translator helper
    """

    domain: str
    url: str
    params: dict

    def __init__(self):
        if not settings.IFRC_TRANSLATION_DOMAIN or not settings.IFRC_TRANSLATION_HEADER_API_KEY:
            raise Exception("Translation configuration missing")
        self.domain = settings.IFRC_TRANSLATION_DOMAIN.strip("/")
        self.url = f"{self.domain}/api/translate"
        self.headers = {
            "X-API-KEY": settings.IFRC_TRANSLATION_HEADER_API_KEY,
        }

    @classmethod
    def is_text_html(cls, text):
        return bool(BeautifulSoup(text, "html.parser").find())

    @classmethod
    def find_last_slashtable(cls, text, limit):
        tag = "</table>"
        truncate_here = text[:limit].rfind(tag)
        if truncate_here != -1:
            truncate_here += len(tag)
        return truncate_here

    @classmethod
    def find_last_slashp(cls, text, limit):
        tag = "</p>"
        truncate_here = text[:limit].rfind(tag)
        if truncate_here != -1:
            truncate_here += len(tag)
        return truncate_here

    @classmethod
    def split_text_for_translation(cls, text, limit):
        """Split at HTML boundaries when possible; hard-split as last resort."""
        if len(text) <= limit:
            return text, ""

        truncate_here = cls.find_last_slashtable(text, limit)
        if truncate_here == -1:
            truncate_here = cls.find_last_slashp(text, limit)
        if truncate_here == -1:
            truncate_here = limit

        return text[:truncate_here], text[truncate_here:]

    def _call_ifrc_api(self, text, dest_language, source_language, table_field):
        payload = {
            "text": text,
            "from": source_language,
            "to": dest_language,
        }
        if self.is_text_html(text):
            payload["textType"] = "html"

        with IFRC_TRANSLATION_CALL_LOCK:
            global IFRC_TRANSLATION_CALL_COUNT
            IFRC_TRANSLATION_CALL_COUNT += 1
            logger.info(f"IFRC translation API call count: {IFRC_TRANSLATION_CALL_COUNT}")
        logger.info(
            "IFRC translation API call – %s>%s – %s (len=%d): %s...",
            source_language,
            dest_language,
            table_field,
            len(text),
            text[:30],
        )
        response = requests.post(
            self.url,
            headers=self.headers,
            json=payload,
        )

        if response.status_code >= 400:
            logger.warning(
                "IFRC translation API error for %s>%s %s",
                source_language,
                dest_language,
                table_field,
                extra={
                    "status_code": response.status_code,
                    "text_length": len(text),
                    "dest_language": dest_language,
                    "source_language": source_language,
                    "table_field": table_field,
                },
            )
            return None

        return response.json()[0]["translations"][0]["text"]

    def _translate_with_cache(self, text, dest_language, source_language, table_field):
        use_cache = len(text) < 300
        if not use_cache:
            return self._call_ifrc_api(text, dest_language, source_language, table_field)

        text_hash = sha256_hash(text)
        cache = TranslationCache.objects.filter(
            text_hash=text_hash,
            source_language=source_language or "",
            dest_language=dest_language,
        ).first()
        if cache:
            cache_other_fields = cache.table_field != table_field
            TranslationCache.objects.filter(id=cache.pk).update(
                last_used=timezone.now(),
                num_calls=F("num_calls") + 1,
                other_fields=Case(
                    When(other_fields=True, then=Value(True)),
                    default=Value(cache_other_fields),
                    output_field=BooleanField(),
                ),
            )
            logger.info(
                f"Translation cache hit, {source_language}>{dest_language} {table_field} – {cache.num_calls}: {text[:30]}... "
            )
            return cache.translated_text

        translated = self._call_ifrc_api(text, dest_language, source_language, table_field)
        if translated is None:
            return None

        obj, created = TranslationCache.objects.get_or_create(
            text=text,
            text_hash=text_hash,
            source_language=source_language or "",
            dest_language=dest_language,
            defaults={
                "translated_text": translated,
                "table_field": table_field or "",
                "last_used": timezone.now(),
            },
        )
        if not created:
            TranslationCache.objects.filter(pk=obj.pk).update(
                last_used=timezone.now(),
                num_calls=F("num_calls") + 1,
            )
        return translated

    def translate_text(self, text, dest_language, source_language=None, table_field=""):
        if settings.TESTING:
            return self._fake_translation(text, dest_language, source_language)

        if not text:
            return text

        original_length = len(text)
        head, tail = self.split_text_for_translation(text, settings.AZURE_TRANSL_LIMIT)
        translated_head = self._translate_with_cache(head, dest_language, source_language, table_field)
        if translated_head is None:
            return None

        if not tail:
            return translated_head

        translated_tail = self.translate_text(tail, dest_language, source_language, table_field)
        if translated_tail is None:
            logger.warning(
                "IFRC translation stopped after partial chunk for %s>%s %s",
                source_language,
                dest_language,
                table_field,
                extra={"original_text_length": original_length, "translated_head_length": len(translated_head)},
            )
            return None

        return translated_head + translated_tail

    def get_cached_translations(self, text, dest_languages, source_language=None, table_field=""):
        if not dest_languages or len(text) >= 300:
            return {}

        text_hash = sha256_hash(text)
        source_language = source_language or ""
        caches = TranslationCache.objects.filter(
            text_hash=text_hash,
            source_language=source_language,
            dest_language__in=dest_languages,
        )
        cache_by_lang = {cache.dest_language: cache for cache in caches}
        if not cache_by_lang:
            return {}
        cache_ids = [cache.id for cache in cache_by_lang.values()]
        TranslationCache.objects.filter(id=cache_ids).update(
            last_used=timezone.now(),
            num_calls=F("num_calls") + 1,
        )
        TranslationCache.objects.filter(id=cache_ids, other_fields=False).exclude(table_field=table_field).update(
            other_fields=True,
        )
        return {lang: cache.translated_text for lang, cache in cache_by_lang.items()}


def get_translator_class():
    return import_string(settings.AUTO_TRANSLATION_TRANSLATOR)
