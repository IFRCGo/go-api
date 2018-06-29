GenericMapping = {
    'properties': {
        'id': {'type': 'keyword'},
        'event_id': {'type': 'keyword'},
        'type': {'type': 'keyword'},
        'name': {'type': 'text'},
        'body': {
            'type': 'text',
            'analyzer': 'autocomplete'
        },
        'date': {'type': 'date'},
    }
}

GenericSetting = {
    'settings': {
        'number_of_shards': 1,
        'analysis': {
            'filter': {
                'autocomplete_filter': {
                    'type': 'edge_ngram',
                    'min_gram': 3,
                    'max_gram': 10,
                    'token_chars': [
                        'letter',
                        'digit'
                    ]
                }
            },
            'analyzer': {
                'autocomplete': {
                    'type': 'custom',
                    'tokenizer': 'standard',
                    'filter': [
                        'lowercase',
                        'autocomplete_filter'
                    ]
                }
            }
        }
    }
}

ES_PAGE_NAME = 'page_all'
