import logging
import threading

import boto3
import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils.module_loading import import_string

from .models import TranslationCache

logger = logging.getLogger(__name__)


# Array of language : ['en', 'es', 'fr', ....]
AVAILABLE_LANGUAGES = [lang for lang, _ in settings.LANGUAGES]

IFRC_TRANSLATION_CALL_COUNT = 0
IFRC_TRANSLATION_CALL_LOCK = threading.Lock()


class BaseTranslator:
    def _fake_translation(self, text, dest_language, source_language):
        """
        This is only used for test
        """
        return text + f' translated to "{dest_language}" using source language "{source_language}"'


class DummyTranslator(BaseTranslator):
    def translate_text(self, text, dest_language, source_language="auto"):
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
        return self._translator.translate_text(Text=text, SourceLanguageCode=source_language, TargetLanguageCode=dest_language)[
            "TranslatedText"
        ]


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

    def translate_text(self, text, dest_language, source_language=None):
        if settings.TESTING:
            # NOTE: Mocking for test purpose
            return self._fake_translation(text, dest_language, source_language)

        global IFRC_TRANSLATION_CALL_COUNT

        # A dirty workaround to handle oversized HTML+CSS texts, usually tables:
        textTail = ""
        if len(text) > settings.AZURE_TRANSL_LIMIT:
            truncate_here = self.find_last_slashtable(text, settings.AZURE_TRANSL_LIMIT)
            if truncate_here != -1:
                textTail = text[truncate_here:]
                text = text[:truncate_here]
            else:
                truncate_here = self.find_last_slashp(text, settings.AZURE_TRANSL_LIMIT)
                if truncate_here != -1:
                    textTail = text[truncate_here:]
                    text = text[:truncate_here]
                else:
                    textTail = text[settings.AZURE_TRANSL_LIMIT :]
                    text = text[: settings.AZURE_TRANSL_LIMIT]

        payload = {
            "text": text,
            "from": source_language,
            "to": dest_language,
        }
        if self.is_text_html(text):
            # NOTE: Sending 'text' throws 500 from IFRC translation endpoint
            # So only sending if html
            payload["textType"] = "html"

        # Try cache at first (for shorter texts)
        use_cache = len(text) < 200

        if use_cache:
            cache = TranslationCache.objects.filter(
                text=text,
                source_language=source_language or "",  # source_language can be "detected"
                dest_language=dest_language,
            ).first()
            if cache:
                logger.info(f"IFRC translation cache hit: {text[:30]}... {source_language}>{dest_language}")
                return cache.translated_text

        with IFRC_TRANSLATION_CALL_LOCK:
            IFRC_TRANSLATION_CALL_COUNT += 1
            logger.info(f"IFRC translation API call count: {IFRC_TRANSLATION_CALL_COUNT}")
        logger.info(f"IFRC translation API call: {text[:30]}... {source_language}>{dest_language}")
        response = requests.post(
            self.url,
            headers=self.headers,
            json=payload,
        )

        # Not using == 200 – it would break tests with MagicMock name=requests.post() results
        if response.status_code != 500:
            translated = response.json()[0]["translations"][0]["text"]

            # Cache the translation if original text was short enough
            if use_cache:
                TranslationCache.objects.create(
                    text=text,
                    source_language=source_language or "",  # source_language can be "detected"
                    dest_language=dest_language,
                    translated_text=translated,
                )
            return translated + textTail


def get_translator_class():
    return import_string(settings.AUTO_TRANSLATION_TRANSLATOR)
