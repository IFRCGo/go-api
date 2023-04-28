# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestProjectAPI::test_global_project_api 1'] = {
    'ns_with_ongoing_activities': 16,
    'projects_per_programme_type': [
        {
            'count': 6,
            'programme_type': 0,
            'programme_type_display': 'Bilateral'
        },
        {
            'count': 3,
            'programme_type': 1,
            'programme_type_display': 'Multilateral'
        },
        {
            'count': 7,
            'programme_type': 2,
            'programme_type_display': 'Domestic'
        }
    ],
    'projects_per_secondary_sectors': [
    ],
    'projects_per_sector': [
        {
            'count': 16,
            'primary_sector': 1,
            'primary_sector_display': 'sect-zoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYx'
        }
    ],
    'target_total': 0,
    'total_ongoing_projects': 16
}

snapshots['TestProjectAPI::test_global_project_api 2'] = {
    'results': [
        {
            'budget_amount_total': 7890000,
            'id': 5,
            'iso3': 'YvZ',
            'name': 'country-SZuAxgjBPLqqIBKxNrRzWnAJYJElxJJEqtKwXTzViQhVoCYSkg',
            'ongoing_projects': 1,
            'operation_types': [
                1
            ],
            'operation_types_display': [
                'Emergency Operation'
            ],
            'projects_per_sector': [
                {
                    'count': 1,
                    'primary_sector': 1,
                    'primary_sector_display': 'sect-zoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYx'
                }
            ],
            'society_name': 'society-name-JNSRTdkyOaZfjEMBfeqoxfMcUyzNPHsTMdXlOFCamQZHsmcYMG',
            'target_total': 0
        },
        {
            'budget_amount_total': 1430000,
            'id': 7,
            'iso3': 'kfs',
            'name': 'country-ZwjrVnVzStakFageXSAHAPsUBklxlTimFlGhCKnlmdVlZWmqAC',
            'ongoing_projects': 1,
            'operation_types': [
                1
            ],
            'operation_types_display': [
                'Emergency Operation'
            ],
            'projects_per_sector': [
                {
                    'count': 1,
                    'primary_sector': 1,
                    'primary_sector_display': 'sect-zoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYx'
                }
            ],
            'society_name': 'society-name-fyhrevbLpEFRWgadrWaQLYcgnHYayMHWrFEWvMBvxRvupxQzyN',
            'target_total': 0
        },
        {
            'budget_amount_total': 4740000,
            'id': 9,
            'iso3': 'RTM',
            'name': 'country-XrUUrqOGvAQqwfagTZFpLFoLBQrgXTFJMKyMHQycMgLYPgKghW',
            'ongoing_projects': 1,
            'operation_types': [
                0
            ],
            'operation_types_display': [
                'Programme'
            ],
            'projects_per_sector': [
                {
                    'count': 1,
                    'primary_sector': 1,
                    'primary_sector_display': 'sect-zoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYx'
                }
            ],
            'society_name': 'society-name-AzTVcwPYCDKHczZOVXBQbnKlbOvgsAZbUDqwRwwprCYduDSOqX',
            'target_total': 0
        },
        {
            'budget_amount_total': 1510000,
            'id': 11,
            'iso3': 'upQ',
            'name': 'country-jfwLeHpiSEbcdrzABgtvOLbWeYhdCLFQDhqcbVPqLpIXJeTKWS',
            'ongoing_projects': 1,
            'operation_types': [
                1
            ],
            'operation_types_display': [
                'Emergency Operation'
            ],
            'projects_per_sector': [
                {
                    'count': 1,
                    'primary_sector': 1,
                    'primary_sector_display': 'sect-zoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYx'
                }
            ],
            'society_name': 'society-name-TeuYlcqNMGcZLtPMFzYMHFOoPemDLCRhAyMJVsgAygjnFsdFEK',
            'target_total': 0
        },
        {
            'budget_amount_total': 2590000,
            'id': 13,
            'iso3': 'DUn',
            'name': 'country-HMXjEmKAVfuMCBqXaumRPVuACdVEGMDFTvwqkBeLTbpYHqjlEn',
            'ongoing_projects': 1,
            'operation_types': [
                1
            ],
            'operation_types_display': [
                'Emergency Operation'
            ],
            'projects_per_sector': [
                {
                    'count': 1,
                    'primary_sector': 1,
                    'primary_sector_display': 'sect-zoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYx'
                }
            ],
            'society_name': 'society-name-ldTllPjEggWeDxPFBMhFgBkdXskNIxhsrJzKJocxlgBLanLZll',
            'target_total': 0
        },
        {
            'budget_amount_total': 4880000,
            'id': 15,
            'iso3': 'Rap',
            'name': 'country-pUBMSvIcwbWUYtuZdxUcMlIrzDkUadDmrlWMWmKcSDCoVFjLur',
            'ongoing_projects': 1,
            'operation_types': [
                1
            ],
            'operation_types_display': [
                'Emergency Operation'
            ],
            'projects_per_sector': [
                {
                    'count': 1,
                    'primary_sector': 1,
                    'primary_sector_display': 'sect-zoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYx'
                }
            ],
            'society_name': 'society-name-JbeAivJwhwcRiSSOatvbQlJgtnvoeiDMqXRRRRooWFNWvmfZUU',
            'target_total': 0
        },
        {
            'budget_amount_total': 1740000,
            'id': 17,
            'iso3': 'ZEZ',
            'name': 'country-SQTvZhsNCjqMSdmiiprEFesBYNvcLpTwuxwSCcjccAhEqemAtq',
            'ongoing_projects': 1,
            'operation_types': [
                0
            ],
            'operation_types_display': [
                'Programme'
            ],
            'projects_per_sector': [
                {
                    'count': 1,
                    'primary_sector': 1,
                    'primary_sector_display': 'sect-zoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYx'
                }
            ],
            'society_name': 'society-name-zhXkgJKpQMfOjERUWYaAubCVzgjkjIPpPTObxyssAJSwpQaqxx',
            'target_total': 0
        },
        {
            'budget_amount_total': 1230000,
            'id': 19,
            'iso3': 'zEf',
            'name': 'country-MhpQyDQuMgAtrSOKhumYjUhJPbggmdHuingwzIXkpslIqTaUij',
            'ongoing_projects': 1,
            'operation_types': [
                1
            ],
            'operation_types_display': [
                'Emergency Operation'
            ],
            'projects_per_sector': [
                {
                    'count': 1,
                    'primary_sector': 1,
                    'primary_sector_display': 'sect-zoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYx'
                }
            ],
            'society_name': 'society-name-OpXkaiupWqkpIBCZcCEybtXiNUmPOQQLWIFOTBTzEtdISFFiec',
            'target_total': 0
        },
        {
            'budget_amount_total': 1150000,
            'id': 21,
            'iso3': 'Bzu',
            'name': 'country-GtArEivAdsyZDGkPcRnBNbzSguTYSwcQlzepqbSNEofijYXRdT',
            'ongoing_projects': 1,
            'operation_types': [
                0
            ],
            'operation_types_display': [
                'Programme'
            ],
            'projects_per_sector': [
                {
                    'count': 1,
                    'primary_sector': 1,
                    'primary_sector_display': 'sect-zoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYx'
                }
            ],
            'society_name': 'society-name-sPauoVOlrkOPhSAKrovoSkGVBeDJQaxJepHcvColhoyXZCJWPJ',
            'target_total': 0
        },
        {
            'budget_amount_total': 8860000,
            'id': 23,
            'iso3': 'CQe',
            'name': 'country-qWYnIFiQbCuCMmUgtPtqPMrZYZhLTKyQruRKWWPylOqQmJraKT',
            'ongoing_projects': 1,
            'operation_types': [
                0
            ],
            'operation_types_display': [
                'Programme'
            ],
            'projects_per_sector': [
                {
                    'count': 1,
                    'primary_sector': 1,
                    'primary_sector_display': 'sect-zoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYx'
                }
            ],
            'society_name': 'society-name-wCoQOAHvaPCduRhIjwfPhYbmfPIBCibEwLgrrVxABeNAZzUDRy',
            'target_total': 0
        },
        {
            'budget_amount_total': 2410000,
            'id': 25,
            'iso3': 'uBA',
            'name': 'country-icmMwRdPTZdCGBCCvvacXumVuEYOOyTdPozCnnyerlqErfwWfB',
            'ongoing_projects': 1,
            'operation_types': [
                1
            ],
            'operation_types_display': [
                'Emergency Operation'
            ],
            'projects_per_sector': [
                {
                    'count': 1,
                    'primary_sector': 1,
                    'primary_sector_display': 'sect-zoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYx'
                }
            ],
            'society_name': 'society-name-TePrGXYYSkSqPpAtIveCHkSCRxVFEmdWyeqzbfFQqXfMytbUdd',
            'target_total': 0
        },
        {
            'budget_amount_total': 4770000,
            'id': 27,
            'iso3': 'rMT',
            'name': 'country-OaaikPCKBXkVrtvlCGsmaSaoMIFGOWcAYsBvKtVMfQWIAIPUtM',
            'ongoing_projects': 1,
            'operation_types': [
                0
            ],
            'operation_types_display': [
                'Programme'
            ],
            'projects_per_sector': [
                {
                    'count': 1,
                    'primary_sector': 1,
                    'primary_sector_display': 'sect-zoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYx'
                }
            ],
            'society_name': 'society-name-mSlanULjkyJzGEbPRnExxVYFIxYsuETSyunaLjqVAsnbGhoijl',
            'target_total': 0
        },
        {
            'budget_amount_total': 1590000,
            'id': 29,
            'iso3': 'nUd',
            'name': 'country-vywZNUlnadilslioCfzytonQUmVZSwfZMNNCOVkeeeuiNkCWaY',
            'ongoing_projects': 1,
            'operation_types': [
                0
            ],
            'operation_types_display': [
                'Programme'
            ],
            'projects_per_sector': [
                {
                    'count': 1,
                    'primary_sector': 1,
                    'primary_sector_display': 'sect-zoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYx'
                }
            ],
            'society_name': 'society-name-AZEBOqidOTSYhUXfFWSpececNhbRXqzcdvlPctLvyAIZzTwfbm',
            'target_total': 0
        },
        {
            'budget_amount_total': 8470000,
            'id': 31,
            'iso3': 'tSc',
            'name': 'country-UMYoFEUEYltXVlqkEGtYSelIQFOAXYgiWVGjBgkrTLNJDCMKMs',
            'ongoing_projects': 1,
            'operation_types': [
                1
            ],
            'operation_types_display': [
                'Emergency Operation'
            ],
            'projects_per_sector': [
                {
                    'count': 1,
                    'primary_sector': 1,
                    'primary_sector_display': 'sect-zoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYx'
                }
            ],
            'society_name': 'society-name-ATJhlDwzfUascJBEmjuYHzGrHebykrDeywzNmOWSYYIVAuelbv',
            'target_total': 0
        },
        {
            'budget_amount_total': 3720000,
            'id': 33,
            'iso3': 'qdv',
            'name': 'country-gEjLhkzKGguporwomItnbNOiAMDGGPmnhdTlXdGvSjcPxzqvNH',
            'ongoing_projects': 1,
            'operation_types': [
                1
            ],
            'operation_types_display': [
                'Emergency Operation'
            ],
            'projects_per_sector': [
                {
                    'count': 1,
                    'primary_sector': 1,
                    'primary_sector_display': 'sect-zoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYx'
                }
            ],
            'society_name': 'society-name-IZwBwUNxfLEVqSpXMXwcqsWTQOQtTSKUYiWRbLxruxrMflWHne',
            'target_total': 0
        },
        {
            'budget_amount_total': 7040000,
            'id': 35,
            'iso3': 'rSa',
            'name': 'country-vqBqljxxKiiFeNlOaEtrfQgsRHykMQTFGmiOGsumHhWkWKVhOB',
            'ongoing_projects': 1,
            'operation_types': [
                1
            ],
            'operation_types_display': [
                'Emergency Operation'
            ],
            'projects_per_sector': [
                {
                    'count': 1,
                    'primary_sector': 1,
                    'primary_sector_display': 'sect-zoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYx'
                }
            ],
            'society_name': 'society-name-SXZWbVLJLoVBIUCceEjexSfIqPYDWsqYcdduqRpPfQkikTAtLl',
            'target_total': 0
        }
    ]
}

