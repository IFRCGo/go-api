from elasticsearch.helpers import bulk

from api.esconnection import ES_CLIENT
from api.indexes import ES_PAGE_NAME
from api.logger import logger


def log_errors(errors):
    if len(errors):
        logger.error("Produced the following errors:")
        logger.error("[%s]" % ", ".join(map(str, errors)))


def delete_es_index(instance):
    """instance needs an es_id()"""

    if ES_CLIENT and ES_PAGE_NAME:
        # To make sure it doesn't run for tests
        if hasattr(instance, "es_id"):
            try:
                deleted, errors = bulk(
                    client=ES_CLIENT,
                    actions=[{"_op_type": "delete", "_index": ES_PAGE_NAME, "_type": "page", "_id": instance.es_id()}],
                )
                logger.info(f"Deleted {deleted} records")
                log_errors(errors)
            except Exception:
                logger.error("Could not reach Elasticsearch server or index was already missing.")
        else:
            logger.warning("instance does not have an es_id() method")


def construct_es_data(instance, is_create=False):
    data = instance.indexing()
    metadata = {
        "_op_type": "create" if is_create else "update",
        "_index": ES_PAGE_NAME,
        "_type": "page",
        "_id": instance.es_id(),
    }
    if is_create:
        metadata.update(**data)
    else:
        metadata["doc"] = data
        # Create the document when an update targets a missing ES record (#2523)
        metadata["doc_as_upsert"] = True
    return metadata


def _log_bulk_errors(errors, context=""):
    if not errors:
        return
    logger.error(
        "Elasticsearch bulk indexing produced errors%s: %s",
        f" ({context})" if context else "",
        errors[:5],
        extra={"error_count": len(errors)},
    )


def create_es_index(instance):
    """Creates an Elasticsearch index from the record instance"""

    if ES_CLIENT and ES_PAGE_NAME:
        try:
            created, errors = bulk(client=ES_CLIENT, actions=[construct_es_data(instance, True)])
            logger.info(f"Created {created} records for {instance.__class__.__name__} pk={instance.pk}")
            _log_bulk_errors(errors, f"create {instance.__class__.__name__}:{instance.pk}")
        except Exception:
            logger.error(
                "Failed to index %s pk=%s",
                instance.__class__.__name__,
                instance.pk,
                exc_info=True,
            )


def update_es_index(instance):
    """Updates the Elasticsearch index from the record instance"""

    if ES_CLIENT and ES_PAGE_NAME:
        try:
            updated, errors = bulk(client=ES_CLIENT, actions=[construct_es_data(instance)])
            logger.info(f"Updated {updated} records for {instance.__class__.__name__} pk={instance.pk}")
            _log_bulk_errors(errors, f"update {instance.__class__.__name__}:{instance.pk}")
        except Exception:
            logger.error(
                "Failed to index %s pk=%s",
                instance.__class__.__name__,
                instance.pk,
                exc_info=True,
            )
