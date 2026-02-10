from django.core.management.base import BaseCommand
from elasticsearch.client import IndicesClient

from api.esconnection import ES_CLIENT
from api.indexes import (
    CLEANED_FRAMEWORK_AGREEMENTS_INDEX_NAME,
    CLEANED_FRAMEWORK_AGREEMENTS_MAPPING,
    CLEANED_FRAMEWORK_AGREEMENTS_SETTINGS,
)
from api.logger import logger


class Command(BaseCommand):
    help = "Create the cleaned_framework_agreements Elasticsearch index with mapping and settings"

    def handle(self, *args, **options):
        if ES_CLIENT is None:
            logger.error("ES client not configured, cannot create index")
            return

        indices_client = IndicesClient(client=ES_CLIENT)
        index_name = CLEANED_FRAMEWORK_AGREEMENTS_INDEX_NAME

        try:
            if indices_client.exists(index_name):
                logger.info(f"Deleting existing index {index_name}")
                indices_client.delete(index=index_name)

            logger.info(f"Creating index {index_name}")
            indices_client.create(index=index_name, body=CLEANED_FRAMEWORK_AGREEMENTS_SETTINGS)
            # ES7+: do not specify a document type
            indices_client.put_mapping(index=index_name, body=CLEANED_FRAMEWORK_AGREEMENTS_MAPPING)
            logger.info(f"Index {index_name} created")
        except Exception as ex:
            logger.error(f"Failed to create index {index_name}: {str(ex)[:512]}")
            raise
