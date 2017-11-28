from django.core.management.base import BaseCommand

from elasticsearch.client import IndicesClient
from elasticsearch.helpers import bulk
from elasticsearch import Elasticsearch

from api.esconnection import ES_CLIENT
from api.indexes import PageIndexMapping
from api.models import Event, Appeal, FieldReport

class Command(BaseCommand):
    help = 'Create a new elasticsearch index and bulk-index existing objects'

    def handle(self, *args, **options):
        self.recreate_index()
        self.push_table_to_index(model=Event)
        self.push_table_to_index(model=Appeal)
        self.push_table_to_index(model=FieldReport)

    def recreate_index(self):
        indices_client = IndicesClient(client=ES_CLIENT)
        index_name = 'pages'
        if indices_client.exists(index_name):
            indices_client.delete(index=index_name)
        indices_client.create(index=index_name)
        indices_client.put_mapping(doc_type='page',
                                   index=index_name,
                                   body=PageIndexMapping)


    def push_table_to_index(self, model):
        data = [
            self.convert_for_bulk(s) for s in model.objects.all()
        ]
        created, errors = bulk(client=ES_CLIENT, actions=data)
        print('Created %s records' % created)
        if len(errors):
            print('Produced the following errors:')
            print('[%s]' % ', '.join(map(str, errors)))

    def convert_for_bulk(self, model_object):
        data = model_object.indexing()
        metadata = {
            '_op_type': 'index',
            '_index': 'pages',
            '_type': 'page',
        }
        data.update(**metadata)
        return data
