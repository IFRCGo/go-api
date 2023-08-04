import logging
import sys

from django.conf import settings

from azure_storage_logging.handlers import BlobStorageTimedRotatingFileHandler as storage

formatter = logging.Formatter(
    fmt='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

screen_handler = logging.StreamHandler(stream=sys.stdout)
screen_handler.setFormatter(formatter)

logger = logging.getLogger('api')
logger.setLevel('DEBUG')
logger.addHandler(screen_handler)

if (
    settings.AZURE_ACCOUNT_NAME is not None and
    settings.AZURE_ACCOUNT_KEY is not None
):
    handler = storage(
        account_name=settings.AZURE_ACCOUNT_NAME,
        account_key=settings.AZURE_ACCOUNT_KEY,
        filename='go.log',
        when='M',
        interval=90,
        container='logs',
        encoding='utf-8'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
else:
    logger.warning('No Azure credentials found, falling back to local logs.')
