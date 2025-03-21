import logging
import sys

formatter = logging.Formatter(fmt="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

screen_handler = logging.StreamHandler(stream=sys.stdout)
screen_handler.setFormatter(formatter)

logger = logging.getLogger("api")
logger.setLevel("DEBUG")
logger.addHandler(screen_handler)

# NOTE: Disabled due to old azure_storage_logging package.
# TODO: Replace this with opentelemetry?
#  https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable?tabs=python
# from azure_storage_logging.handlers import (
#     BlobStorageTimedRotatingFileHandler as storage,
# )
# from django.conf import settings
#
# if settings.AZURE_STORAGE_ACCOUNT is not None and settings.AZURE_STORAGE_KEY is not None:
#     handler = storage(
#         account_name=settings.AZURE_STORAGE_ACCOUNT,
#         account_key=settings.AZURE_STORAGE_KEY,
#         filename="go.log",
#         when="M",
#         interval=90,
#         container="logs",
#         encoding="utf-8",
#     )
#     handler.setFormatter(formatter)
#     logger.addHandler(handler)
# else:
#     logger.warning("No Azure credentials found, falling back to local logs.")
