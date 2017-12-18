EventPageMapping = {
    'properties': {
        'id': {'type': 'keyword'},
        'name': {'type': 'text'},
        'dtype': {'type': 'text'},
        'location': {'type': 'text'},
        'summary': {'type': 'text'},
        'date': {'type': 'date'},
    }
}

AppealPageMapping = {
    'properties': {
        'id': {'type': 'keyword'},
        'name': {'type': 'text'},
        'dtype': {'type': 'text'},
        'location': {'type': 'text'},
        'date': {'type': 'date'},
    }
}

ReportPageMapping = {
    'properties': {
        'id': {'type': 'text'},
        'name': {'type': 'text'},
        'dtype': {'type': 'text'},
        'location': {'type': 'text'},
        'summary': {'type': 'text'},
        'date': {'type': 'date'},
    }
}