snapshots['TestProjectAPI::test_personnel_csv_api 1'] = '''event_id,event_glide_id,event_name,event_ifrc_severity_level,event_disaster_type,event_country_name,event_country_iso3,event_country_nationalsociety,event_country_regionname,role,type,name,deployed_id,deployed_to_name,deployed_to_iso3,deployed_to_nationalsociety,deployed_to_regionname,deployed_from_name,deployed_from_iso3,deployed_from_nationalsociety,deployed_from_regionname,start_date,end_date,ongoing,is_active,molnix_id,molnix_sector,molnix_role_profile,molnix_language,molnix_region,molnix_scope,molnix_modality,molnix_operation\r
,,,,,,,,,,,,1,,,,,,,,,,,True,True,,,,,,,,\r
,,,,,,,,,,,,2,,,,,,,,,,,True,True,,,,,,,,\r
,,,,,,,,,,,,3,,,,,,,,,,,True,True,,,,,,,,\r
,,,,,,,,,,,,4,,,,,,,,,,,True,True,,,,,,,,\r
,,,,,,,,,,,,5,,,,,,,,,,,True,True,,,,,,,,\r
,,,,,,,,,,,,6,,,,,,,,,,,True,True,,,,,,,,\r
,,,,,,,,,,,,7,,,,,,,,,,,True,True,,,,,,,,\r
,,,,,,,,,,,,8,,,,,,,,,,,True,True,,,,,,,,\r
,,,,,,,,,,,,9,,,,,,,,,,,True,True,,,,,,,,\r
,,,,,,,,,,,,10,,,,,,,,,,,True,True,,,,,,,,\r
'''

snapshots['TestProjectAPI::test_project_create 1'] = {
    'actual_expenditure': 0,
    'annual_split_detail': [
    ],
    'budget_amount': 7530000,
    'description': '',
    'document': None,
    'dtype': None,
    'dtype_detail': None,
    'end_date': '2008-01-01',
    'event': None,
    'event_detail': None,
    'id': 1,
    'modified_at': '2008-01-01T00:00:00.123456Z',
    'modified_by': None,
    'modified_by_detail': None,
    'name': 'Mock Project for Create API Test',
    'operation_type': 0,
    'operation_type_display': 'Programme',
    'primary_sector': 1,
    'primary_sector_display': 'sect-blDLTmDfquSPTYkTUhfhTCOxfHTyUYGNkyJycXkvKQjkjlXTdA',
    'programme_type': 2,
    'programme_type_display': 'Domestic',
    'project_country': 1,
    'project_country_detail': {
        'average_household_size': None,
        'fdrs': None,
        'id': 1,
        'independent': None,
        'is_deprecated': False,
        'iso': 'nC',
        'iso3': 'MEE',
        'name': 'country-jlkxMThQoAZvUhEREEnLkPAbpciKLkiOGcKjdkqlHzMKObUUQs',
        'record_type': 1,
        'record_type_display': 'Country',
        'region': 1,
        'society_name': 'society-name-koAMjYLXlNQGqkURvDMLeoyyigbmHGRAjMglENMcYIGWhfEQiM'
    },
    'project_districts': [
        1
    ],
    'project_districts_detail': [
        {
            'code': 'NdSHjDPCfU',
            'id': 1,
            'is_deprecated': True,
            'is_enclave': True,
            'name': 'district-DpBzXcMVyUuzNVKMIHPTYcHgCDcpHIzVcJyHWOdmsCztXsDkBs'
        }
    ],
    'reached_female': 0,
    'reached_male': 0,
    'reached_other': 0,
    'reached_total': 0,
    'regional_project': None,
    'regional_project_detail': None,
    'reporting_ns': 1,
    'reporting_ns_contact_email': None,
    'reporting_ns_contact_name': None,
    'reporting_ns_contact_role': None,
    'reporting_ns_detail': {
        'average_household_size': None,
        'fdrs': None,
        'id': 1,
        'independent': None,
        'is_deprecated': False,
        'iso': 'nC',
        'iso3': 'MEE',
        'name': 'country-jlkxMThQoAZvUhEREEnLkPAbpciKLkiOGcKjdkqlHzMKObUUQs',
        'record_type': 1,
        'record_type_display': 'Country',
        'region': 1,
        'society_name': 'society-name-koAMjYLXlNQGqkURvDMLeoyyigbmHGRAjMglENMcYIGWhfEQiM'
    },
    'secondary_sectors': [
        1,
        2
    ],
    'secondary_sectors_display': [
        'sect-tag-tUXCsOlhimaNWqaDFFIZaMFpnLQEDACfMMapJrNOJndljdPwcj',
        'sect-tag-QKMtvfdgAlkRsNQSSMKYJlDVLxcfXtuxyeWBJesEihSrvHAHnS'
    ],
    'start_date': '2008-01-01',
    'status': 1,
    'status_display': 'Ongoing',
    'target_female': 0,
    'target_male': 0,
    'target_other': 0,
    'target_total': 0,
    'user': 5,
    'visibility': 'public',
    'visibility_display': 'Public'
}

