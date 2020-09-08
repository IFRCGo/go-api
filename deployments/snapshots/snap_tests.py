# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestProjectAPI::test_project_list_one 1'] = {
    'count': 1,
    'next': None,
    'previous': None,
    'results': [
        {
            'actual_expenditure': 0,
            'budget_amount': 0,
            'dtype': 72,
            'dtype_detail': {
                'id': 72,
                'name': None,
                'summary': None
            },
            'end_date': '2020-09-08',
            'event': 8,
            'event_detail': {
                'dtype': 70,
                'id': 8,
                'name': None,
                'parent_event': 7,
                'slug': None
            },
            'id': 24,
            'modified_at': '2019-03-23T00:00:00.123456Z',
            'name': None,
            'operation_type': 1,
            'operation_type_display': 'Emergency Operation',
            'primary_sector': 6,
            'primary_sector_display': 'Shelter',
            'programme_type': 2,
            'programme_type_display': 'Domestic',
            'project_country': 327,
            'project_country_detail': {
                'id': 327,
                'independent': None,
                'iso': 'ZS',
                'iso3': 'YCQ',
                'name': None,
                'record_type': 5,
                'region': 15,
                'society_name': None
            },
            'project_districts': [
            ],
            'project_districts_detail': [
            ],
            'reached_female': 0,
            'reached_male': 0,
            'reached_other': 0,
            'reached_total': 0,
            'regional_project': 1,
            'regional_project_detail': {
                'created_at': '2019-03-23T00:00:00.123456Z',
                'id': 1,
                'modified_at': '2019-03-23T00:00:00.123456Z',
                'name': None
            },
            'reporting_ns': 326,
            'reporting_ns_detail': {
                'id': 326,
                'independent': None,
                'iso': 'Sn',
                'iso3': 'iWX',
                'name': None,
                'record_type': 5,
                'region': 14,
                'society_name': None
            },
            'secondary_sectors': [
            ],
            'secondary_sectors_display': [
            ],
            'start_date': '2020-09-08',
            'status': 1,
            'status_display': 'Ongoing',
            'target_female': 0,
            'target_male': 0,
            'target_other': 0,
            'target_total': 0,
            'user': 47,
            'visibility': 'public'
        }
    ]
}

snapshots['TestProjectAPI::test_project_list_zero 1'] = {
    'count': 0,
    'next': None,
    'previous': None,
    'results': [
    ]
}
