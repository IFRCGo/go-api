from django.core.management.base import BaseCommand
from elasticsearch.client import IndicesClient

from api.esconnection import ES_CLIENT
from api.indexes import WAREHOUSE_INDEX_NAME, WAREHOUSE_MAPPING, WAREHOUSE_SETTINGS
from api.logger import logger


class Command(BaseCommand):
    help = "Create the warehouse_stocks Elasticsearch index with mapping and settings"

    def handle(self, *args, **options):
        if ES_CLIENT is None:
            logger.error("ES client not configured, cannot create index")
            return

        indices_client = IndicesClient(client=ES_CLIENT)
        index_name = WAREHOUSE_INDEX_NAME

        try:
            if indices_client.exists(index_name):
                logger.info(f"Deleting existing index {index_name}")
                indices_client.delete(index=index_name)

            logger.info(f"Creating index {index_name}")
            indices_client.create(index=index_name, body=WAREHOUSE_SETTINGS)
            # Put mapping (ES7+: do not specify a document type)
            indices_client.put_mapping(index=index_name, body=WAREHOUSE_MAPPING)
            logger.info(f"Index {index_name} created")
        except Exception as ex:
            logger.error(f"Failed to create index {index_name}: {str(ex)[:512]}")
            raise
