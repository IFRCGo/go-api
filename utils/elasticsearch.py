from api.logger import logger
from api.indexes import ES_PAGE_NAME
from api.esconnection import ES_CLIENT
from elasticsearch.helpers import bulk


def log_errors(errors):
    if len(errors):
        logger.error('Produced the following errors:')
        logger.error('[%s]' % ', '.join(map(str, errors)))


def delete_es_index(instance):
    ''' instance needs an es_id() '''
    if hasattr(instance, 'es_id'):
        try:
            deleted, errors = bulk(client=ES_CLIENT, actions=[{
                '_op_type': 'delete',
                '_index': ES_PAGE_NAME,
                '_type': 'page',
                '_id': instance.es_id()
            }])
            logger.info(f'Deleted {deleted} records')
            log_errors(errors)
        except Exception:
            logger.error('Could not reach Elasticsearch server or index was already missing.')
    else:
        logger.warn('instance does not have an es_id() method')


def construct_es_data(instance, is_create=False):
    data = instance.indexing()
    metadata = {
        '_op_type': 'create' if is_create else 'update',
        '_index': ES_PAGE_NAME,
        '_type': 'page',
        '_id': instance.es_id(),
    }
    if (is_create):
        metadata.update(**data)
    else:
        metadata['doc'] = data
    return metadata


def create_es_index(instance):
    created, errors = bulk(client=ES_CLIENT, actions=[construct_es_data(instance, True)])
    logger.info(f'Created {created} records')
    log_errors(errors)


def update_es_index(instance):
    updated, errors = bulk(client=ES_CLIENT, actions=[construct_es_data(instance)])
    logger.info('Updated {updated} records')
    log_errors(errors)
