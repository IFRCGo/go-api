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

# Cleaned Framework Agreements index
CLEANED_FRAMEWORK_AGREEMENTS_INDEX_NAME = "cleaned_framework_agreements"

# Stock Inventory index (PySpark-transformed stock data)
STOCK_INVENTORY_INDEX_NAME = "stock_inventory"

CLEANED_FRAMEWORK_AGREEMENTS_MAPPING = {
    "properties": {
        "id": {"type": "long"},
        "agreement_id": {"type": "keyword"},
        "classification": {"type": "keyword"},
        "default_agreement_line_effective_date": {"type": "date"},
        "default_agreement_line_expiration_date": {"type": "date"},
        "workflow_status": {"type": "keyword"},
        "status": {"type": "keyword"},
        "price_per_unit": {"type": "double"},
        "pa_line_procurement_category": {"type": "keyword"},
        "vendor_name": {"type": "text", "fields": {"raw": {"type": "keyword"}}},
        "vendor_valid_from": {"type": "date"},
        "vendor_valid_to": {"type": "date"},
        "vendor_country": {"type": "keyword"},
        "region_countries_covered": {"type": "keyword"},
        "item_type": {"type": "keyword"},
        "item_category": {"type": "keyword"},
        "item_service_short_description": {"type": "text"},
        "owner": {"type": "keyword"},
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
    }
}

CLEANED_FRAMEWORK_AGREEMENTS_SETTINGS = {
    "settings": {
        "number_of_shards": 1,
    }
}

STOCK_INVENTORY_MAPPING = {
    "properties": {
        "id": {"type": "long"},
        "warehouse_id": {"type": "keyword"},
        "warehouse": {"type": "text", "fields": {"raw": {"type": "keyword"}}},
        "warehouse_country": {"type": "text", "fields": {"raw": {"type": "keyword"}}},
        "country_iso3": {"type": "keyword"},
        "country": {"type": "text", "fields": {"raw": {"type": "keyword"}}},
        "region": {"type": "keyword"},
        "product_category": {"type": "keyword"},
        "item_name": {"type": "text", "analyzer": "autocomplete", "fields": {"raw": {"type": "keyword"}}},
        "quantity": {"type": "double"},
        "unit_measurement": {"type": "keyword"},
        "catalogue_link": {"type": "keyword", "index": False},
    }
}

STOCK_INVENTORY_SETTINGS = {
    "settings": {
        "number_of_shards": 1,
        "analysis": {
            "filter": {
                "autocomplete_filter": {"type": "edge_ngram", "min_gram": 3, "max_gram": 10, "token_chars": ["letter", "digit"]}
            },
            "analyzer": {
                "autocomplete": {"type": "custom", "tokenizer": "standard", "filter": ["lowercase", "autocomplete_filter"]}
            },
        },
    }
}