snapshots['TestProjectAPI::test_project_csv_api 1'] = '''actual_expenditure,budget_amount,description,document,dtype,dtype_detail.id,dtype_detail.name,dtype_detail.summary,end_date,event,event_detail.dtype,event_detail.emergency_response_contact_email,event_detail.id,event_detail.name,event_detail.parent_event,event_detail.slug,id,modified_at,modified_by,modified_by_detail,name,operation_type,operation_type_display,primary_sector,primary_sector_display,programme_type,programme_type_display,project_country,project_country_detail.average_household_size,project_country_detail.fdrs,project_country_detail.id,project_country_detail.independent,project_country_detail.is_deprecated,project_country_detail.iso,project_country_detail.iso3,project_country_detail.name,project_country_detail.record_type,project_country_detail.record_type_display,project_country_detail.region,project_country_detail.society_name,project_districts_detail.code,project_districts_detail.id,project_districts_detail.is_deprecated,project_districts_detail.is_enclave,project_districts_detail.name,reached_female,reached_male,reached_other,reached_total,regional_project,regional_project_detail.created_at,regional_project_detail.id,regional_project_detail.modified_at,regional_project_detail.name,reporting_ns,reporting_ns_contact_email,reporting_ns_contact_name,reporting_ns_contact_role,reporting_ns_detail.average_household_size,reporting_ns_detail.fdrs,reporting_ns_detail.id,reporting_ns_detail.independent,reporting_ns_detail.is_deprecated,reporting_ns_detail.iso,reporting_ns_detail.iso3,reporting_ns_detail.name,reporting_ns_detail.record_type,reporting_ns_detail.record_type_display,reporting_ns_detail.region,reporting_ns_detail.society_name,secondary_sectors,secondary_sectors_display,start_date,status,status_display,target_female,target_male,target_other,target_total,user,visibility,visibility_display\r
0,3070000,,,3,3,disaster-type-zjivfEKVdJzqfzGBXSiWiEJmFzPKmJNVHpperXBuRKfhQABxwm,uwMPbXtkwNZCNjCcomRxjWUfhVdpNjsavSZhtCEbvnVInnIHWqJENUjSSQbyLQHcqkdsmYSNrdDPaeyQrQQxgbsPyoyGTguFMIflmGDJTbcpHtvFzVkbwRwwOtpGrZdOqybJrojvzQifUyHRNORoApKjBtMvCIinPiLIRZmitSTHiBXjPKkueJIUhlujUbWuAAtCVOVrjXmgilbWNNrMKNoMooRbwfSXEiGMETPxlyFEikmocAWarAoVQmWnelCNFSuDpBzXcMVyUuzNVKMIHPTYcHgCDcpHIzVcJyHWOdmsCztXsDkBsNdSHjDPCfUGhlXLSIizAuCblDLTmDfquSPTYkTUhfhTCOxfHTyUYGNkyJycXkvKQjkjlXTdAttUXCsOlhimaNWqaDFFIZaMFpnLQEDACfMMapJrNOJndljdPwcjcQKMtvfdgAlkRsNQSSMKYJlDVLxcfXtuxyeWBJesEihSrvHAHnSnNdgKUOHfEUSMYTsB,2008-01-01,2,1,,2,event-silUaSKzXKclMuZNoOKgFjvVepwukOfTQOUvCaqnpSewqYgUad,1,ycuakafywiygeykpwrokcezcsbuqgevkykuejfvmnetbbpkmbk,1,2008-01-01T00:00:00.123456Z,,,project-MuqHKNwiNKFHUOFFZlNoTsmahbDOYhVnZNAAcvwJZOnaOmSsqY,1,Emergency Operation,1,sect-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx,0,Bilateral,3,,,3,,False,gZ,UEW,country-mdryRMMcemZWLUQJnEnvtanmVhVWEpSMTnzpJuXsyDIPwtqxGF,4,Country Office,3,society-name-unxuAcKoVjbqJLLUAsjmvoyKpFJPRvqWFUPVFDkUYwkiUIFlIP,"CefuMjeirN, QWBUdsMtwg","1, 2","False, True","False, True","district-hQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRgFT, district-gYShPPXJUnBCoAvDzAUguBuQqxjREefffBgVVxZiJdLJJvQhAw",0,0,0,0,1,2008-01-01T00:00:00.123456Z,1,2008-01-01T00:00:00.123456Z,regional-project-vREEZcPiEjODIvDYAVdHtKURuJIbnKRvZYwejrbvyOIkKMylMh,2,,,,,,2,,False,Mf,djk,country-WrKoZBJXNNRPJbMQSrblrSWtvwaljKQzejVObfVHnyADvkxtUu,5,Representative Office,2,society-name-WNdRfrCQBFMCArnWGhwBhsRRLFHQtcozMdantnXiWqsuhaFVBl,"1, 2","sect-tag-RoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSx, sect-tag-CCpxgRxIPwdzrmhDfQnPOMbdYvpiYKneWJnLnovXjYMarjiIqZ",2008-01-01,1,Ongoing,0,0,0,0,5,public,Public\r
0,7190000,,,6,6,disaster-type-xVZxVXLHMxpPrnLyfgiOVMhcLPmmTCgeINvtUEWmIUjcimAJTq,WJwxCOThBeEAHGYbkMrSiscKdYSmVzFRIGekCWGyJXyzMrnlakKnLSaYGDGTUHqtosTrJhkocIpscOjrirYdPpnIhaPwOMxufTJqUiANsudOawoUrlqbIQXXLgUVSyPqOOMJnCournLOZWzjCoUUBxjEfFlDllmKFUlPsbtklzRMmejeBpDPzgUHiUWZaMgyybhaWPcipXfrjOMaYaYgIVvTfmiEWKCktvEjpdISrOIhbcgIsgGAjaoboByjwPsoRyRThFkhogsweNvhxfcMjlBHvMlRBjQRtNswgrFQxqZTZeYajXPjujyCUYYEehKBUrjfuilXywuFBESAMYOviZPpyAJFIIFIIoyfLTAHKXSZVoSfpxanbxJEihdwxXisDjJApnodVihSTjyUbSBxdSgQLeEMkbjxjfpeaKAjWlEViVHStEAUvCYPSashjdPcMWlGkazBRDJTqKGtToBkrfHyiVnzNdozlVJMeSDEuPPzykdZxPBm,2008-01-01,4,4,,4,event-fvuzXkBdzWcQPjKdOTZQHsAzRSJtUVuwarHNjSzCPnINYNPCSw,3,zypzxmtfcivyuuvihisnfgjthvwokbbyilqpxtubghudxqogwh,2,2008-01-01T00:00:00.123456Z,,,project-rggexMXvbpskIgenMaWtmJmOcprfKKcKYEcduftawWszGmuWzU,0,Programme,1,sect-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx,1,Multilateral,5,,,5,,False,gI,Lwj,country-REShxGUKbqkLdjuDSiwkdrxAOwdssHOeGmXOlWgMWkIuuRZtrR,3,Region,5,society-name-aiHsxXFAvkgnjGomYJNSHITJSWZhADehibEwtSxiCMHWvlTtbV,"CefuMjeirN, QWBUdsMtwg","1, 2","False, True","False, True","district-hQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRgFT, district-gYShPPXJUnBCoAvDzAUguBuQqxjREefffBgVVxZiJdLJJvQhAw",0,0,0,0,2,2008-01-01T00:00:00.123456Z,2,2008-01-01T00:00:00.123456Z,regional-project-kjRDfOfTonZRPjXTkGHUMPHXvCYivsxNBcTXRypnNMejKOFgZa,4,,,,,,4,,False,at,cRM,country-uTcrAfFpxCtnHtlhxYcXmfCGbZEGjmvEUHtXujXgHRinUcDyTH,1,Country,4,society-name-fvDcgHXQVtbKWtOnummsrIuXCQhrjkrhaNJGgnIwJurjTZsKpk,"1, 2","sect-tag-RoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSx, sect-tag-CCpxgRxIPwdzrmhDfQnPOMbdYvpiYKneWJnLnovXjYMarjiIqZ",2008-01-01,1,Ongoing,0,0,0,0,6,public,Public\r
0,9720000,,,9,9,disaster-type-hYQmOusTYYfwMZFbNLAkxqmGrHbFukdPpStqCBvcrVWQDQfvJc,iNaVKbtymEyycSRrSyvxZGYBATviwUqJmFsrfCQfZQuGhbZiZWgpelxejKZpXfeaUaVZvNejLODOvYQgNhdTimVflfTfaBYRondTfyuOHmEmTFMTlEsURLdClGaflmqjIKmShSWemluWokzOLsMAGOsnBqwVpHaPRqsWkedeFwUdNWBfRWTCaVRfuLXxSRMReKqUuCwVZExFtWFuIVmoLkcSwADDuYzDDCjjVWyAbiYuyOjzxaBYQljLlngbzEjrvmbFzktJromFMUFBBkFQdwgeuTEMsjpHFZnAFatOkvOtRNBNhMiHsvUxZSixKEebCxApnuSouOEYrJvKYvSmiuYOKoTLNppFKEbuGgyWjNufHFDMUreCyXmYXrTjxXdEpoOauwNEJjYruFuMImZPmMMhsUdVmHZGspYyBSatqnjsbbPPWAfxDXjCOyJkMCWugrDrmTMDskLiubhduJExjuUyJbOBPuzluNWcPsuKWKcGdUTTiFee,2008-01-01,6,7,,6,event-nDqchHQOlEiDLuxKyQLcuSgOwakAEvvPglwtkDIlWbCZNDLKSB,5,uzepquxmverztcowggabxrkzlbkgktmshmkwiiqvydftyxjzwd,3,2008-01-01T00:00:00.123456Z,,,project-ijgHkTpfWxwvfAvWeFzIdHAPYzSjJfnCkhWqopdPRJbdPSoEcc,0,Programme,1,sect-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx,0,Bilateral,7,,,7,,False,we,AMV,country-yTwekseIKpHNGtzNdIShLEqPbcvAqmvWdinJUvWQdpFeZKNSWZ,1,Country,7,society-name-NfJEirUcgcFGoPwBEtYobdbXYZmIMyRRVbJEdyXySiBSBJihCh,"CefuMjeirN, QWBUdsMtwg","1, 2","False, True","False, True","district-hQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRgFT, district-gYShPPXJUnBCoAvDzAUguBuQqxjREefffBgVVxZiJdLJJvQhAw",0,0,0,0,3,2008-01-01T00:00:00.123456Z,3,2008-01-01T00:00:00.123456Z,regional-project-QTSAJecmLcnoLFawSfLxGkznjIaOVNsrJxGykmWMqvmuqzhPsC,6,,,,,,6,,False,NP,dVY,country-YfFgDukskerKxwfelTXDqEqWCPihKFcxszANRiCxGNuxfRAGCq,1,Country,6,society-name-pSJajgsykKzeoyDQfwDDPIDgflUgzXBmzveuvMFnSVEhrDcIjE,"1, 2","sect-tag-RoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSx, sect-tag-CCpxgRxIPwdzrmhDfQnPOMbdYvpiYKneWJnLnovXjYMarjiIqZ",2008-01-01,1,Ongoing,0,0,0,0,7,public,Public\r
0,800000,,,12,12,disaster-type-eSHyDByhcbGOMQJZRETyhaJfsmxyYfsdUpJsuPpPfLGWdYErAY,WXJPimutALuRYgcamUXbDWzlaxrvVLyCevbScBBQyBrfeaPzxtfTfTosaZCIugzNLrXNEcHNaxXJWmBAJmsJjyIUKKNzkyMDYaHoIBJJHOKhEHRQPFYNexbxZLBlxDeKDybSMpibfiBSWwDOHKJlyatfJaWKxieYDxvGuhDFDsTfQViFsyMlYegIRZPJjrfMTLziBrlkjMEvGLeCdZTqUUxrigJwRsxFcuBXGiaKjixFaTKbUdeOzoTvArdDknirElGkJNuUYradfFHPHlkSqTCpfiAeyIYXxaEedYwJPSWdfhKxaNlDZgQfulBfVcVxoYCdKimccDeZBLuRaaEqSPfGKYtJTuSsoZPjZKHDALJKnAwiMqrEXhAUfNYUGjEmZtZIfnXUXecqvcjwXJQNzoRleDsnYYUxCqHWpvjAHdzrIBcVBCmLJoTqtIGmJtluZoyZOtziIdvvdCCrTdzxCNvwfxzknKlUaMcIvXugcFOStUbQMgog,2008-01-01,8,10,,8,event-XbcmdHnxyzMfWbyjRDeuVnglXnqvwdBGJlBKgFOFBWJPjNnHqs,7,vchptjayhcxmvtpeqjvhiacnopxnuhdgqxcssbmdgxkltezssk,4,2008-01-01T00:00:00.123456Z,,,project-fgDXGygMRbjvZsTCRydRSlkObzTNxourSfRlafQilCuYYKwdak,0,Programme,1,sect-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx,1,Multilateral,9,,,9,,False,YT,uCi,country-fdLhjgCijUesXvSuLpTEBAhPQQJULtTnEPcxkzmwedcZqylFDQ,4,Country Office,9,society-name-uVTBQuWKSlaYkqAfFvjcipGMFrmUlAcXaOxTvZNxvagEXGmnjv,"CefuMjeirN, QWBUdsMtwg","1, 2","False, True","False, True","district-hQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRgFT, district-gYShPPXJUnBCoAvDzAUguBuQqxjREefffBgVVxZiJdLJJvQhAw",0,0,0,0,4,2008-01-01T00:00:00.123456Z,4,2008-01-01T00:00:00.123456Z,regional-project-CscFgWCTmiDMJdwTVLRxPboQWedazsRNntXUanSLharwicnBcG,8,,,,,,8,,False,Ms,YQp,country-znlhcyZgVnmWKVVtSRnLtxDdPOoKqnGbtanlvnFUyUuDzMWkFE,5,Representative Office,8,society-name-eNgabNdaratCyUKkgdxnPmBVxerAPbtXchtjqDZnhOVRYbElah,"1, 2","sect-tag-RoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSx, sect-tag-CCpxgRxIPwdzrmhDfQnPOMbdYvpiYKneWJnLnovXjYMarjiIqZ",2008-01-01,1,Ongoing,0,0,0,0,8,public,Public\r
0,6370000,,,15,15,disaster-type-GWvRMZcyEWnKAntRkSGSNGWEzbVuZOubQOtKiihSDdqPJBWSWe,IzRUCbAznldWezWkKRaEmZLLlXGNfRKIkFhJjASuXnXZoDfDVaIBtNqkzLskbnTSLIRQpfRXputROMSbhswXKNACbyMleNvICmaxqMHkroJGVXrQYpZdSjYSRVeDUIhAEGayOyPrQoRhvPHLWWdgyPqXLUQjPGfvamCXchEdMjAOtcCdnbGOIcHOeDkzjHkMAJlPXstHuWbQbDjHGQLvKlPPDOrfeAIaBLRhUMyhkZEzziaJcHibpNhDdOWZlAmRqrrnuZMyOPlPqvHRFaflaVVsZQQjtkQxnAMbLfjoDxpalJrKCzTdpNyPWCaiWspyuiWStcwwoSWBqGWfSICYxXrRbpzSrGIjhwTKCFpHxrTzAjmioBcyzZDMXNHAsLeixLtKFQliVdqlMHylkAKNiayAzeDKLAlmwyNLMQjLVMYUJpnuWJVEzJGDTFCNlxXBathpqHldHZqMpgumMHVmWMfjizabaestdPQSDzjNUVeYtVPQocsU,2008-01-01,10,13,,10,event-UKOkgCDKdxujJBBLnoYxfOQuVGIWbWUDVaXQumiRzbVVhhKpYL,9,fapiiketipuwhpubckdshuizggthcsuditntdnzevsyyhfnywz,5,2008-01-01T00:00:00.123456Z,,,project-KenthbnHZKFujOIEicLNIBPuQytkVYQSisavNTPjdHlovobKFB,0,Programme,1,sect-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx,1,Multilateral,11,,,11,,False,PQ,FCs,country-kQVicpmtDslqAnPgbtoQCTLAGVSRZQzYIbcJYPuTTjKryWLdjZ,1,Country,11,society-name-eDqmctnudjoIYYxdkkJNrBzvlCWvUWWkmmiHjNYoaibivzKgnn,"CefuMjeirN, QWBUdsMtwg","1, 2","False, True","False, True","district-hQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRgFT, district-gYShPPXJUnBCoAvDzAUguBuQqxjREefffBgVVxZiJdLJJvQhAw",0,0,0,0,5,2008-01-01T00:00:00.123456Z,5,2008-01-01T00:00:00.123456Z,regional-project-EQxpOaCNAAgHBKvEjWWPUPXsatpYtFqhTkuoeQmEQNuzgadFFF,10,,,,,,10,,False,EG,rSR,country-eItONgoPvNNlIwwWWpxRKvjcxyecdAFKKaPbzKBJdeIyTCEqcX,2,Cluster,10,society-name-iTnQmKstLSxobazFDyWkvuankOwaeFnyuqizlsgDIqlLdOlQKS,"1, 2","sect-tag-RoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSx, sect-tag-CCpxgRxIPwdzrmhDfQnPOMbdYvpiYKneWJnLnovXjYMarjiIqZ",2008-01-01,1,Ongoing,0,0,0,0,9,public,Public\r
0,4720000,,,18,18,disaster-type-uynXdMpaXZEMzHQVvXNcPLBSQtxYLIDiOrUcJVNMlSgDEOXmvP,WfAzGeennNEmBCbESihEQoTsaTltiPkPkVrgSNHYUoZZdARplUpButagIgPYtsrksWJrjQQbkSrpZWxaSMtCAwSfhQVGBQevAraNZKsgtFwmNINTemDcutOitufRONdGlyeQXebPmuyuNrlVKLlcOlpEyTyBLQBMlXkKwooIyfKqfeOIYWmMRbNYoYYtirPOjsayBRlGVmrAmmZtRHIMopqnExgVHyBNqUcGBXZxZslspUJlyNiJvvbCrnvbKwkWJOHZNxMrEOapKBZMBsunuMgEzvcqDhZJHmacWLZLvriJGDnrsVUNPzQyHBBCLINLqDbASgDSPbBLdfqNCffbWnZHqYTCgvzEwABUuaPveIUGBbRgyFQsqKURlnsSnxNOBKHubruWbPvYAATKYoFvtciTVqlYJBeESILkvZChtcivdRpIuTFBVlWytGYeOAWWpHPsKpWVAJdQymuGwobUfbXfWjCJKyMvfZNPnaWsPGxjTFDwHyWE,2008-01-01,12,16,,12,event-hQjgoQNUTCqpUzMKauvJuwFYxLKtSXbIWrlKVaAMBKOdStwjHM,11,zibayeudyvadpocwrxccfzujcafoaqjetljdiwoobgrmeuznnk,6,2008-01-01T00:00:00.123456Z,,,project-dnyuAjdmVBnqtRsnOMqzGXMyVVTpogIeRjmoxCRAfETVdCohCt,1,Emergency Operation,1,sect-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx,1,Multilateral,13,,,13,,False,aZ,FCp,country-yTWMchdDLioEXjLJjyJMoorTGQBQtMDcpTucAFuDGNAHYUomvw,4,Country Office,13,society-name-VgXkZQnguvvOcRXuCRcwiPfHENMRVoHrTrqctxGIngetetEdPS,"CefuMjeirN, QWBUdsMtwg","1, 2","False, True","False, True","district-hQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRgFT, district-gYShPPXJUnBCoAvDzAUguBuQqxjREefffBgVVxZiJdLJJvQhAw",0,0,0,0,6,2008-01-01T00:00:00.123456Z,6,2008-01-01T00:00:00.123456Z,regional-project-ScGNJMFFqYFXxNrRsPpsGTviLwmCVDYqbWYpEyDAJEsbqjbEAD,12,,,,,,12,,False,ue,aSE,country-doAfWKWQlcjSvNVLMUeLmHEmnDcmtUlZstrCsJMaXrFBbCVIAi,2,Cluster,12,society-name-AueXWMeYEOcSJXwfESpQkILwfrwymqcMeJYwGawwIVfUVZguCq,"1, 2","sect-tag-RoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSx, sect-tag-CCpxgRxIPwdzrmhDfQnPOMbdYvpiYKneWJnLnovXjYMarjiIqZ",2008-01-01,1,Ongoing,0,0,0,0,10,public,Public\r
0,6670000,,,21,21,disaster-type-XvlEjHDVybUpjaGECJorCfVaAlQIoorOOwWWOTxEpvBlmPiZCF,PTXcdqvnvHwTLEndiXDoVOQikJwZCbtTkYqcWUjvvvsAHMUYSRoLYCDPcsggAEJIexYLAOYszPDoHzYvyMatrGQqVQBFVonlTlNeSksIMvwIDSCbaQBkpRNquLLRrkArcFAbOJMundfiTdopKGbShpUGFfWyjIopwBJNduJXecIRbhxnnDrZmuzDbiOPCFkGXDeuyxMBQNxDSLQswFvKvNKxxbvuPpSOyiKTOfChtGxseJoNwkSuiVQxjZdDQXHPGkXWezPugeNOTlftxFsTsujdZncYZQiEOyWNqDmbGUXJjtdmUxRplUfYkVssaVSlLmXBosPYYbKqflZTfJcxTQkwEKuLKdTbsEMqfiZPpjutAafJMfYhnZtVUoqZGTxEemnMXRNBSlDBIAflFpsihXhjbXkNfSTnGfocfsLtJckNHMdJIPHTeLyRAtZxkmhKgRKLcGjeQnmuzJUSngCjoWBOzFdtTSeEfaPnSJKfNhGYWEscubhp,2008-01-01,14,19,,14,event-sMJnADfqyEqKcByHGUACxeJvWFgfBtwBcwQMYxzntpWfGdOPCn,13,ljbuciwhwbvwynpxeteeypbrmgyfsjeglykagxsjerjagjqqdi,7,2008-01-01T00:00:00.123456Z,,,project-UnYkbWprZqLxBbFeqHEXzwdTFDwWTjwTPDjoeyWVnhzbmQFPGU,0,Programme,1,sect-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx,0,Bilateral,15,,,15,,False,qQ,Hpm,country-ehHgZXSIQWSvfnyCmGbRvjdnJPPIgSLnCUBGtXgIXrFfqyQikb,1,Country,15,society-name-purdghlCkInyamaGEXzsDEcUKaAQQEBgIpXDyjVMxaEAPESeOA,"CefuMjeirN, QWBUdsMtwg","1, 2","False, True","False, True","district-hQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRgFT, district-gYShPPXJUnBCoAvDzAUguBuQqxjREefffBgVVxZiJdLJJvQhAw",0,0,0,0,7,2008-01-01T00:00:00.123456Z,7,2008-01-01T00:00:00.123456Z,regional-project-DbawMMrzMzzRMpTiXpnSDdbFgVRuHaYbLFerPdJAmplntnbZWz,14,,,,,,14,,False,Ri,ABc,country-mtfeuWEXnPXndNLdYcPTcKrVcYAxzwUGjpVsUqvpHZvPQBxpvl,2,Cluster,14,society-name-ORQWacqDbKVfedVptLWQxAefMSWMGKLVzuffJgRuGnVCYrzBet,"1, 2","sect-tag-RoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSx, sect-tag-CCpxgRxIPwdzrmhDfQnPOMbdYvpiYKneWJnLnovXjYMarjiIqZ",2008-01-01,1,Ongoing,0,0,0,0,11,public,Public\r
0,9480000,,,24,24,disaster-type-QGfLROCZnxqYYsiwlrTSEFFEqsXrKyqYLpctBsZddBayKIGiyt,IBiVQDxZxZnFDLoYJwPsPZybLgihbqbDkxqZwUmMBcfWBdKNojOVqDbCKjzixQYgTEsmhRzXdnixdPoVRSXLtpROMGHqrjDJKwjRpBfYFLqKAUqvZtMSVwTNwDUGhlCUmUgFTsRUQZjCUgHoijRrbknMnzQiEygDArTbXQrcrUyvQxgfkJyoGfhbwaiTZiITMkcEXPsROvLwkYHTiCXAFEYrlnNnuSqnWoODmUYiTCHnMAXVLlfwhcaiyaFCWkeqmOOqSHyKQYyYvnFexwEphbwlaJKJmeJDobQZKxdENnoDCogiNEmrfVtHvdXkRSDQxMOSbHjAITbaMdEjlbJPOEfkWhHLWrwlpMPSuKAXcipneuZNXNHUDwhDxCYNbmkmaJHIdYBaMseDvakYUrhobdCGOIBFPwHSYFuvRIvaLvKWgtvcsNClpzANsRziClGBvgIhsXSictYoPJrWQucRSqzjgFyqQmsMmKsgBYTWyCqcCJRJRSAK,2008-01-01,16,22,,16,event-VjrTvORupHgxfIkFjRmWGiBriLwgGvlxxPDRAXHYHQUfvvLcpd,15,ghkbuunvtqvgdygrzvatwsgjslvhtuvbgkipqsatscpvbcamxw,8,2008-01-01T00:00:00.123456Z,,,project-GVSxIuCrNeWfdzPZBDPjBsfGCNpPLCINunDEdekrKnhBVrwRQM,0,Programme,1,sect-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx,2,Domestic,17,,,17,,False,Wd,nYB,country-mdluwLVGXFLUidBYjohYsQvMBJQSGSMgbLTyOgKWzJdswbwkfe,2,Cluster,17,society-name-aHhzYrXgSJXaqqVYZAcISeSNFgqcZXJprBKuqrKwbzaLRZVvGc,"CefuMjeirN, QWBUdsMtwg","1, 2","False, True","False, True","district-hQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRgFT, district-gYShPPXJUnBCoAvDzAUguBuQqxjREefffBgVVxZiJdLJJvQhAw",0,0,0,0,8,2008-01-01T00:00:00.123456Z,8,2008-01-01T00:00:00.123456Z,regional-project-OLmyweZGCxzYLlBSLiWdXXoQUkEnvXFhjxyElejpabJXvDQGKw,16,,,,,,16,,False,JT,Fmz,country-SHJmNPkpDvMUaKFljHuISjRxJvVrwuhnNXhKAYbntHkXWpBFIJ,2,Cluster,16,society-name-KOmjpIbcqSpAqCxHtAAZrHBVETrgzoFXficzogDvwkKCEzchqw,"1, 2","sect-tag-RoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSx, sect-tag-CCpxgRxIPwdzrmhDfQnPOMbdYvpiYKneWJnLnovXjYMarjiIqZ",2008-01-01,1,Ongoing,0,0,0,0,12,public,Public\r
0,6480000,,,27,27,disaster-type-CUVyFnuUaEJWfVdQFlHSoPMtZDyrUAVRelRyfqNSOYMnQzQpgX,KzlCvzStqoLWcLueOMvzznbdPzmyjThYdwReyqdCGDVZTPdtGgfnVPxWWmSUEVOQOpMAxkEOkWZMuLVIzCDESdvxtHLLTXcEflSLMyMWMgusTJlEadQiKpnXSgnizGKmEqAbkepBWIIsexFEfSiVMeHrlSOPxeULwYAWfEBQxvJMkjoSxxiSIuJFQbBmaYQjXjJXTlMoZpwjICHNFgxUmwZMPAtFkAHQtVFrArRxucDRjHpgWahJwURdHIdIEuzVtwWbVRvIhPauHagaJPJRAFMFZqqFBfLnCIZXUJBymyYOsyWvpootCCrVKAomEKjjYSBkGhNewalnFsnJOFpsudukhMsauOaqEiWAbNEPKBkMerwLFCpAybKIWVuLhMJfCWtFUoyBxnNCPHHwHCZtGVMRRwPxChphZONIqqqYUMyeBpKulvEqEEErpCOkfjoGrGDCxyeYNfJWKHEvxFLQIoiUlMcOXbduLauswVhCoyuJxscuUKeK,2008-01-01,18,25,,18,event-dDYeiSXzvjsNsYIMeGwkZUMGpGGkaTeuhrLDCFArKfpzUfAwCA,17,wigkitzwygkpuqrtkqbiktjqlxsmqvqvudezazeupiibvovbxv,9,2008-01-01T00:00:00.123456Z,,,project-ortlsAiQVEgimNopdXWAvpmxYmTxNEuLQIbKzZkGlUThMzaHFJ,1,Emergency Operation,1,sect-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx,1,Multilateral,19,,,19,,False,Ot,IRf,country-NMcxbltczueeREOTrEZeUfDdQzrIwZCKBGJzmOQfkYYqdCVQMb,3,Region,19,society-name-pIQHhKdhgWrvSAFYSzDCAeLvirKzVbgEcKjYgCBtveEDWZcijQ,"CefuMjeirN, QWBUdsMtwg","1, 2","False, True","False, True","district-hQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRgFT, district-gYShPPXJUnBCoAvDzAUguBuQqxjREefffBgVVxZiJdLJJvQhAw",0,0,0,0,9,2008-01-01T00:00:00.123456Z,9,2008-01-01T00:00:00.123456Z,regional-project-DoLPGUpByAbKFQKFGZuvaYWdRPsrxQcCTiMzkNUXVbRfbCNoTl,18,,,,,,18,,False,VF,ZcB,country-TtlvXyybaLIYUavFZInAPMcSnbmrepOzvPmiLGuBUIrNRMCUZC,1,Country,18,society-name-cbFrygrYppCcdYrULfUQFtsmyJCfQUOypGSDBlfwETFZtaVuqx,"1, 2","sect-tag-RoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSx, sect-tag-CCpxgRxIPwdzrmhDfQnPOMbdYvpiYKneWJnLnovXjYMarjiIqZ",2008-01-01,1,Ongoing,0,0,0,0,13,public,Public\r
0,5950000,,,30,30,disaster-type-diRngieFHhCYWbtlTpiFuHIJffIuNZkbAnbqhywiDkzfJKgaKw,ogcbeDMQlWueozOkjmIPbenQCclbKPJfMtaeWryNyfTpzcDFjFkcOVsxdSTKJaBVnSRwopnxbhzTlAiuectKryhFpcxQeZUvgnoQibLzCmdLYjsaEtfOmvKORAAvppKdoYyoQHxErmoMgLuGbSabYJtgzjRyFxcfTtBHpPhrzxaYboKqXOxxGTRUTsyVsPkdgGgWPMbinkagywgMHJMazVbMhFXwcDvhVLkyDEOwZbrzgzPkQjROGOsmUMRBwBIVOJWOFYkajaqJFfboyYRvosFyWsfqsYjUTVEhRLCsvnesxLxwaJddjONbBULwtEmuBqiZCSiLqnAOfcYNbKHkqudPHhqTBQtCcjmAaCshFdYBaklxkvumQQfmqVfCAllIbKwteFxrRcgypCNcwXJrJkJhCmNnnWNVzNOgbWWIkZLBPQwBgiZdYysyrUAEyqDJwykvdJqwdVRePtpYKLKjwDaLLkGBhajHwOvWgqpHRjuRvjaplRUI,2008-01-01,20,28,,20,event-dfuVpeThKuNOAdjEzMXmZSrYWFFMBAduqGvyjuEwarkltzqWdy,19,lqqvsgawhxuwfvqgvhkfxfgyhtjjygydxjbekfqyvwfcjkzfvj,10,2008-01-01T00:00:00.123456Z,,,project-WAvKhIWhKYHcXwlHnZMXcvmaBFoaUQIoZdoJHsbgVBOEDYzLjS,0,Programme,1,sect-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx,2,Domestic,21,,,21,,False,zG,dzn,country-SEZudqaYKnEbfVhHuNzJKSCrPbVNwkKbuUYQwcMwEKjGeHrCUj,4,Country Office,21,society-name-VMMOlseBOgfMwrcZSUUOYylVFGPNbGIVVPdzGZmfWhjQhDLvMi,"CefuMjeirN, QWBUdsMtwg","1, 2","False, True","False, True","district-hQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRgFT, district-gYShPPXJUnBCoAvDzAUguBuQqxjREefffBgVVxZiJdLJJvQhAw",0,0,0,0,10,2008-01-01T00:00:00.123456Z,10,2008-01-01T00:00:00.123456Z,regional-project-FsWtwTrbBLhtpGDZBEnJPtphXSOuVZxAFBMuMDNkKylVAokTEn,20,,,,,,20,,False,SJ,Zax,country-kwsypbvNtQfVwBFheDCunLJXUYCkrZOuJfTLYJDQcGQGtaFvTu,2,Cluster,20,society-name-mVzvNOEjBHnNxcXDVSbwfZmcAMACleXiIguyJpJCYblEHvoCKJ,"1, 2","sect-tag-RoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSx, sect-tag-CCpxgRxIPwdzrmhDfQnPOMbdYvpiYKneWJnLnovXjYMarjiIqZ",2008-01-01,1,Ongoing,0,0,0,0,14,public,Public\r
'''

