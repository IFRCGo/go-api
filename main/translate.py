import boto3
from django.conf import settings


class AmazonTranslate(object):
    def __init__(self, client=None):
        self.translate = client or boto3.client(
            'translate',
            aws_access_key_id=settings.AWS_TRANSLATE_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_TRANSLATE_SECRET_KEY,
            region_name=settings.AWS_TRANSLATE_REGION,
        )

    def translate_text(self, text, source_language, dest_language):
        return self.translate.translate_text(
            Text=text,
            SourceLanguageCode=source_language,
            TargetLanguageCode=dest_language
        )
