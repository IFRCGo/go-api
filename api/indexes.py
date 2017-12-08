EventPageMapping = {
    'properties': {
        'id': {'type': 'keyword'},
        'name': {'type': 'text'},
        'dtype': {'type': 'text'},
        'location': {'type': 'text'},
        'summary': {'type': 'text'},
    }
}

AppealPageMapping = {
    'properties': {
        'id': {'type': 'keyword'},
        'name': {'type': 'text'},
        'dtype': {'type': 'text'},
        'location': {'type': 'text'},
    }
}

ReportPageMapping = {
    'properties': {
        'id': {'type': 'text'},
        'name': {'type': 'text'},
        'dtype': {'type': 'text'},
        'location': {'type': 'text'},
        'summary': {'type': 'text'},
    }
}
