import logging
import requests
import boto3

from django.conf import settings
from django.utils.module_loading import import_string


logger = logging.getLogger(__name__)


# Array of language : ['en', 'es', 'fr', ....]
AVAILABLE_LANGUAGES = [lang for lang, _ in settings.LANGUAGES]


class BaseTranslator():
    def _fake_translation(self, text, dest_language, source_language):
        """
        This is only used for test
        """
        return text + f' translated to "{dest_language}" using source language "{source_language}"'


class DummyTranslator(BaseTranslator):
    def translate_text(self, text, dest_language, source_language='auto'):
        return self._fake_translation(text, dest_language, source_language)


class AmazonTranslator(BaseTranslator):
    """
    Amazon Translator helper
    """
    def __init__(self, client=None):
        if settings.TESTING:
            return

        if (
            not settings.AWS_TRANSLATE_ACCESS_KEY or
            not settings.AWS_TRANSLATE_SECRET_KEY or
            not settings.AWS_TRANSLATE_REGION
        ):
            raise Exception('Translation configuration missing')

        # NOTE: Service not used for testing
        self.translate = client or boto3.client(
            'translate',
            aws_access_key_id=settings.AWS_TRANSLATE_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_TRANSLATE_SECRET_KEY,
            region_name=settings.AWS_TRANSLATE_REGION,
        )

    def translate_text(self, text, dest_language, source_language='auto'):
        # NOTE: using 'auto' as source_language will cost extra. Language Detection: https://aws.amazon.com/comprehend/pricing/
        if settings.TESTING:
            # NOTE: Mocking for test purpose
            return self._fake_translation(text, dest_language, source_language)
        return self.translate.translate_text(
            Text=text,
            SourceLanguageCode=source_language,
            TargetLanguageCode=dest_language
        )['TranslatedText']


class IfrcTranslator(BaseTranslator):
    """
    IFRC Translator helper
    """
    url: str
    params: dict

    def __init__(self):
        if settings.TESTING:
            return

        if (
            not settings.IFRC_TRANSLATION_URL or
            not settings.IFRC_TRANSLATION_API_KEY
        ):
            raise Exception('Translation configuration missing')
        self.url = settings.IFRC_TRANSLATION_URL
        self.params = dict(
            apiKey=settings.IFRC_TRANSLATION_API_KEY
        )

    def translate_text(self, text, dest_language, source_language=None):
        if settings.TESTING:
            # NOTE: Mocking for test purpose
            return self._fake_translation(text, dest_language, source_language)
        payload = {
            "text": text,
            "from": source_language,
            "to": dest_language,
        }
        response = requests.post(
            self.url,
            params=self.params,
            json=payload,
        )
        return response.json()[0]["Translations"][0]["Text"]


def get_translator_class():
    return import_string(settings.AUTO_TRANSLATION_TRANSLATOR)
