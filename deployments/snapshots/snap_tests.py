# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestProjectAPI::test_personnel_csv_api 1'] = '''deployedperson-id,country-from.iso3,country-from.name,country-from.region,country-from.society-name,country-to.iso3,country-to.name,country-to.region,country-to.society-name,deployment.event-deployed-to.countries.iso3,deployment.event-deployed-to.countries.name,deployment.event-deployed-to.countries.region,deployment.event-deployed-to.countries.society-name,disaster-type,deployment.event-deployed-to.glide,deployment.event-deployed-to.id,deployment.event-deployed-to.ifrc-severity-level,deployment.event-deployed-to.name,end-date,is-active,molnix-id,molnix-language,molnix-modality,molnix-operation,molnix-region,molnix-role-profile,molnix-scope,molnix-sector,molnix-status,name,role,start-date,type,ongoing,inactive-status\r
1,,,,,,,,,,,,,,,,,,,True,,,,,,,,,,,,,,True,\r
2,,,,,,,,,,,,,,,,,,,True,,,,,,,,,,,,,,True,\r
3,,,,,,,,,,,,,,,,,,,True,,,,,,,,,,,,,,True,\r
4,,,,,,,,,,,,,,,,,,,True,,,,,,,,,,,,,,True,\r
5,,,,,,,,,,,,,,,,,,,True,,,,,,,,,,,,,,True,\r
6,,,,,,,,,,,,,,,,,,,True,,,,,,,,,,,,,,True,\r
7,,,,,,,,,,,,,,,,,,,True,,,,,,,,,,,,,,True,\r
8,,,,,,,,,,,,,,,,,,,True,,,,,,,,,,,,,,True,\r
9,,,,,,,,,,,,,,,,,,,True,,,,,,,,,,,,,,True,\r
10,,,,,,,,,,,,,,,,,,,True,,,,,,,,,,,,,,True,\r
'''


snapshots['TestProjectAPI::test_global_project_api 1'] = {
    'ns_with_ongoing_activities': 16,
    'projects_per_programme_type': [
        {
            'count': 9,
            'programme_type': 0,
            'programme_type_display': 'Bilateral'
        },
        {
            'count': 4,
            'programme_type': 1,
            'programme_type_display': 'Multilateral'
        },
        {
            'count': 3,
            'programme_type': 2,
            'programme_type_display': 'Domestic'
        }
    ],
    'projects_per_secondary_sectors': [
        {
            'count': 8,
            'secondary_sector': '0',
            'secondary_sector_display': 'WASH'
        },
        {
            'count': 8,
            'secondary_sector': '1',
            'secondary_sector_display': 'PGI'
        },
        {
            'count': 4,
            'secondary_sector': '10',
            'secondary_sector_display': 'Recovery'
        },
        {
            'count': 4,
            'secondary_sector': '11',
            'secondary_sector_display': 'Internal displacement'
        },
        {
            'count': 4,
            'secondary_sector': '3',
            'secondary_sector_display': 'Migration'
        },
        {
            'count': 4,
            'secondary_sector': '9',
            'secondary_sector_display': 'Livelihoods and basic needs'
        }
    ],
    'projects_per_sector': [
        {
            'count': 3,
            'primary_sector': 0,
            'primary_sector_display': 'WASH'
        },
        {
            'count': 1,
            'primary_sector': 1,
            'primary_sector_display': 'PGI'
        },
        {
            'count': 3,
            'primary_sector': 3,
            'primary_sector_display': 'Migration'
        },
        {
            'count': 3,
            'primary_sector': 5,
            'primary_sector_display': 'DRR'
        },
        {
            'count': 1,
            'primary_sector': 6,
            'primary_sector_display': 'Shelter'
        },
        {
            'count': 1,
            'primary_sector': 7,
            'primary_sector_display': 'NS Strengthening'
        },
        {
            'count': 3,
            'primary_sector': 8,
            'primary_sector_display': 'Education'
        },
        {
            'count': 1,
            'primary_sector': 9,
            'primary_sector_display': 'Livelihoods and basic needs'
        }
    ],
    'target_total': 0,
    'total_ongoing_projects': 16
}

snapshots['TestProjectAPI::test_global_project_api 2'] = {
    'results': [
        {
            'budget_amount_total': 9560000,
            'id': 5,
            'iso3': 'Pug',
            'name': 'country-XLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYxyE',
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
                    'primary_sector': 9,
                    'primary_sector_display': 'Livelihoods and basic needs'
                }
            ],
            'society_name': 'society-name-THOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjlkxMThQoA',
            'target_total': 0
        },
        {
            'budget_amount_total': 9100000,
            'id': 7,
            'iso3': 'nId',
            'name': 'country-oGLTaobNWhtpVBWpNfdixFsmjynPcpUMCVviruPYWcHYAPsWbo',
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
                    'primary_sector': 5,
                    'primary_sector_display': 'DRR'
                }
            ],
            'society_name': 'society-name-QpZRSUoMyHulCOaeFemdOjniflLJYnpGfBUDtkUmpBlMptsKCO',
            'target_total': 0
        },
        {
            'budget_amount_total': 1200000,
            'id': 9,
            'iso3': 'hVr',
            'name': 'country-tvTDQLHHKrWiuBxQjLVcVZyOdYmlajOcYpkzuaKEEwmOKzCnDN',
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
                    'primary_sector': 3,
                    'primary_sector_display': 'Migration'
                }
            ],
            'society_name': 'society-name-PXGvvlqvZFXJDQgQvWHqeYxBPbIigoDhhJTsiwtCBJfGlzGmjR',
            'target_total': 0
        },
        {
            'budget_amount_total': 150000,
            'id': 11,
            'iso3': 'JuI',
            'name': 'country-zOHivaKQuijMsyibLmSxwUyYeZVVPaZnTQKMwiXSLFbXgoDhjr',
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
                    'primary_sector': 8,
                    'primary_sector_display': 'Education'
                }
            ],
            'society_name': 'society-name-xytWinbqeVXjbjEdBhxNkEoJFrdkMNdCUUfBBLbAoiisHPgvuq',
            'target_total': 0
        },
        {
            'budget_amount_total': 7060000,
            'id': 13,
            'iso3': 'Nvo',
            'name': 'country-YksnSVShNIoKisIsGeobatgVBMZZeauocjgxeyEUxWZTJySszT',
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
                    'primary_sector': 6,
                    'primary_sector_display': 'Shelter'
                }
            ],
            'society_name': 'society-name-tJffaubhWrFAqXjFGZLYBhuEpJvuVWhiIXeCFvZgioLxWKFGgv',
            'target_total': 0
        },
        {
            'budget_amount_total': 460000,
            'id': 15,
            'iso3': 'tHB',
            'name': 'country-iuvNEEDjBuMFysbJmJxVIbubeTshXCgXyvEJLmKeiLwzwZfIIC',
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
                    'primary_sector': 5,
                    'primary_sector_display': 'DRR'
                }
            ],
            'society_name': 'society-name-cdPxXcaTMlqrMTOlHCJFwODdOoPbXjLmbhgUjvOaePGzOcFrkK',
            'target_total': 0
        },
        {
            'budget_amount_total': 6050000,
            'id': 17,
            'iso3': 'PJN',
            'name': 'country-VeiQGOKHLNUoaRFrygVhVpUKMWOEKMiDgOvSzdYonHRFVIHRwj',
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
                    'primary_sector': 3,
                    'primary_sector_display': 'Migration'
                }
            ],
            'society_name': 'society-name-GzGPgIXXqXpKDzSpdTKaPaEpFLsNLNYUPtYruDRPQqZtrhcCzL',
            'target_total': 0
        },
        {
            'budget_amount_total': 8290000,
            'id': 19,
            'iso3': 'NTS',
            'name': 'country-PhnjWOLpxCunHtYGOegfuTFcmtDxzdPfAsRkyltvusAkalhovT',
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
                    'primary_sector': 0,
                    'primary_sector_display': 'WASH'
                }
            ],
            'society_name': 'society-name-kjQpKsaFfWCpQsoryydZNvqERdUQdAdYYpKHedCKXwgzmvieqO',
            'target_total': 0
        },
        {
            'budget_amount_total': 5920000,
            'id': 21,
            'iso3': 'WNq',
            'name': 'country-FWJNPIGxPkqKRLeNzbOHsgUSwRJXvxmDTodTYrnDAnhHuxKzFb',
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
                    'primary_sector': 8,
                    'primary_sector_display': 'Education'
                }
            ],
            'society_name': 'society-name-qJTgrVtaadVUrcYCxAcjpXhdUBtXcCXMFkLAHVklUJGQvVYtjD',
            'target_total': 0
        },
        {
            'budget_amount_total': 5040000,
            'id': 23,
            'iso3': 'dFd',
            'name': 'country-pLvNPspuCIVYPruNbVEnSUhjHkeOgYelztOjgQGfuqqXFJGLnX',
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
                    'primary_sector': 0,
                    'primary_sector_display': 'WASH'
                }
            ],
            'society_name': 'society-name-xbCbNxPUbOziyQnlCzlqTQWmiBvCjaXFMHdqVFcEGNYVPpCMHF',
            'target_total': 0
        },
        {
            'budget_amount_total': 810000,
            'id': 25,
            'iso3': 'fYO',
            'name': 'country-rXPYckUybVlHPtYAwUvLjfTHLuyIGZzqNKnmQLCrwmMeIcloIs',
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
                    'primary_sector': 0,
                    'primary_sector_display': 'WASH'
                }
            ],
            'society_name': 'society-name-ttqoUToQRXCoyXPPcNdGvCvoXVDMtCzWngHTnPqlTKbaksLkPF',
            'target_total': 0
        },
        {
            'budget_amount_total': 7560000,
            'id': 27,
            'iso3': 'Bdp',
            'name': 'country-VniWFQHzzHBIQMKHtjbbolyZvdPoduiqggrWkcUCAxgZonvlKs',
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
                    'primary_sector_display': 'PGI'
                }
            ],
            'society_name': 'society-name-TOWKASebIrYORKkWTLEdtXunHBICzejSWKCAFyjhOmvtOuzWer',
            'target_total': 0
        },
        {
            'budget_amount_total': 8060000,
            'id': 29,
            'iso3': 'ELL',
            'name': 'country-QTqbSLbvtPttKBkPVxjhAwpJNDXZVnYLYRdDzyVzFwSjqPtlap',
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
                    'primary_sector': 7,
                    'primary_sector_display': 'NS Strengthening'
                }
            ],
            'society_name': 'society-name-FazwYJegirxWdYECJoBoucRZNAVGdgKijDhWXAAknMPowlAafD',
            'target_total': 0
        },
        {
            'budget_amount_total': 6730000,
            'id': 31,
            'iso3': 'IBB',
            'name': 'country-TtOYzaCmFldtcpOlRYtastbgkeCJvBTOnPWtmzervxcfkMbqpf',
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
                    'primary_sector': 8,
                    'primary_sector_display': 'Education'
                }
            ],
            'society_name': 'society-name-DCwyszNZGXQmypnWjcKsHVgAGwmfLLQMaSHEceWtyhGEdYOTkE',
            'target_total': 0
        },
        {
            'budget_amount_total': 5220000,
            'id': 33,
            'iso3': 'hNK',
            'name': 'country-lFoucligTrYZNfzfdSWfMLvoRjfavNEGPtQYlQIfZsPpOuhTPN',
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
                    'primary_sector': 5,
                    'primary_sector_display': 'DRR'
                }
            ],
            'society_name': 'society-name-DMYIfFApbQgMPVWggwrZnUhBSCdfQshatRJHibAqQwyjPObObN',
            'target_total': 0
        },
        {
            'budget_amount_total': 3510000,
            'id': 35,
            'iso3': 'Bnz',
            'name': 'country-NUBFklsXHvwhvOCcmqmsYKfCZeQddoPOvFOcvIoPoPYtLrpOFs',
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
                    'primary_sector': 3,
                    'primary_sector_display': 'Migration'
                }
            ],
            'society_name': 'society-name-JvnKNSlGzUnyLPRoqRfeZxiwArYgPzwdBsnTobwsdWUzKBxgrG',
            'target_total': 0
        }
    ]
}

snapshots['TestProjectAPI::test_project_create 1'] = {
    'actual_expenditure': 0,
    'budget_amount': 410000,
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
    'operation_type': 1,
    'operation_type_display': 'Emergency Operation',
    'primary_sector': 7,
    'primary_sector_display': 'NS Strengthening',
    'programme_type': 2,
    'programme_type_display': 'Domestic',
    'project_country': 1,
    'project_country_detail': {
        'average_household_size': None,
        'fdrs': None,
        'id': 1,
        'independent': None,
        'is_deprecated': False,
        'iso': 'oA',
        'iso3': 'MjY',
        'name': 'country-hQoAZvUhEREEnLkPAbpciKLkiOGcKjdkqlHzMKObUUQsfnCMEE',
        'record_type': 2,
        'record_type_display': 'Cluster',
        'region': 1,
        'society_name': 'society-name-LXlNQGqkURvDMLeoyyigbmHGRAjMglENMcYIGWhfEQiMIaXRPB'
    },
    'project_districts': [
        1
    ],
    'project_districts_detail': [
        {
            'code': 'DPCfUGhlXL',
            'id': 1,
            'is_deprecated': False,
            'is_enclave': True,
            'name': 'district-cMVyUuzNVKMIHPTYcHgCDcpHIzVcJyHWOdmsCztXsDkBsNdSHj'
        }
    ],
    'reached_female': 0,
    'reached_male': 0,
    'reached_other': 0,
    'reached_total': 0,
    'regional_project': None,
    'regional_project_detail': None,
    'reporting_ns': 1,
    'reporting_ns_detail': {
        'average_household_size': None,
        'fdrs': None,
        'id': 1,
        'independent': None,
        'is_deprecated': False,
        'iso': 'oA',
        'iso3': 'MjY',
        'name': 'country-hQoAZvUhEREEnLkPAbpciKLkiOGcKjdkqlHzMKObUUQsfnCMEE',
        'record_type': 2,
        'record_type_display': 'Cluster',
        'region': 1,
        'society_name': 'society-name-LXlNQGqkURvDMLeoyyigbmHGRAjMglENMcYIGWhfEQiMIaXRPB'
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
    'user': 2,
    'visibility': 'public',
    'visibility_display': 'Public'
}

snapshots['TestProjectAPI::test_project_csv_api 1'] = '''actual_expenditure,budget_amount,dtype,dtype_detail.id,dtype_detail.name,dtype_detail.summary,end_date,event,event_detail.dtype,event_detail.id,event_detail.name,event_detail.parent_event,event_detail.slug,id,modified_at,modified_by,modified_by_detail,name,operation_type,operation_type_display,primary_sector,primary_sector_display,programme_type,programme_type_display,project_country,project_country_detail.average_household_size,project_country_detail.fdrs,project_country_detail.id,project_country_detail.independent,project_country_detail.is_deprecated,project_country_detail.iso,project_country_detail.iso3,project_country_detail.name,project_country_detail.record_type,project_country_detail.record_type_display,project_country_detail.region,project_country_detail.society_name,project_districts_detail.code,project_districts_detail.id,project_districts_detail.is_deprecated,project_districts_detail.is_enclave,project_districts_detail.name,reached_female,reached_male,reached_other,reached_total,regional_project,regional_project_detail.created_at,regional_project_detail.id,regional_project_detail.modified_at,regional_project_detail.name,reporting_ns,reporting_ns_detail.average_household_size,reporting_ns_detail.fdrs,reporting_ns_detail.id,reporting_ns_detail.independent,reporting_ns_detail.is_deprecated,reporting_ns_detail.iso,reporting_ns_detail.iso3,reporting_ns_detail.name,reporting_ns_detail.record_type,reporting_ns_detail.record_type_display,reporting_ns_detail.region,reporting_ns_detail.society_name,secondary_sectors,secondary_sectors_display,start_date,status,status_display,target_female,target_male,target_other,target_total,user,visibility,visibility_display\r
0,1200000,3,3,disaster-type-KOlJVJAVgXOKwRDSQBgkYlJzGvQkIMCwuJuxAWOBUuMpKInyXJ,VqxCCzaUcsMbHitatonubXSrJGJKKjgcDwjiqxLpoqZtfKzKnUeUuYElFSSKgMPtcUZKyfXdXvwBAhXoVPMaOXOydtHcuIKjuGSojdRUzCWMKGfoBsYzjivfEKVdJzqfzGBXSiWiEJmFzPKmJNVHpperXBuRKfhQABxwmuwMPbXtkwNZCNjCcomRxjWUfhVdpNjsavSZhtCEbvnVInnIHWqJENUjSSQbyLQHcqkdsmYSNrdDPaeyQrQQxgbsPyoyGTguFMIflmGDJTbcpHtvFzVkbwRwwOtpGrZdOqybJrojvzQifUyHRNORoApKjBtMvCIinPiLIRZmitSTHiBXjPKkueJIUhlujUbWuAAtCVOVrjXmgilbWNNrMKNoMooRbwfSXEiGMETPxlyFEikmocAWarAoVQmWnelCNFSuDpBzXcMVyUuzNVKMIHPTYcHgCDcpHIzVcJyHWOdmsCztXsDkBsNdSHjDPCfUGhlXLSIizAuCblDL,2008-01-01,2,1,2,event-JEdfryiAmPZHpOZIYbyYTwEIYFwKGuyrlbuMobZXrdZEHwXLok,1,gpqpriyvdwokzywllpluzvswlbtswkkjkmzfitlfcfdomobhea,1,2008-01-01T00:00:00.123456Z,,,project-TmDfquSPTYkTUhfhTCOxfHTyUYGNkyJycXkvKQjkjlXTdAttUX,0,Programme,4,Health,1,Multilateral,3,,,3,,False,ZQ,ANX,country-AlXiXPUPAxyCyyfRQIiPwhlIzHiUoaWbtDRUIBIyopDwjrmUWh,1,Country,3,society-name-bpnegMcCMRTdpVczCoInWXdiGsoUKuKMXRuptjQHoAtrdJLVlO,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,1,2008-01-01T00:00:00.123456Z,1,2008-01-01T00:00:00.123456Z,regional-project-pnLQEDACfMMapJrNOJndljdPwcjcQKMtvfdgAlkRsNQSSMKYJl,2,,,2,,False,dE,zBR,country-YMarjiIqZlhQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtD,1,Country,2,society-name-gFTCefuMjeirNOLJTuyMHsDGMBgYShPPXJUnBCoAvDzAUguBuQ,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,2,public,Public\r
0,8470000,6,6,disaster-type-hmscizAVvckQmEQrhAFJFZRTiuWWXzGUVyihgYbijwGaXRpdRv,BMVaBEssFfWBpNjUGlprXhqSpQBmETYZgSUGNlmLOOjohizcrmjBbNmfdyAHtSOoovBEdGBPdthrxrwTApudlcadQVunsErMgBlqFxvthgQaRJXivxVZxVXLHMxpPrnLyfgiOVMhcLPmmTCgeINvtUEWmIUjcimAJTqWJwxCOThBeEAHGYbkMrSiscKdYSmVzFRIGekCWGyJXyzMrnlakKnLSaYGDGTUHqtosTrJhkocIpscOjrirYdPpnIhaPwOMxufTJqUiANsudOawoUrlqbIQXXLgUVSyPqOOMJnCournLOZWzjCoUUBxjEfFlDllmKFUlPsbtklzRMmejeBpDPzgUHiUWZaMgyybhaWPcipXfrjOMaYaYgIVvTfmiEWKCktvEjpdISrOIhbcgIsgGAjaoboByjwPsoRyRThFkhogsweNvhxfcMjlBHvMlRBjQRtNswgrFQxqZTZeYajXPjujyCUYYEehKBUrjfuilXywuFBESAM,2008-01-01,4,4,4,event-vMTQDisUTyARPVxYEZkNnsSVfQEilmkMFgYAFtpnJdbwqwRklG,3,czevbhnohjofqvywxcxjrjsgmqgtdczdwhgynnygjcggkohnxk,2,2008-01-01T00:00:00.123456Z,,,project-YOviZPpyAJFIIFIIoyfLTAHKXSZVoSfpxanbxJEihdwxXisDjJ,0,Programme,3,Migration,1,Multilateral,5,,,5,,False,MM,GdQ,country-sWKQjZKUCvShUEciRJhtbzNoCwfudMPmLHoYXrmbfICRQfGzmF,3,Region,5,society-name-xzjTBxyxaswwtCJfnUCVAZCskZUBUAiLMfjntEHveLWyfaAOrA,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,2,2008-01-01T00:00:00.123456Z,2,2008-01-01T00:00:00.123456Z,regional-project-SgQLeEMkbjxjfpeaKAjWlEViVHStEAUvCYPSashjdPcMWlGkaz,4,,,4,,False,UO,FFZ,country-XtuxyeWBJesEihSrvHAHnSnNdgKUOHfEUSMYTsBMuqHKNwiNKF,5,Representative Office,4,society-name-lNoTsmahbDOYhVnZNAAcvwJZOnaOmSsqYettGJuXahRvvzUKNb,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,3,public,Public\r
0,8680000,9,9,disaster-type-vuQziUHnpnTmKmUQYNxDJWYAxPtnzjEgIPCtXNAdmnvJkQyHBl,CbSnyKQlrVRKXjPzKYZmjAuDpViWFuNWNHVOcRgYefbadvfuwmVjntexNuLCEvTlstgZJkjkAhINAkJJOESrSphQjCgWciyEyEkXbLSxCLKlCbFQKwvfxeliNtRzjhYQmOusTYYfwMZFbNLAkxqmGrHbFukdPpStqCBvcrVWQDQfvJciNaVKbtymEyycSRrSyvxZGYBATviwUqJmFsrfCQfZQuGhbZiZWgpelxejKZpXfeaUaVZvNejLODOvYQgNhdTimVflfTfaBYRondTfyuOHmEmTFMTlEsURLdClGaflmqjIKmShSWemluWokzOLsMAGOsnBqwVpHaPRqsWkedeFwUdNWBfRWTCaVRfuLXxSRMReKqUuCwVZExFtWFuIVmoLkcSwADDuYzDDCjjVWyAbiYuyOjzxaBYQljLlngbzEjrvmbFzktJromFMUFBBkFQdwgeuTEMsjpHFZnAFatOkvOtRNBNhMiHsvUxZSixKEebCxApn,2008-01-01,6,7,6,event-ZgcxbNTjTVlifAhdCOTdugIrmPNVbvRuTkLUxHaQzAQQdemWGj,5,urflccrmmsgalovatrjwhvdksfkdfhfluflulobxkyanoxdfup,3,2008-01-01T00:00:00.123456Z,,,project-uSouOEYrJvKYvSmiuYOKoTLNppFKEbuGgyWjNufHFDMUreCyXm,1,Emergency Operation,2,CEA,1,Multilateral,7,,,7,,False,Qg,FRE,country-GelPjwPUKvDTYirYWQtzePEyEMQlKTGXQHqiSuLLwLNzecbUko,1,Country,7,society-name-uWoXZUYpglUyWAedNqhcVeCWxMOblugSCyiOKJmmqFCRsomVkB,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,3,2008-01-01T00:00:00.123456Z,3,2008-01-01T00:00:00.123456Z,regional-project-uFuMImZPmMMhsUdVmHZGspYyBSatqnjsbbPPWAfxDXjCOyJkMC,6,,,6,,False,kI,gen,country-qKGtToBkrfHyiVnzNdozlVJMeSDEuPPzykdZxPBmrggexMXvbp,3,Region,6,society-name-MaWtmJmOcprfKKcKYEcduftawWszGmuWzUwiSRgvAVGgGZXjbL,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,4,public,Public\r
0,10000000,12,12,disaster-type-cqvTOmcyMYouUIGjrNovotacSYOVgGeTzCEGsGeBwlrqqQxqqB,dInIxSeEMNnCTYJgaPRPWZUQupPMhjIDGGQqIVyZNKLBLHGXjWSMdtuELSiEgrCRiqyocZfUMIVyTqlrinJPoLCkHppKYgjhPQJFbzkKnlHGdTKJnkjhchalolabeSHyDByhcbGOMQJZRETyhaJfsmxyYfsdUpJsuPpPfLGWdYErAYWXJPimutALuRYgcamUXbDWzlaxrvVLyCevbScBBQyBrfeaPzxtfTfTosaZCIugzNLrXNEcHNaxXJWmBAJmsJjyIUKKNzkyMDYaHoIBJJHOKhEHRQPFYNexbxZLBlxDeKDybSMpibfiBSWwDOHKJlyatfJaWKxieYDxvGuhDFDsTfQViFsyMlYegIRZPJjrfMTLziBrlkjMEvGLeCdZTqUUxrigJwRsxFcuBXGiaKjixFaTKbUdeOzoTvArdDknirElGkJNuUYradfFHPHlkSqTCpfiAeyIYXxaEedYwJPSWdfhKxaNlDZgQfulBfVcVxoYCdKi,2008-01-01,8,10,8,event-zUoZjZgfgTMDHDUYhIdMmpLfORmFnizPuocAcUefWNWGFWuygD,7,gaxjuhaalnbzblgvxahjimhapsyveosfqusmhuaanrnzxnywid,4,2008-01-01T00:00:00.123456Z,,,project-mccDeZBLuRaaEqSPfGKYtJTuSsoZPjZKHDALJKnAwiMqrEXhAU,0,Programme,9,Livelihoods and basic needs,0,Bilateral,9,,,9,,False,pF,FzL,country-tFUzdLtZqgjJoYopDjgSIGxAVzAKvtfpkNEQeXudBzBjAEbvxh,3,Region,9,society-name-nzBpspNZkvkMuLyfgffYVajIBFfYZSPjdaElcisxRRSwQKfckt,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,4,2008-01-01T00:00:00.123456Z,4,2008-01-01T00:00:00.123456Z,regional-project-jwXJQNzoRleDsnYYUxCqHWpvjAHdzrIBcVBCmLJoTqtIGmJtlu,8,,,8,,False,kT,pfW,country-TMDskLiubhduJExjuUyJbOBPuzluNWcPsuKWKcGdUTTiFeeijg,5,Representative Office,8,society-name-xwvfAvWeFzIdHAPYzSjJfnCkhWqopdPRJbdPSoEccoWojiGuuy,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,5,public,Public\r
0,2900000,15,15,disaster-type-crSDlmHBUTrePaaMvoGvOuEVrlfzUrpuXLMbZcLXoEIeqRBdtF,POAVgsoDGHqrnDdzUyfIWCPwAqADiRyWozJZYexQtSfHxHVMKcdjCESkKhaXHtvcSDPJybspxAWBcvcoTpCrBLGpnbzEPCQnbzESYhJilVlAAEKPrXfNbXGCGPGBvnGWvRMZcyEWnKAntRkSGSNGWEzbVuZOubQOtKiihSDdqPJBWSWeIzRUCbAznldWezWkKRaEmZLLlXGNfRKIkFhJjASuXnXZoDfDVaIBtNqkzLskbnTSLIRQpfRXputROMSbhswXKNACbyMleNvICmaxqMHkroJGVXrQYpZdSjYSRVeDUIhAEGayOyPrQoRhvPHLWWdgyPqXLUQjPGfvamCXchEdMjAOtcCdnbGOIcHOeDkzjHkMAJlPXstHuWbQbDjHGQLvKlPPDOrfeAIaBLRhUMyhkZEzziaJcHibpNhDdOWZlAmRqrrnuZMyOPlPqvHRFaflaVVsZQQjtkQxnAMbLfjoDxpalJrKCzTdpNyPWCaiWspyuiWS,2008-01-01,10,13,10,event-VECVykLZzLetonziLMKqyOYBqvdNLKLYbSchdIMJvEoKbIoRTv,9,kgtfimaqhsskpsyrvgxhtnwqnudlxckjxxfvotkwwhihvhldlj,5,2008-01-01T00:00:00.123456Z,,,project-tcwwoSWBqGWfSICYxXrRbpzSrGIjhwTKCFpHxrTzAjmioBcyzZ,1,Emergency Operation,9,Livelihoods and basic needs,1,Multilateral,11,,,11,,False,iM,UEU,country-ptvWqsVotTqYeYtNhzKMLpWMpTqrLCsoKrAqbHWRQSJkjodLvG,4,Country Office,11,society-name-nKQIPXHLrgpkgaWKCidSlhEWcEutHwmsOTYAxvEZLiXicpactr,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,5,2008-01-01T00:00:00.123456Z,5,2008-01-01T00:00:00.123456Z,regional-project-MHylkAKNiayAzeDKLAlmwyNLMQjLVMYUJpnuWJVEzJGDTFCNlx,10,,,10,,False,gM,Rbj,country-iIdvvdCCrTdzxCNvwfxzknKlUaMcIvXugcFOStUbQMgogfgDXG,4,Country Office,10,society-name-vZsTCRydRSlkObzTNxourSfRlafQilCuYYKwdakAWZSdfuhvnU,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,6,public,Public\r
0,2090000,18,18,disaster-type-gJNIQgaBeFnOZRTuApgAmgkMDxwClVWAgAMtMAnFJGefKnHSTL,PLLdzHkSdhWnPaFeBFwmYRSkhyoZSmAhZpeENHvrLcWctSMdpERkMwVsxHXvGovSApRMLJWhjErUnMOjjuXvgCZreMSVluJeOVqFAlgTlTmzZchSIzoKMqwqgnUXJquoguynXdMpaXZEMzHQVvXNcPLBSQtxYLIDiOrUcJVNMlSgDEOXmvPWfAzGeennNEmBCbESihEQoTsaTltiPkPkVrgSNHYUoZZdARplUpButagIgPYtsrksWJrjQQbkSrpZWxaSMtCAwSfhQVGBQevAraNZKsgtFwmNINTemDcutOitufRONdGlyeQXebPmuyuNrlVKLlcOlpEyTyBLQBMlXkKwooIyfKqfeOIYWmMRbNYoYYtirPOjsayBRlGVmrAmmZtRHIMopqnExgVHyBNqUcGBXZxZslspUJlyNiJvvbCrnvbKwkWJOHZNxMrEOapKBZMBsunuMgEzvcqDhZJHmacWLZLvriJGDnrsVUNPzQyHBBCLINLq,2008-01-01,12,16,12,event-GPAlqcYSGCXZgaaOAAIMdRrZWgFiIjaEAkmGUhhwYQkiojJjll,11,jjsaireujhmwmlmtcarfcuwjrcmzhoxygthpwqbxumuxcjkxph,6,2008-01-01T00:00:00.123456Z,,,project-DbASgDSPbBLdfqNCffbWnZHqYTCgvzEwABUuaPveIUGBbRgyFQ,0,Programme,4,Health,1,Multilateral,13,,,13,,False,ER,Kdc,country-zlLnQPRfxfZHZWfDIGjsXjyxvKtANJLbAjpiDUjoPEhCNGLbjk,2,Cluster,13,society-name-TYWBurZTIOOCdQJrZDCLuTqeOYCAFuumLHeIINRcCVnDGewLeu,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,6,2008-01-01T00:00:00.123456Z,6,2008-01-01T00:00:00.123456Z,regional-project-PvYAATKYoFvtciTVqlYJBeESILkvZChtcivdRpIuTFBVlWytGY,12,,,12,,False,nt,hbn,country-pqHldHZqMpgumMHVmWMfjizabaestdPQSDzjNUVeYtVPQocsUK,1,Country,12,society-name-HZKFujOIEicLNIBPuQytkVYQSisavNTPjdHlovobKFBBMZgNqJ,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,7,public,Public\r
0,6150000,21,21,disaster-type-pdZDbQAvNqHbuogyciTiCOtppdnCRlZPTWFeIAOPkstDwAmeZZ,giOenISaFIlJFIWZdzAeuStwNGvGzyowBuTsfHbkOJRHlviekQHTIyBLcuNryLTMHWtlIGkSIsCcvjcpfQoRkNIJDfYUWknVkbnByHBsiYCVEIyiBISQXvlEjHDVybUpjaGECJorCfVaAlQIoorOOwWWOTxEpvBlmPiZCFPTXcdqvnvHwTLEndiXDoVOQikJwZCbtTkYqcWUjvvvsAHMUYSRoLYCDPcsggAEJIexYLAOYszPDoHzYvyMatrGQqVQBFVonlTlNeSksIMvwIDSCbaQBkpRNquLLRrkArcFAbOJMundfiTdopKGbShpUGFfWyjIopwBJNduJXecIRbhxnnDrZmuzDbiOPCFkGXDeuyxMBQNxDSLQswFvKvNKxxbvuPpSOyiKTOfChtGxseJoNwkSuiVQxjZdDQXHPGkXWezPugeNOTlftxFsTsujdZncYZQiEOyWNqDmbGUXJjtdmUxRplUfYkVssaVSlLmXBosPYYbKqfl,2008-01-01,14,19,14,event-YBhVAieQQIQxTBpuiaXaDBeucsjduMJQyGZwQPAMCDetmRnSBb,13,gcvwlcgcfswwaugdunmjfghgjgimncrzzqhypjhhagetiuwfhr,7,2008-01-01T00:00:00.123456Z,,,project-ZTfJcxTQkwEKuLKdTbsEMqfiZPpjutAafJMfYhnZtVUoqZGTxE,0,Programme,3,Migration,0,Bilateral,15,,,15,,False,tk,FOt,country-QJXYLBCzRpwmYBFpxRYwTHMAcFdDiiIInrXfnoZwgWmNaermdM,4,Country Office,15,society-name-NoBzRouETXUKACXeSrHbmTXQaQdDRUoZxXOBxJjybGlvlQApUE,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,7,2008-01-01T00:00:00.123456Z,7,2008-01-01T00:00:00.123456Z,regional-project-sihXhjbXkNfSTnGfocfsLtJckNHMdJIPHTeLyRAtZxkmhKgRKL,14,,,14,,False,dn,yuA,country-HPsKpWVAJdQymuGwobUfbXfWjCJKyMvfZNPnaWsPGxjTFDwHyW,4,Country Office,14,society-name-jdmVBnqtRsnOMqzGXMyVVTpogIeRjmoxCRAfETVdCohCtrwDDB,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,8,public,Public\r
0,9070000,24,24,disaster-type-EdbprpWDrmUjwyZREsbYYSvnyiufPQjnhevqgOehLbOibyaFgp,VzPLndYcxileRtqkPBYCPpVWxmJqQiuXBhhAgRuQWNKTNtrVjAYSfIrvunCWXuIjzHiUPNxdIgrNLQtclZmimwJxLowGdSnQVOvPkGHbvbZFucFTQGfLROCZnxqYYsiwlrTSEFFEqsXrKyqYLpctBsZddBayKIGiytIBiVQDxZxZnFDLoYJwPsPZybLgihbqbDkxqZwUmMBcfWBdKNojOVqDbCKjzixQYgTEsmhRzXdnixdPoVRSXLtpROMGHqrjDJKwjRpBfYFLqKAUqvZtMSVwTNwDUGhlCUmUgFTsRUQZjCUgHoijRrbknMnzQiEygDArTbXQrcrUyvQxgfkJyoGfhbwaiTZiITMkcEXPsROvLwkYHTiCXAFEYrlnNnuSqnWoODmUYiTCHnMAXVLlfwhcaiyaFCWkeqmOOqSHyKQYyYvnFexwEphbwlaJKJmeJDobQZKxdENnoDCogiNEmrfVtHvdXkRSDQxMOSbHjAITbaMdEjlb,2008-01-01,16,22,16,event-DnBvQsSRasqNiElGdNamhCJGpYQYyZqpVfBFVHuVNGrqrcJJQK,15,uvlnbmlocdoxbatvjbnnxdhvxknpcimmqnzymobmkpwzwqapbc,8,2008-01-01T00:00:00.123456Z,,,project-JPOEfkWhHLWrwlpMPSuKAXcipneuZNXNHUDwhDxCYNbmkmaJHI,0,Programme,6,Shelter,0,Bilateral,17,,,17,,False,oK,AIC,country-bkLvYEmYHagbelsZwDgIfxJdyVPZfMsMKXLhmzOYUxcwvhKgQV,5,Representative Office,17,society-name-fGBYQFeEaIaPtNjMnTkWJTYxbFSgMBfjLonieWmrKwkicKXZqc,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,8,2008-01-01T00:00:00.123456Z,8,2008-01-01T00:00:00.123456Z,regional-project-dCGOIBFPwHSYFuvRIvaLvKWgtvcsNClpzANsRziClGBvgIhsXS,16,,,16,,False,Lx,BbF,country-muzJUSngCjoWBOzFdtTSeEfaPnSJKfNhGYWEscubhpUnYkbWpr,3,Region,16,society-name-eqHEXzwdTFDwWTjwTPDjoeyWVnhzbmQFPGUefPQVXduXSWCbmW,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,9,public,Public\r
0,6280000,27,27,disaster-type-zCgOSYQZaQGaaTqOwGSElrkQlERPsUSLzBwTQiNtHmcwhDhLDj,VvelPnqnWpuoBDxRCREFCnqUYiyZXvIEudnQeatTPLCMfqaEEeOROlGbYAfQKMcEqzzTAMWFQrEjYVfDhWksXoxyBGQZpYVdnjwWmyKxTjxuICUVyFnuUaEJWfVdQFlHSoPMtZDyrUAVRelRyfqNSOYMnQzQpgXKzlCvzStqoLWcLueOMvzznbdPzmyjThYdwReyqdCGDVZTPdtGgfnVPxWWmSUEVOQOpMAxkEOkWZMuLVIzCDESdvxtHLLTXcEflSLMyMWMgusTJlEadQiKpnXSgnizGKmEqAbkepBWIIsexFEfSiVMeHrlSOPxeULwYAWfEBQxvJMkjoSxxiSIuJFQbBmaYQjXjJXTlMoZpwjICHNFgxUmwZMPAtFkAHQtVFrArRxucDRjHpgWahJwURdHIdIEuzVtwWbVRvIhPauHagaJPJRAFMFZqqFBfLnCIZXUJBymyYOsyWvpootCCrVKAomEKjjYSBkGhNewalnFsnJOFpsu,2008-01-01,18,25,18,event-taTcnVkEnbnWitXHlTCtSynVYuiRUoYvAfhJGSWjapIaRBRTUL,17,vgqaiqejvmpqetggpkgwfdfymbznozbyzozpuntelgeppkaulg,9,2008-01-01T00:00:00.123456Z,,,project-dukhMsauOaqEiWAbNEPKBkMerwLFCpAybKIWVuLhMJfCWtFUoy,0,Programme,5,DRR,1,Multilateral,19,,,19,,False,ER,Zvn,country-kHVnkyFRbgVWfzCGhhZBDYVIAViMalugvmGzqWkBCoXbkkcNKt,1,Country,19,society-name-PbsRaxYmeMHrXedQvbCuYuaHqGukJsAFCdoYFGqBCNFdUaJPUo,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,9,2008-01-01T00:00:00.123456Z,9,2008-01-01T00:00:00.123456Z,regional-project-hZONIqqqYUMyeBpKulvEqEEErpCOkfjoGrGDCxyeYNfJWKHEvx,18,,,18,,False,dz,PZB,country-JrWQucRSqzjgFyqQmsMmKsgBYTWyCqcCJRJRSAKGVSxIuCrNeW,1,Country,18,society-name-DPjBsfGCNpPLCINunDEdekrKnhBVrwRQMHjqpCIarCascEOLmy,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,10,public,Public\r
0,3590000,30,30,disaster-type-pAPmOaxyMvPPWAluOcRLyNteinukJHINLRYaRJGWWHyWbHefaD,gsMVlnTzbpXAGbGPvJQGsqYXrnZFiXhmlBYTTFFAnJYoXeTLeRGdZtoGtSpcXLEKFvXyGTYqlhJhJWceZHVErDkMfTSoghkywNSCtyandiRngieFHhCYWbtlTpiFuHIJffIuNZkbAnbqhywiDkzfJKgaKwogcbeDMQlWueozOkjmIPbenQCclbKPJfMtaeWryNyfTpzcDFjFkcOVsxdSTKJaBVnSRwopnxbhzTlAiuectKryhFpcxQeZUvgnoQibLzCmdLYjsaEtfOmvKORAAvppKdoYyoQHxErmoMgLuGbSabYJtgzjRyFxcfTtBHpPhrzxaYboKqXOxxGTRUTsyVsPkdgGgWPMbinkagywgMHJMazVbMhFXwcDvhVLkyDEOwZbrzgzPkQjROGOsmUMRBwBIVOJWOFYkajaqJFfboyYRvosFyWsfqsYjUTVEhRLCsvnesxLxwaJddjONbBULwtEmuBqiZCSiLqnAOfcYNbKHkqudPHh,2008-01-01,20,28,20,event-uFoeQGdjbsbqeTaDZgKeiMXZrpYSpDdlBxCHgsNzoZwubfLnxn,19,eqfbhuugtxzcofoedscusteqsdrkmfcxabzfoalgtscndnpmez,10,2008-01-01T00:00:00.123456Z,,,project-qTBQtCcjmAaCshFdYBaklxkvumQQfmqVfCAllIbKwteFxrRcgy,0,Programme,7,NS Strengthening,0,Bilateral,21,,,21,,False,sB,qum,country-hqEusQzBjrWHjiodPBsiVeYfBGqzdoHZMZwgOSvNjprSBzujeW,4,Country Office,21,society-name-WogBWrLYuaBcXuPsggSnEPgoPRsPBVYpOgWRaFIMRcOEIBKRVu,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,10,2008-01-01T00:00:00.123456Z,10,2008-01-01T00:00:00.123456Z,regional-project-bWWIkZLBPQwBgiZdYysyrUAEyqDJwykvdJqwdVRePtpYKLKjwD,20,,,20,,False,pm,xYm,country-iUlMcOXbduLauswVhCoyuJxscuUKeKortlsAiQVEgimNopdXWA,3,Region,20,society-name-TxNEuLQIbKzZkGlUThMzaHFJFWOuOEGPJjXSYEmDBpdLEDoLPG,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,11,public,Public\r
'''

snapshots['TestProjectAPI::test_project_delete 1'] = b''

snapshots['TestProjectAPI::test_project_list_one 1'] = {
    'count': 1,
    'next': None,
    'previous': None,
    'results': [
        {
            'actual_expenditure': 0,
            'budget_amount': 9080000,
            'dtype': 3,
            'dtype_detail': {
                'id': 3,
                'name': 'disaster-type-CDQLGiFaHVdJBLEGXlSLlUigyQMMuGyAMSWprzvsCZiiAMSVGt',
                'summary': 'SJuTVJOnmnNTsRwRiTPlGISOuThWwJELKQTARVIsBZaHgbyjdQdmrWYksRqjdSYsnWIcwCgNRVJoVPJypGYYZSsSQdyyAYRuJdaVqmNXCoOTTPxWLIVMmXUmsClRellVGhycBrJqikLqavDTjcjuMdXONQtFYKJweYTuHolHeYGkAIIzfwonQvvxsnWNHEJWPahQwCpPNNpcRuyYhyqIUsbHXxGZGCFcsPmuGfgkXIIaOenQOXnRBgnISVXBPeVRjbDTvcfedlYqJeKoqAyCOzBubyRhIaPUNeWVLcSewGgsYRtMfsWCyzQbEkIoiVzYZIsOjtRYUPxaJJjhcaKMzIJftnVVUwnAPGjkloNqmhlQZKdWJDPJesQeqgmULFvwiQPpgsNemuFCvNQtSLjKKxZuBkaupYoTVPBrxiRUvEDCwXtFJglPMfriImqUOeUebGObLLzXLncJqIIEPXjxzoXLUsiDGGfzxGaQpZNRkWGiCklKKQjV'
            },
            'end_date': '2008-01-01',
            'event': 2,
            'event_detail': {
                'dtype': 1,
                'id': 2,
                'name': 'event-KRWmlNOzBGufzQgliEupaqypCWrvtLUKaqPxSpdQhDtkzRGTXt',
                'parent_event': 1,
                'slug': 'shosxnooiejdvmxasjewizqnwprwmyfhchtxekhdjgmkijkuhc'
            },
            'id': 1,
            'modified_at': '2008-01-01T00:00:00.123456Z',
            'modified_by': None,
            'modified_by_detail': None,
            'name': 'project-UEwcoWFoeqxocQnHYxyEDccPugTHOrVqLIKlyPyxLPeHqyoHzw',
            'operation_type': 1,
            'operation_type_display': 'Emergency Operation',
            'primary_sector': 7,
            'primary_sector_display': 'NS Strengthening',
            'programme_type': 1,
            'programme_type_display': 'Multilateral',
            'project_country': 2,
            'project_country_detail': {
                'average_household_size': None,
                'fdrs': None,
                'id': 2,
                'independent': None,
                'is_deprecated': False,
                'iso': 'Eb',
                'iso3': 'NJu',
                'name': 'country-AlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOxgR',
                'record_type': 2,
                'record_type_display': 'Cluster',
                'region': 2,
                'society_name': 'society-name-NoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgR'
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
                'name': 'regional-project-lkxMThQoAZvUhEREEnLkPAbpciKLkiOGcKjdkqlHzMKObUUQsf'
            },
            'reporting_ns': 1,
            'reporting_ns_detail': {
                'average_household_size': None,
                'fdrs': None,
                'id': 1,
                'independent': None,
                'is_deprecated': False,
                'iso': 'wM',
                'iso3': 'qZc',
                'name': 'country-bVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgfyg',
                'record_type': 3,
                'record_type_display': 'Region',
                'region': 1,
                'society_name': 'society-name-UDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkIUpkDyrOS'
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
            'user': 2,
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
            'budget_amount': 9080000,
            'dtype': 3,
            'dtype_detail': {
                'id': 3,
                'name': 'disaster-type-CDQLGiFaHVdJBLEGXlSLlUigyQMMuGyAMSWprzvsCZiiAMSVGt',
                'summary': 'SJuTVJOnmnNTsRwRiTPlGISOuThWwJELKQTARVIsBZaHgbyjdQdmrWYksRqjdSYsnWIcwCgNRVJoVPJypGYYZSsSQdyyAYRuJdaVqmNXCoOTTPxWLIVMmXUmsClRellVGhycBrJqikLqavDTjcjuMdXONQtFYKJweYTuHolHeYGkAIIzfwonQvvxsnWNHEJWPahQwCpPNNpcRuyYhyqIUsbHXxGZGCFcsPmuGfgkXIIaOenQOXnRBgnISVXBPeVRjbDTvcfedlYqJeKoqAyCOzBubyRhIaPUNeWVLcSewGgsYRtMfsWCyzQbEkIoiVzYZIsOjtRYUPxaJJjhcaKMzIJftnVVUwnAPGjkloNqmhlQZKdWJDPJesQeqgmULFvwiQPpgsNemuFCvNQtSLjKKxZuBkaupYoTVPBrxiRUvEDCwXtFJglPMfriImqUOeUebGObLLzXLncJqIIEPXjxzoXLUsiDGGfzxGaQpZNRkWGiCklKKQjV'
            },
            'end_date': '2008-01-01',
            'event': 2,
            'event_detail': {
                'dtype': 1,
                'id': 2,
                'name': 'event-KRWmlNOzBGufzQgliEupaqypCWrvtLUKaqPxSpdQhDtkzRGTXt',
                'parent_event': 1,
                'slug': 'shosxnooiejdvmxasjewizqnwprwmyfhchtxekhdjgmkijkuhc'
            },
            'id': 1,
            'modified_at': '2008-01-01T00:00:00.123456Z',
            'modified_by': None,
            'modified_by_detail': None,
            'name': 'project-UEwcoWFoeqxocQnHYxyEDccPugTHOrVqLIKlyPyxLPeHqyoHzw',
            'operation_type': 1,
            'operation_type_display': 'Emergency Operation',
            'primary_sector': 7,
            'primary_sector_display': 'NS Strengthening',
            'programme_type': 1,
            'programme_type_display': 'Multilateral',
            'project_country': 2,
            'project_country_detail': {
                'average_household_size': None,
                'fdrs': None,
                'id': 2,
                'independent': None,
                'is_deprecated': False,
                'iso': 'Eb',
                'iso3': 'NJu',
                'name': 'country-AlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOxgR',
                'record_type': 2,
                'record_type_display': 'Cluster',
                'region': 2,
                'society_name': 'society-name-NoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgR'
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
                'name': 'regional-project-lkxMThQoAZvUhEREEnLkPAbpciKLkiOGcKjdkqlHzMKObUUQsf'
            },
            'reporting_ns': 1,
            'reporting_ns_detail': {
                'average_household_size': None,
                'fdrs': None,
                'id': 1,
                'independent': None,
                'is_deprecated': False,
                'iso': 'wM',
                'iso3': 'qZc',
                'name': 'country-bVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgfyg',
                'record_type': 3,
                'record_type_display': 'Region',
                'region': 1,
                'society_name': 'society-name-UDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkIUpkDyrOS'
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
            'user': 2,
            'visibility': 'public',
            'visibility_display': 'Public'
        },
        {
            'actual_expenditure': 0,
            'budget_amount': 4360000,
            'dtype': 6,
            'dtype_detail': {
                'id': 6,
                'name': 'disaster-type-YLPcnomCpzntByKkxqJfiWfsCHwoLcDGNvBCDBAxZFuryblCoq',
                'summary': 'PewfsGGIPfYroghexcImvmRvqtVXRrmTMiWTVIqaXtswYzzLWPaEPGWjzooUVnEoHLYJWDUDvYfumBXSAnCCJbxiKitVaFZQwvoABRWzWXSItuLbKYcijvKOZMMKzynzeIymEgvKCOtfkgRJlcSMFblmeysnosQHeDdxHakuAzkhiIAEVeynintBTQEkMKtLmGTRDrmajCezMZpHvKFDDKcVfsPDwSTYtzNZlAplNUBDyQlSKgzScpkrOIsQeSUUnFAWJhxeWgGXXuACkqnGcDbeOSRVDyvVzmzcaqhTiuQVDFDefJQpTCiErkkbMglshIVzkeQWaRrjCwlnTcRInCSdOZHPQTQgyStCdMadXyXmpxpmfbAbavmRQeogZQkUkcAGguuJOmNnIzBhongwulazPuaynDoeQrPNxcenAtXMFgTIYKkqgMuOSyRXSivlOWSuQEevbMLCyGOVoGLTaobNWhtpVBWpNfdixFsmjynPcpUMCVvi'
            },
            'end_date': '2008-01-01',
            'event': 4,
            'event_detail': {
                'dtype': 4,
                'id': 4,
                'name': 'event-IsCNxZRSZemDffzlsegkrhSjFjnHObsARIiEwACVPbsmebZoHP',
                'parent_event': 3,
                'slug': 'valvppyuflqshjcdtkiytkyqoexsxdjwsdknktislltsqyjkph'
            },
            'id': 2,
            'modified_at': '2008-01-01T00:00:00.123456Z',
            'modified_by': None,
            'modified_by_detail': None,
            'name': 'project-ruPYWcHYAPsWboUvvpnIdQpZRSUoMyHulCOaeFemdOjniflLJY',
            'operation_type': 0,
            'operation_type_display': 'Programme',
            'primary_sector': 3,
            'primary_sector_display': 'Migration',
            'programme_type': 0,
            'programme_type_display': 'Bilateral',
            'project_country': 4,
            'project_country_detail': {
                'average_household_size': None,
                'fdrs': None,
                'id': 4,
                'independent': None,
                'is_deprecated': False,
                'iso': 'Qj',
                'iso3': 'kjl',
                'name': 'country-lXLSIizAuCblDLTmDfquSPTYkTUhfhTCOxfHTyUYGNkyJycXkv',
                'record_type': 5,
                'record_type_display': 'Representative Office',
                'region': 4,
                'society_name': 'society-name-XTdAttUXCsOlhimaNWqaDFFIZaMFpnLQEDACfMMapJrNOJndlj'
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
                'name': 'regional-project-KCOmrYEfxzykECBGNVBWjYEbWyBfWtMIjJUlqyDtDsyJMEeviT'
            },
            'reporting_ns': 3,
            'reporting_ns_detail': {
                'average_household_size': None,
                'fdrs': None,
                'id': 3,
                'independent': None,
                'is_deprecated': False,
                'iso': 'HA',
                'iso3': 'xcS',
                'name': 'country-jYLXlNQGqkURvDMLeoyyigbmHGRAjMglENMcYIGWhfEQiMIaXR',
                'record_type': 4,
                'record_type_display': 'Country Office',
                'region': 3,
                'society_name': 'society-name-HBoZEYXywLZVWSKgBiqEXofsMIAqmaTVYaKHhHayPnSZuAxgjB'
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
            'user': 3,
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
    'budget_amount': 9080000,
    'dtype': 3,
    'dtype_detail': {
        'id': 3,
        'name': 'disaster-type-CDQLGiFaHVdJBLEGXlSLlUigyQMMuGyAMSWprzvsCZiiAMSVGt',
        'summary': 'SJuTVJOnmnNTsRwRiTPlGISOuThWwJELKQTARVIsBZaHgbyjdQdmrWYksRqjdSYsnWIcwCgNRVJoVPJypGYYZSsSQdyyAYRuJdaVqmNXCoOTTPxWLIVMmXUmsClRellVGhycBrJqikLqavDTjcjuMdXONQtFYKJweYTuHolHeYGkAIIzfwonQvvxsnWNHEJWPahQwCpPNNpcRuyYhyqIUsbHXxGZGCFcsPmuGfgkXIIaOenQOXnRBgnISVXBPeVRjbDTvcfedlYqJeKoqAyCOzBubyRhIaPUNeWVLcSewGgsYRtMfsWCyzQbEkIoiVzYZIsOjtRYUPxaJJjhcaKMzIJftnVVUwnAPGjkloNqmhlQZKdWJDPJesQeqgmULFvwiQPpgsNemuFCvNQtSLjKKxZuBkaupYoTVPBrxiRUvEDCwXtFJglPMfriImqUOeUebGObLLzXLncJqIIEPXjxzoXLUsiDGGfzxGaQpZNRkWGiCklKKQjV'
    },
    'end_date': '2008-01-01',
    'event': 2,
    'event_detail': {
        'dtype': 1,
        'id': 2,
        'name': 'event-KRWmlNOzBGufzQgliEupaqypCWrvtLUKaqPxSpdQhDtkzRGTXt',
        'parent_event': 1,
        'slug': 'shosxnooiejdvmxasjewizqnwprwmyfhchtxekhdjgmkijkuhc'
    },
    'id': 1,
    'modified_at': '2008-01-01T00:00:00.123456Z',
    'modified_by': None,
    'modified_by_detail': None,
    'name': 'project-UEwcoWFoeqxocQnHYxyEDccPugTHOrVqLIKlyPyxLPeHqyoHzw',
    'operation_type': 1,
    'operation_type_display': 'Emergency Operation',
    'primary_sector': 7,
    'primary_sector_display': 'NS Strengthening',
    'programme_type': 1,
    'programme_type_display': 'Multilateral',
    'project_country': 2,
    'project_country_detail': {
        'average_household_size': None,
        'fdrs': None,
        'id': 2,
        'independent': None,
        'is_deprecated': False,
        'iso': 'Eb',
        'iso3': 'NJu',
        'name': 'country-AlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOxgR',
        'record_type': 2,
        'record_type_display': 'Cluster',
        'region': 2,
        'society_name': 'society-name-NoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgR'
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
        'name': 'regional-project-lkxMThQoAZvUhEREEnLkPAbpciKLkiOGcKjdkqlHzMKObUUQsf'
    },
    'reporting_ns': 1,
    'reporting_ns_detail': {
        'average_household_size': None,
        'fdrs': None,
        'id': 1,
        'independent': None,
        'is_deprecated': False,
        'iso': 'wM',
        'iso3': 'qZc',
        'name': 'country-bVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgfyg',
        'record_type': 3,
        'record_type_display': 'Region',
        'region': 1,
        'society_name': 'society-name-UDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkIUpkDyrOS'
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
    'user': 2,
    'visibility': 'public',
    'visibility_display': 'Public'
}

snapshots['TestProjectAPI::test_project_update 1'] = {
    'actual_expenditure': 0,
    'budget_amount': 9080000,
    'dtype': 3,
    'dtype_detail': {
        'id': 3,
        'name': 'disaster-type-CDQLGiFaHVdJBLEGXlSLlUigyQMMuGyAMSWprzvsCZiiAMSVGt',
        'summary': 'SJuTVJOnmnNTsRwRiTPlGISOuThWwJELKQTARVIsBZaHgbyjdQdmrWYksRqjdSYsnWIcwCgNRVJoVPJypGYYZSsSQdyyAYRuJdaVqmNXCoOTTPxWLIVMmXUmsClRellVGhycBrJqikLqavDTjcjuMdXONQtFYKJweYTuHolHeYGkAIIzfwonQvvxsnWNHEJWPahQwCpPNNpcRuyYhyqIUsbHXxGZGCFcsPmuGfgkXIIaOenQOXnRBgnISVXBPeVRjbDTvcfedlYqJeKoqAyCOzBubyRhIaPUNeWVLcSewGgsYRtMfsWCyzQbEkIoiVzYZIsOjtRYUPxaJJjhcaKMzIJftnVVUwnAPGjkloNqmhlQZKdWJDPJesQeqgmULFvwiQPpgsNemuFCvNQtSLjKKxZuBkaupYoTVPBrxiRUvEDCwXtFJglPMfriImqUOeUebGObLLzXLncJqIIEPXjxzoXLUsiDGGfzxGaQpZNRkWGiCklKKQjV'
    },
    'end_date': '2008-01-01',
    'event': 2,
    'event_detail': {
        'dtype': 1,
        'id': 2,
        'name': 'event-KRWmlNOzBGufzQgliEupaqypCWrvtLUKaqPxSpdQhDtkzRGTXt',
        'parent_event': 1,
        'slug': 'shosxnooiejdvmxasjewizqnwprwmyfhchtxekhdjgmkijkuhc'
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
    'primary_sector': 7,
    'primary_sector_display': 'NS Strengthening',
    'programme_type': 1,
    'programme_type_display': 'Multilateral',
    'project_country': 3,
    'project_country_detail': {
        'average_household_size': None,
        'fdrs': None,
        'id': 3,
        'independent': None,
        'is_deprecated': False,
        'iso': 'XR',
        'iso3': 'PBH',
        'name': 'country-oAMjYLXlNQGqkURvDMLeoyyigbmHGRAjMglENMcYIGWhfEQiMI',
        'record_type': 1,
        'record_type_display': 'Country',
        'region': 3,
        'society_name': 'society-name-AxcSHBoZEYXywLZVWSKgBiqEXofsMIAqmaTVYaKHhHayPnSZuA'
    },
    'project_districts': [
        1
    ],
    'project_districts_detail': [
        {
            'code': 'XkvKQjkjlX',
            'id': 1,
            'is_deprecated': False,
            'is_enclave': True,
            'name': 'district-UGhlXLSIizAuCblDLTmDfquSPTYkTUhfhTCOxfHTyUYGNkyJyc'
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
        'name': 'regional-project-lkxMThQoAZvUhEREEnLkPAbpciKLkiOGcKjdkqlHzMKObUUQsf'
    },
    'reporting_ns': 3,
    'reporting_ns_detail': {
        'average_household_size': None,
        'fdrs': None,
        'id': 3,
        'independent': None,
        'is_deprecated': False,
        'iso': 'XR',
        'iso3': 'PBH',
        'name': 'country-oAMjYLXlNQGqkURvDMLeoyyigbmHGRAjMglENMcYIGWhfEQiMI',
        'record_type': 1,
        'record_type_display': 'Country',
        'region': 3,
        'society_name': 'society-name-AxcSHBoZEYXywLZVWSKgBiqEXofsMIAqmaTVYaKHhHayPnSZuA'
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
    'user': 2,
    'visibility': 'public',
    'visibility_display': 'Public'
}
