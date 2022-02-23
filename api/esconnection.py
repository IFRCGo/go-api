from elasticsearch import Elasticsearch
from django.conf import settings

if settings.ELASTIC_SEARCH_HOST is not None:
    ES_CLIENT = Elasticsearch([settings.ELASTIC_SEARCH_HOST], timeout=2, max_retries=3, retry_on_timeout=True)
else:
    print('Warning: No elasticsearch host found, will not index elasticsearch')
    ES_CLIENT = None
