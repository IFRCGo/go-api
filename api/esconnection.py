import os
from elasticsearch import Elasticsearch

hosts = ['http://dsgoes.northeurope.cloudapp.azure.com:9200/']
if os.environ.get('LOCAL_ES'):
    hosts = ['http://localhost:9200/']

ES_CLIENT = Elasticsearch(hosts)
