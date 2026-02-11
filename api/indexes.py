GenericMapping = {
    "properties": {
        "id": {"type": "keyword"},
        "event_id": {"type": "keyword"},
        "type": {"type": "keyword"},
        "name": {"type": "text"},
        "keyword": {"type": "keyword", "normalizer": "lowercase"},
        "visibility": {"type": "text"},
        "ns": {"type": "text"},
        "body": {"type": "text", "analyzer": "autocomplete"},
        "date": {"type": "date"},
    }
}

GenericSetting = {
    "settings": {
        "number_of_shards": 1,
        "analysis": {
            "filter": {
                "autocomplete_filter": {"type": "edge_ngram", "min_gram": 3, "max_gram": 10, "token_chars": ["letter", "digit"]}
            },
            "analyzer": {
                "autocomplete": {"type": "custom", "tokenizer": "standard", "filter": ["lowercase", "autocomplete_filter"]}
            },
            "normalizer": {"lowercase": {"type": "custom", "char_filter": [], "filter": ["lowercase"]}},
        },
    }
}

ES_PAGE_NAME = "page_all"

# Warehouse stocks index
WAREHOUSE_INDEX_NAME = "warehouse_stocks"

WAREHOUSE_MAPPING = {
    "properties": {
        "warehouse_id": {"type": "keyword"},
        "warehouse_name": {"type": "text", "fields": {"raw": {"type": "keyword", "normalizer": "lowercase"}}},
        "country_iso3": {"type": "keyword"},
        "country_name": {"type": "text", "fields": {"raw": {"type": "keyword"}}},
        "region": {"type": "keyword"},
        "product_id": {"type": "keyword"},
        "item_number": {"type": "keyword"},
        "item_name": {"type": "text", "analyzer": "autocomplete", "fields": {"raw": {"type": "keyword"}}},
        "item_group": {"type": "keyword"},
        "unit": {"type": "keyword"},
        "quantity": {"type": "double"},
        "item_status": {"type": "keyword"},
        "item_status_name": {"type": "keyword"},
        "last_updated": {"type": "date"},
    }
}

WAREHOUSE_SETTINGS = {
    "settings": {
        "number_of_shards": 1,
        "analysis": {
            "filter": {
                "autocomplete_filter": {"type": "edge_ngram", "min_gram": 3, "max_gram": 10, "token_chars": ["letter", "digit"]}
            },
            "analyzer": {
                "autocomplete": {"type": "custom", "tokenizer": "standard", "filter": ["lowercase", "autocomplete_filter"]}
            },
            "normalizer": {"lowercase": {"type": "custom", "char_filter": [], "filter": ["lowercase"]}},
        },
    }
}
