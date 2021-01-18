from django.core.management.base import BaseCommand

from elasticsearch.client import IndicesClient
from elasticsearch.helpers import bulk
from elasticsearch import Elasticsearch

from utils.elasticsearch import construct_es_data
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
        elif model.__name__ == 'Country':
            query = model.objects.filter(society_name__isnull=False)
        else:
            query = model.objects.all()
        data = [
            construct_es_data(s, is_create=True) for s in list(query)
        ]
        created, errors = bulk(client=ES_CLIENT, actions=data)
        logger.info('Created %s records' % created)
        if len(errors):
            logger.error('Produced the following errors:')
            logger.error('[%s]' % ', '.join(map(str, errors)))