snapshots['TestProjectAPI::test_project_delete 1'] = b''

snapshots['TestProjectAPI::test_project_list_one 1'] = {
    'count': 1,
    'next': None,
    'previous': None,
    'results': [
        {
            'actual_expenditure': 0,
            'annual_split_detail': [
            ],
            'budget_amount': 9440000,
            'description': '',
            'document': None,
            'dtype': 3,
            'dtype_detail': {
                'id': 3,
                'name': 'disaster-type-TVJOnmnNTsRwRiTPlGISOuThWwJELKQTARVIsBZaHgbyjdQdmr',
                'summary': 'WYksRqjdSYsnWIcwCgNRVJoVPJypGYYZSsSQdyyAYRuJdaVqmNXCoOTTPxWLIVMmXUmsClRellVGhycBrJqikLqavDTjcjuMdXONQtFYKJweYTuHolHeYGkAIIzfwonQvvxsnWNHEJWPahQwCpPNNpcRuyYhyqIUsbHXxGZGCFcsPmuGfgkXIIaOenQOXnRBgnISVXBPeVRjbDTvcfedlYqJeKoqAyCOzBubyRhIaPUNeWVLcSewGgsYRtMfsWCyzQbEkIoiVzYZIsOjtRYUPxaJJjhcaKMzIJftnVVUwnAPGjkloNqmhlQZKdWJDPJesQeqgmULFvwiQPpgsNemuFCvNQtSLjKKxZuBkaupYoTVPBrxiRUvEDCwXtFJglPMfriImqUOeUebGObLLzXLncJqIIEPXjxzoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYxyEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFY'
            },
            'end_date': '2008-01-01',
            'event': 2,
            'event_detail': {
                'countries_for_preview': [
                ],
                'dtype': 1,
                'emergency_response_contact_email': None,
                'id': 2,
                'name': 'event-xNooiEjDVMxASJEWIZQnWpRWMYfHCHTxeKhdJGmKIjkuHChRnT',
                'parent_event': 1,
                'slug': 'lffgczddigadkdjdrztubzqavnlecbwseideecsalxixpupaxy'
            },
            'id': 1,
            'modified_at': '2008-01-01T00:00:00.123456Z',
            'modified_by': None,
            'modified_by_detail': None,
            'name': 'project-EMaGiCkoeGPrnjlkxMThQoAZvUhEREEnLkPAbpciKLkiOGcKjd',
            'operation_type': 1,
            'operation_type_display': 'Emergency Operation',
            'primary_sector': 1,
            'primary_sector_display': 'sect-OhbVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgf',
            'programme_type': 0,
            'programme_type_display': 'Bilateral',
            'project_country': 2,
            'project_country_detail': {
                'average_household_size': None,
                'fdrs': None,
                'id': 2,
                'independent': None,
                'is_deprecated': False,
                'iso': 'Cp',
                'iso3': 'xgR',
                'name': 'country-oEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSxn',
                'record_type': 4,
                'record_type_display': 'Country Office',
                'region': 2,
                'society_name': 'society-name-xIPwdzrmhDfQnPOMbdYvpiYKneWJnLnovXjYMarjiIqZlhQbia'
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
                'created_at': '2008-01-01T00:00:00.123456Z',
                'id': 1,
                'modified_at': '2008-01-01T00:00:00.123456Z',
                'name': 'regional-project-koAMjYLXlNQGqkURvDMLeoyyigbmHGRAjMglENMcYIGWhfEQiM'
            },
            'reporting_ns': 1,
            'reporting_ns_contact_email': None,
            'reporting_ns_contact_name': None,
            'reporting_ns_contact_role': None,
            'reporting_ns_detail': {
                'average_household_size': None,
                'fdrs': None,
                'id': 1,
                'independent': None,
                'is_deprecated': False,
                'iso': 'yr',
                'iso3': 'OSJ',
                'name': 'country-wMqZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkIUpk',
                'record_type': 4,
                'record_type_display': 'Country Office',
                'region': 1,
                'society_name': 'society-name-oRuXXdocZuzrenKTunPFzPDjqipVJIqVLBLzxoiGFfWdhjOkYR'
            },
            'secondary_sectors': [
            ],
            'secondary_sectors_display': [
            ],
            'start_date': '2008-01-01',
            'status': 1,
            'status_display': 'Ongoing',
            'target_female': 0,
            'target_male': 0,
            'target_other': 0,
            'target_total': 0,
            'user': 5,
            'visibility': 'public',
            'visibility_display': 'Public'
        }
    ]
}

