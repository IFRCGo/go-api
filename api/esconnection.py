import os
from elasticsearch import Elasticsearch

host = os.environ.get('ES_HOST')
if host is not None:
    ES_CLIENT = Elasticsearch([host])
else:
    print('Warning: No elasticsearch host found, will not index elasticsearch')
    ES_CLIENT = None
