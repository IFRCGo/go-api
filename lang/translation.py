import logging
import boto3

from django.conf import settings


logger = logging.getLogger(__name__)


# Array of language : ['en', 'es', 'fr', ....]
AVAILABLE_LANGUAGES = [lang for lang, _ in settings.LANGUAGES]


class AmazonTranslate(object):
    """
    Amazon Translate helper
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

    def _fake_translation(self, text, dest_language, source_language):
        """
        This is only used for test
        """
        return text + f' translated to "{dest_language}" using source language "{source_language}"'

    def translate_text(self, text, dest_language, source_language='auto'):
        # NOTE: using 'auto' as source_language will cost extra. Language Detection: https://aws.amazon.com/comprehend/pricing/
        if not settings.TESTING:
            return self.translate.translate_text(
                Text=text,
                SourceLanguageCode=source_language,
                TargetLanguageCode=dest_language
            )['TranslatedText']
        else:
            # NOTE: Mocking for test purpose
            return self._fake_translation(text, dest_language, source_language)