snapshots['TestProjectAPI::test_project_list_two 1'] = {
    'count': 2,
    'next': None,
    'previous': None,
    'results': [
        {
            'actual_expenditure': 0,
            'annual_split_detail': [
            ],
            'budget_amount': 9440000,
            'description': '',
            'document': None,
            'dtype': 3,
            'dtype_detail': {
                'id': 3,
                'name': 'disaster-type-TVJOnmnNTsRwRiTPlGISOuThWwJELKQTARVIsBZaHgbyjdQdmr',
                'summary': 'WYksRqjdSYsnWIcwCgNRVJoVPJypGYYZSsSQdyyAYRuJdaVqmNXCoOTTPxWLIVMmXUmsClRellVGhycBrJqikLqavDTjcjuMdXONQtFYKJweYTuHolHeYGkAIIzfwonQvvxsnWNHEJWPahQwCpPNNpcRuyYhyqIUsbHXxGZGCFcsPmuGfgkXIIaOenQOXnRBgnISVXBPeVRjbDTvcfedlYqJeKoqAyCOzBubyRhIaPUNeWVLcSewGgsYRtMfsWCyzQbEkIoiVzYZIsOjtRYUPxaJJjhcaKMzIJftnVVUwnAPGjkloNqmhlQZKdWJDPJesQeqgmULFvwiQPpgsNemuFCvNQtSLjKKxZuBkaupYoTVPBrxiRUvEDCwXtFJglPMfriImqUOeUebGObLLzXLncJqIIEPXjxzoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYxyEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFY'
            },
            'end_date': '2008-01-01',
            'event': 2,
            'event_detail': {
                'countries_for_preview': [
                ],
                'dtype': 1,
                'emergency_response_contact_email': None,
                'id': 2,
                'name': 'event-xNooiEjDVMxASJEWIZQnWpRWMYfHCHTxeKhdJGmKIjkuHChRnT',
                'parent_event': 1,
                'slug': 'lffgczddigadkdjdrztubzqavnlecbwseideecsalxixpupaxy'
            },
            'id': 1,
            'modified_at': '2008-01-01T00:00:00.123456Z',
            'modified_by': None,
            'modified_by_detail': None,
            'name': 'project-EMaGiCkoeGPrnjlkxMThQoAZvUhEREEnLkPAbpciKLkiOGcKjd',
            'operation_type': 1,
            'operation_type_display': 'Emergency Operation',
            'primary_sector': 1,
            'primary_sector_display': 'sect-OhbVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgf',
            'programme_type': 0,
            'programme_type_display': 'Bilateral',
            'project_country': 2,
            'project_country_detail': {
                'average_household_size': None,
                'fdrs': None,
                'id': 2,
                'independent': None,
                'is_deprecated': False,
                'iso': 'Cp',
                'iso3': 'xgR',
                'name': 'country-oEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSxn',
                'record_type': 4,
                'record_type_display': 'Country Office',
                'region': 2,
                'society_name': 'society-name-xIPwdzrmhDfQnPOMbdYvpiYKneWJnLnovXjYMarjiIqZlhQbia'
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
                'created_at': '2008-01-01T00:00:00.123456Z',
                'id': 1,
                'modified_at': '2008-01-01T00:00:00.123456Z',
                'name': 'regional-project-koAMjYLXlNQGqkURvDMLeoyyigbmHGRAjMglENMcYIGWhfEQiM'
            },
            'reporting_ns': 1,
            'reporting_ns_contact_email': None,
            'reporting_ns_contact_name': None,
            'reporting_ns_contact_role': None,
            'reporting_ns_detail': {
                'average_household_size': None,
                'fdrs': None,
                'id': 1,
                'independent': None,
                'is_deprecated': False,
                'iso': 'yr',
                'iso3': 'OSJ',
                'name': 'country-wMqZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkIUpk',
                'record_type': 4,
                'record_type_display': 'Country Office',
                'region': 1,
                'society_name': 'society-name-oRuXXdocZuzrenKTunPFzPDjqipVJIqVLBLzxoiGFfWdhjOkYR'
            },
            'secondary_sectors': [
            ],
            'secondary_sectors_display': [
            ],
            'start_date': '2008-01-01',
            'status': 1,
            'status_display': 'Ongoing',
            'target_female': 0,
            'target_male': 0,
            'target_other': 0,
            'target_total': 0,
            'user': 5,
            'visibility': 'public',
            'visibility_display': 'Public'
        },
        {
            'actual_expenditure': 0,
            'annual_split_detail': [
            ],
            'budget_amount': 6090000,
            'description': '',
            'document': None,
            'dtype': 6,
            'dtype_detail': {
                'id': 6,
                'name': 'disaster-type-blCoqPewfsGGIPfYroghexcImvmRvqtVXRrmTMiWTVIqaXtswY',
                'summary': 'zzLWPaEPGWjzooUVnEoHLYJWDUDvYfumBXSAnCCJbxiKitVaFZQwvoABRWzWXSItuLbKYcijvKOZMMKzynzeIymEgvKCOtfkgRJlcSMFblmeysnosQHeDdxHakuAzkhiIAEVeynintBTQEkMKtLmGTRDrmajCezMZpHvKFDDKcVfsPDwSTYtzNZlAplNUBDyQlSKgzScpkrOIsQeSUUnFAWJhxeWgGXXuACkqnGcDbeOSRVDyvVzmzcaqhTiuQVDFDefJQpTCiErkkbMglshIVzkeQWaRrjCwlnTcRInCSdOZHPQTQgyStCdMadXyXmpxpmfbAbavmRQeogZQkUkcAGguuJOmNnIzBhongwulazPuaynDoeQrPNxcenAtXMFgTIYKkqgMuOSyRXSivlOWSuQEevbMLCyGOVoGLTaobNWhtpVBWpNfdixFsmjynPcpUMCVviruPYWcHYAPsWboUvvpnIdQpZRSUoMyHulCOaeFemdOjni'
            },
            'end_date': '2008-01-01',
            'event': 4,
            'event_detail': {
                'countries_for_preview': [
                ],
                'dtype': 4,
                'emergency_response_contact_email': None,
                'id': 4,
                'name': 'event-ZoHPvALvPPYuFLQSHJCDtKiYtkYqoExsXdjwsDkNkTIsllTSQY',
                'parent_event': 3,
                'slug': 'jkphcukicqxlnjtcquwjxcikithbzfxjdujavigvptseswkqjz'
            },
            'id': 2,
            'modified_at': '2008-01-01T00:00:00.123456Z',
            'modified_by': None,
            'modified_by_detail': None,
            'name': 'project-flLJYnpGfBUDtkUmpBlMptsKCOmrYEfxzykECBGNVBWjYEbWyB',
            'operation_type': 1,
            'operation_type_display': 'Emergency Operation',
            'primary_sector': 1,
            'primary_sector_display': 'sect-OhbVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgf',
            'programme_type': 0,
            'programme_type_display': 'Bilateral',
            'project_country': 4,
            'project_country_detail': {
                'average_household_size': None,
                'fdrs': None,
                'id': 4,
                'independent': None,
                'is_deprecated': False,
                'iso': 'NO',
                'iso3': 'Jnd',
                'name': 'country-kvKQjkjlXTdAttUXCsOlhimaNWqaDFFIZaMFpnLQEDACfMMapJ',
                'record_type': 3,
                'record_type_display': 'Region',
                'region': 4,
                'society_name': 'society-name-ljdPwcjcQKMtvfdgAlkRsNQSSMKYJlDVLxcfXtuxyeWBJesEih'
            },
            'project_districts': [
            ],
            'project_districts_detail': [
            ],
            'reached_female': 0,
            'reached_male': 0,
            'reached_other': 0,
            'reached_total': 0,
            'regional_project': 2,
            'regional_project_detail': {
                'created_at': '2008-01-01T00:00:00.123456Z',
                'id': 2,
                'modified_at': '2008-01-01T00:00:00.123456Z',
                'name': 'regional-project-JMEeviTEmjmaaGUUxFzAzVxyFtPLeAchyKkmWBqXWUwGTFOSxS'
            },
            'reporting_ns': 3,
            'reporting_ns_contact_email': None,
            'reporting_ns_contact_name': None,
            'reporting_ns_contact_role': None,
            'reporting_ns_detail': {
                'average_household_size': None,
                'fdrs': None,
                'id': 3,
                'independent': None,
                'is_deprecated': False,
                'iso': 'Ax',
                'iso3': 'gjB',
                'name': 'country-BHAxcSHBoZEYXywLZVWSKgBiqEXofsMIAqmaTVYaKHhHayPnSZ',
                'record_type': 3,
                'record_type_display': 'Region',
                'region': 3,
                'society_name': 'society-name-PLqqIBKxNrRzWnAJYJElxJJEqtKwXTzViQhVoCYSkgnGzYvZJN'
            },
            'secondary_sectors': [
            ],
            'secondary_sectors_display': [
            ],
            'start_date': '2008-01-01',
            'status': 1,
            'status_display': 'Ongoing',
            'target_female': 0,
            'target_male': 0,
            'target_other': 0,
            'target_total': 0,
            'user': 6,
            'visibility': 'public',
            'visibility_display': 'Public'
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

snapshots['TestProjectAPI::test_project_read 1'] = {
    'actual_expenditure': 0,
    'annual_split_detail': [
    ],
    'budget_amount': 9440000,
    'description': '',
    'document': None,
    'dtype': 3,
    'dtype_detail': {
        'id': 3,
        'name': 'disaster-type-TVJOnmnNTsRwRiTPlGISOuThWwJELKQTARVIsBZaHgbyjdQdmr',
        'summary': 'WYksRqjdSYsnWIcwCgNRVJoVPJypGYYZSsSQdyyAYRuJdaVqmNXCoOTTPxWLIVMmXUmsClRellVGhycBrJqikLqavDTjcjuMdXONQtFYKJweYTuHolHeYGkAIIzfwonQvvxsnWNHEJWPahQwCpPNNpcRuyYhyqIUsbHXxGZGCFcsPmuGfgkXIIaOenQOXnRBgnISVXBPeVRjbDTvcfedlYqJeKoqAyCOzBubyRhIaPUNeWVLcSewGgsYRtMfsWCyzQbEkIoiVzYZIsOjtRYUPxaJJjhcaKMzIJftnVVUwnAPGjkloNqmhlQZKdWJDPJesQeqgmULFvwiQPpgsNemuFCvNQtSLjKKxZuBkaupYoTVPBrxiRUvEDCwXtFJglPMfriImqUOeUebGObLLzXLncJqIIEPXjxzoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYxyEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFY'
    },
    'end_date': '2008-01-01',
    'event': 2,
    'event_detail': {
        'countries_for_preview': [
        ],
        'dtype': 1,
        'emergency_response_contact_email': None,
        'id': 2,
        'name': 'event-xNooiEjDVMxASJEWIZQnWpRWMYfHCHTxeKhdJGmKIjkuHChRnT',
        'parent_event': 1,
        'slug': 'lffgczddigadkdjdrztubzqavnlecbwseideecsalxixpupaxy'
    },
    'id': 1,
    'modified_at': '2008-01-01T00:00:00.123456Z',
    'modified_by': None,
    'modified_by_detail': None,
    'name': 'project-EMaGiCkoeGPrnjlkxMThQoAZvUhEREEnLkPAbpciKLkiOGcKjd',
    'operation_type': 1,
    'operation_type_display': 'Emergency Operation',
    'primary_sector': 1,
    'primary_sector_display': 'sect-OhbVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgf',
    'programme_type': 0,
    'programme_type_display': 'Bilateral',
    'project_country': 2,
    'project_country_detail': {
        'average_household_size': None,
        'fdrs': None,
        'id': 2,
        'independent': None,
        'is_deprecated': False,
        'iso': 'Cp',
        'iso3': 'xgR',
        'name': 'country-oEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSxn',
        'record_type': 4,
        'record_type_display': 'Country Office',
        'region': 2,
        'society_name': 'society-name-xIPwdzrmhDfQnPOMbdYvpiYKneWJnLnovXjYMarjiIqZlhQbia'
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
        'created_at': '2008-01-01T00:00:00.123456Z',
        'id': 1,
        'modified_at': '2008-01-01T00:00:00.123456Z',
        'name': 'regional-project-koAMjYLXlNQGqkURvDMLeoyyigbmHGRAjMglENMcYIGWhfEQiM'
    },
    'reporting_ns': 1,
    'reporting_ns_contact_email': None,
    'reporting_ns_contact_name': None,
    'reporting_ns_contact_role': None,
    'reporting_ns_detail': {
        'average_household_size': None,
        'fdrs': None,
        'id': 1,
        'independent': None,
        'is_deprecated': False,
        'iso': 'yr',
        'iso3': 'OSJ',
        'name': 'country-wMqZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkIUpk',
        'record_type': 4,
        'record_type_display': 'Country Office',
        'region': 1,
        'society_name': 'society-name-oRuXXdocZuzrenKTunPFzPDjqipVJIqVLBLzxoiGFfWdhjOkYR'
    },
    'secondary_sectors': [
    ],
    'secondary_sectors_display': [
    ],
    'start_date': '2008-01-01',
    'status': 1,
    'status_display': 'Ongoing',
    'target_female': 0,
    'target_male': 0,
    'target_other': 0,
    'target_total': 0,
    'user': 5,
    'visibility': 'public',
    'visibility_display': 'Public'
}

snapshots['TestProjectAPI::test_project_update 1'] = {
    'actual_expenditure': 0,
    'annual_split_detail': [
    ],
    'budget_amount': 9440000,
    'description': '',
    'document': None,
    'dtype': 3,
    'dtype_detail': {
        'id': 3,
        'name': 'disaster-type-TVJOnmnNTsRwRiTPlGISOuThWwJELKQTARVIsBZaHgbyjdQdmr',
        'summary': 'WYksRqjdSYsnWIcwCgNRVJoVPJypGYYZSsSQdyyAYRuJdaVqmNXCoOTTPxWLIVMmXUmsClRellVGhycBrJqikLqavDTjcjuMdXONQtFYKJweYTuHolHeYGkAIIzfwonQvvxsnWNHEJWPahQwCpPNNpcRuyYhyqIUsbHXxGZGCFcsPmuGfgkXIIaOenQOXnRBgnISVXBPeVRjbDTvcfedlYqJeKoqAyCOzBubyRhIaPUNeWVLcSewGgsYRtMfsWCyzQbEkIoiVzYZIsOjtRYUPxaJJjhcaKMzIJftnVVUwnAPGjkloNqmhlQZKdWJDPJesQeqgmULFvwiQPpgsNemuFCvNQtSLjKKxZuBkaupYoTVPBrxiRUvEDCwXtFJglPMfriImqUOeUebGObLLzXLncJqIIEPXjxzoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYxyEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFY'
    },
    'end_date': '2008-01-01',
    'event': 2,
    'event_detail': {
        'countries_for_preview': [
        ],
        'dtype': 1,
        'emergency_response_contact_email': None,
        'id': 2,
        'name': 'event-xNooiEjDVMxASJEWIZQnWpRWMYfHCHTxeKhdJGmKIjkuHChRnT',
        'parent_event': 1,
        'slug': 'lffgczddigadkdjdrztubzqavnlecbwseideecsalxixpupaxy'
    },
    'id': 1,
    'modified_at': '2008-01-01T00:00:00.123456Z',
    'modified_by': 3,
    'modified_by_detail': {
        'email': 'jon@dave.com',
        'first_name': 'Jon',
        'id': 3,
        'last_name': 'Mon',
        'username': 'jon@dave.com'
    },
    'name': 'Mock Project for Update API Test',
    'operation_type': 1,
    'operation_type_display': 'Emergency Operation',
    'primary_sector': 1,
    'primary_sector_display': 'sect-OhbVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgf',
    'programme_type': 0,
    'programme_type_display': 'Bilateral',
    'project_country': 3,
    'project_country_detail': {
        'average_household_size': None,
        'fdrs': None,
        'id': 3,
        'independent': None,
        'is_deprecated': False,
        'iso': 'Ax',
        'iso3': 'gjB',
        'name': 'country-RPBHAxcSHBoZEYXywLZVWSKgBiqEXofsMIAqmaTVYaKHhHayPn',
        'record_type': 3,
        'record_type_display': 'Region',
        'region': 3,
        'society_name': 'society-name-PLqqIBKxNrRzWnAJYJElxJJEqtKwXTzViQhVoCYSkgnGzYvZJN'
    },
    'project_districts': [
        1
    ],
    'project_districts_detail': [
        {
            'code': 'rNOJndljdP',
            'id': 1,
            'is_deprecated': True,
            'is_enclave': False,
            'name': 'district-kvKQjkjlXTdAttUXCsOlhimaNWqaDFFIZaMFpnLQEDACfMMapJ'
        }
    ],
    'reached_female': 0,
    'reached_male': 0,
    'reached_other': 0,
    'reached_total': 0,
    'regional_project': 1,
    'regional_project_detail': {
        'created_at': '2008-01-01T00:00:00.123456Z',
        'id': 1,
        'modified_at': '2008-01-01T00:00:00.123456Z',
        'name': 'regional-project-koAMjYLXlNQGqkURvDMLeoyyigbmHGRAjMglENMcYIGWhfEQiM'
    },
    'reporting_ns': 3,
    'reporting_ns_contact_email': None,
    'reporting_ns_contact_name': None,
    'reporting_ns_contact_role': None,
    'reporting_ns_detail': {
        'average_household_size': None,
        'fdrs': None,
        'id': 3,
        'independent': None,
        'is_deprecated': False,
        'iso': 'Ax',
        'iso3': 'gjB',
        'name': 'country-RPBHAxcSHBoZEYXywLZVWSKgBiqEXofsMIAqmaTVYaKHhHayPn',
        'record_type': 3,
        'record_type_display': 'Region',
        'region': 3,
        'society_name': 'society-name-PLqqIBKxNrRzWnAJYJElxJJEqtKwXTzViQhVoCYSkgnGzYvZJN'
    },
    'secondary_sectors': [
    ],
    'secondary_sectors_display': [
    ],
    'start_date': '2008-01-01',
    'status': 1,
    'status_display': 'Ongoing',
    'target_female': 0,
    'target_male': 0,
    'target_other': 0,
    'target_total': 0,
    'user': 5,
    'visibility': 'public',
    'visibility_display': 'Public'
}
