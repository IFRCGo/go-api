from django.core.management.base import BaseCommand

from elasticsearch.client import IndicesClient
from elasticsearch.helpers import bulk
from elasticsearch import Elasticsearch

from api.esconnection import ES_CLIENT
from api.indexes import GenericMapping, GenericSetting, ES_PAGE_NAME
from api.models import Region, Country, Event, Appeal, FieldReport
from api.logger import logger


class Command(BaseCommand):
    help = 'Create a new elasticsearch index and bulk-index existing objects'

    def handle(self, *args, **options):
        logger.info('Recreating indices')
        self.recreate_index(ES_PAGE_NAME, GenericMapping, GenericSetting)

        logger.info('Indexing regions')
        self.push_table_to_index(model=Region)

        logger.info('Indexing countries')
        self.push_table_to_index(model=Country)

        logger.info('Indexing events')
        self.push_table_to_index(model=Event)

        logger.info('Indexing appeals')
        self.push_table_to_index(model=Appeal)

        logger.info('Indexing field reports')
        self.push_table_to_index(model=FieldReport)

    def recreate_index(self, index_name, index_mapping, index_setting):
        indices_client = IndicesClient(client=ES_CLIENT)
        if indices_client.exists(index_name):
            indices_client.delete(index=index_name)
        indices_client.create(index=index_name,
                              body=index_setting)
        indices_client.put_mapping(doc_type='page',
                                   index=index_name,
                                   body=index_mapping)

    def push_table_to_index(self, model):
        if model.__name__ == 'Event':
            query = model.objects.filter(parent_event__isnull=True)
        else:
            query = model.objects.all()
        data = [
            self.convert_for_bulk(s) for s in list(query)
        ]
        created, errors = bulk(client=ES_CLIENT, actions=data)
        logger.info('Created %s records' % created)
        if len(errors):
            logger.error('Produced the following errors:')
            logger.error('[%s]' % ', '.join(map(str, errors)))

    def convert_for_bulk(self, model_object):
        data = model_object.indexing()
        metadata = {
            '_op_type': 'create',
            '_index': ES_PAGE_NAME,
            '_type': 'page',
            '_id': model_object.es_id(),
        }
        data.update(**metadata)
        return data
