from django.core.management.base import BaseCommand

from elasticsearch.client import IndicesClient
from elasticsearch.helpers import bulk
from elasticsearch import Elasticsearch

from api.esconnection import ES_CLIENT
from api.indexes import GenericMapping
from api.models import Event, Appeal, FieldReport

class Command(BaseCommand):
    help = 'Create a new elasticsearch index and bulk-index existing objects'

    def handle(self, *args, **options):
        print('Recreating indices')
        self.recreate_index('page_event', GenericMapping)
        self.recreate_index('page_appeal', GenericMapping)
        self.recreate_index('page_report', GenericMapping)

        print('Indexing events')
        self.push_table_to_index(index='page_event', model=Event)

        print('Indexing appeals')
        self.push_table_to_index(index='page_appeal', model=Appeal)

        print('Indexing field reports')
        self.push_table_to_index(index='page_report', model=FieldReport)

    def recreate_index(self, index_name, index_mapping):
        indices_client = IndicesClient(client=ES_CLIENT)
        if indices_client.exists(index_name):
            indices_client.delete(index=index_name)
        indices_client.create(index=index_name)
        indices_client.put_mapping(doc_type='page',
                                   index=index_name,
                                   body=index_mapping)


    def push_table_to_index(self, index, model):
        print('Indexing %s models' % model.objects.all().count())
        query = model.objects.all()
        data = [
            self.convert_for_bulk(index, s) for s in list(query)
        ]
        created, errors = bulk(client=ES_CLIENT, actions=data)
        print('Created %s records' % created)
        if len(errors):
            print('Produced the following errors:')
            print('[%s]' % ', '.join(map(str, errors)))


    def convert_for_bulk(self, index, model_object):
        data = model_object.indexing()
        print(data)
        metadata = {
            '_op_type': 'create',
            '_index': index,
            '_type': 'page',
            '_id': model_object.es_id(),
        }
        data.update(**metadata)
        return data
