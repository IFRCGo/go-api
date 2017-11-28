import os
from elasticsearch import Elasticsearch

host = ['http://localhost:9200/']
remote_host = os.environ.get('ES_HOST')
if remote_host is not None:
    host = [remote_host]

ES_CLIENT = Elasticsearch(host)
