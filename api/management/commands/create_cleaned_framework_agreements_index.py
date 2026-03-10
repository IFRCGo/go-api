from django.core.management.base import BaseCommand
from elasticsearch.client import IndicesClient

from api.esaliashelper import create_versioned_index, get_alias_targets, swap_alias
from api.esconnection import ES_CLIENT
from api.indexes import (
    CLEANED_FRAMEWORK_AGREEMENTS_INDEX_NAME,
    CLEANED_FRAMEWORK_AGREEMENTS_MAPPING,
    CLEANED_FRAMEWORK_AGREEMENTS_SETTINGS,
)
from api.logger import logger


class Command(BaseCommand):
    help = "Create a versioned cleaned_framework_agreements Elasticsearch index and point the alias at it"

    def handle(self, *args, **options):
        if ES_CLIENT is None:
            logger.error("ES client not configured, cannot create index")
            return

        alias_name = CLEANED_FRAMEWORK_AGREEMENTS_INDEX_NAME
        indices_client = IndicesClient(client=ES_CLIENT)
        old_indexes = get_alias_targets(indices_client, alias_name)

        try:
            versioned_name = create_versioned_index(
                es_client=ES_CLIENT,
                alias_name=alias_name,
                settings=CLEANED_FRAMEWORK_AGREEMENTS_SETTINGS,
                mapping=CLEANED_FRAMEWORK_AGREEMENTS_MAPPING,
            )
            logger.info("Created versioned index '%s'", versioned_name)

            swap_alias(
                indices_client=indices_client,
                alias_name=alias_name,
                new_index=versioned_name,
                old_indexes=old_indexes,
            )
            logger.info("Alias '%s' now points to '%s'", alias_name, versioned_name)
        except Exception as ex:
            logger.error("Failed to create index for alias '%s': %s", alias_name, str(ex)[:512])
            raise
