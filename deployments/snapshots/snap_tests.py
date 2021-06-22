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
            'name': 'project-UEwcoWFoeqxocQnHYxyEDccPugTHOrVqLIKlyPyxLPeHqyoHzw',
            'operation_type': 1,
            'operation_type_display': 'Emergency Operation',
            'primary_sector': 7,
            'primary_sector_display': 'NS Strengthening',
            'programme_type': 1,
            'programme_type_display': 'Multilateral',
            'project_country': 2,
            'project_country_detail': {
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
            'name': 'project-UEwcoWFoeqxocQnHYxyEDccPugTHOrVqLIKlyPyxLPeHqyoHzw',
            'operation_type': 1,
            'operation_type_display': 'Emergency Operation',
            'primary_sector': 7,
            'primary_sector_display': 'NS Strengthening',
            'programme_type': 1,
            'programme_type_display': 'Multilateral',
            'project_country': 2,
            'project_country_detail': {
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
            'name': 'project-ruPYWcHYAPsWboUvvpnIdQpZRSUoMyHulCOaeFemdOjniflLJY',
            'operation_type': 0,
            'operation_type_display': 'Programme',
            'primary_sector': 3,
            'primary_sector_display': 'Migration',
            'programme_type': 0,
            'programme_type_display': 'Bilateral',
            'project_country': 4,
            'project_country_detail': {
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
    'name': 'project-UEwcoWFoeqxocQnHYxyEDccPugTHOrVqLIKlyPyxLPeHqyoHzw',
    'operation_type': 1,
    'operation_type_display': 'Emergency Operation',
    'primary_sector': 7,
    'primary_sector_display': 'NS Strengthening',
    'programme_type': 1,
    'programme_type_display': 'Multilateral',
    'project_country': 2,
    'project_country_detail': {
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

snapshots['TestProjectAPI::test_personnel_csv_api 1'] = '''country_from,deployment.comments,deployment.country_deployed_to.id,deployment.country_deployed_to.iso,deployment.country_deployed_to.iso3,deployment.country_deployed_to.name,deployment.country_deployed_to.society_name,deployment.event_deployed_to,deployment.id,end_date,id,is_active,name,role,start_date,type\r
,,10,bM,per,country-niMJnLwriUNBeJqqyPkzDfqRBSjIneOUrOSPmTxKQPGMkAjuYB,society-name-hIhRJAevOfxvXrjZoragyoygYhlHUtLZFgHwSKsJrMgdkuWylw,,10,,10,True,,,,\r
,,9,ax,aew,country-BwmmOmYevmQESSDMSvLKvNtAvkgDYcFoaOoSoDNnpEVXvZVynz,society-name-bJhjsCmOLWxcbmmsloqUlvJplmblqgbRiyPYhvntDpxZxQkHZN,,9,,9,True,,,,\r
,,8,TH,BXD,country-MRAYuCEViqlRLuZsmfAxlzyKobbJPNOofDmqSkdzNBMqjfxkKh,society-name-RFhoTnmYrsVFyiBnMnsURmAlAYjbsqpNCpxLRPDfaEiuSzRnTy,,8,,8,True,,,,\r
,,7,Zm,BvZ,country-YUczhnZPQHDRIjVLoecVjFPbENcpSPialOdtYgDNkLeghFMZNo,society-name-VRzuhRKIiuYnWcLlvehrjWAkSxJkCpLcigYONyXkbFfaalfTPL,,7,,7,True,,,,\r
,,6,oB,sYz,country-gMPtcUZKyfXdXvwBAhXoVPMaOXOydtHcuIKjuGSojdRUzCWMKG,society-name-jivfEKVdJzqfzGBXSiWiEJmFzPKmJNVHpperXBuRKfhQABxwmu,,6,,6,True,,,,\r
,,5,Pe,VRj,country-PNNpcRuyYhyqIUsbHXxGZGCFcsPmuGfgkXIIaOenQOXnRBgnIS,society-name-bDTvcfedlYqJeKoqAyCOzBubyRhIaPUNeWVLcSewGgsYRtMfsW,,5,,5,True,,,,\r
,,4,TS,Mcn,country-GiOzeLKdBQipsquZzSVuuCroemiXXLgjgkCDuAhIwXnCtDqhfk,society-name-ujfTpwzGdRtqlbzCJVJpgDgZYihadXoimzxROPfLLqebemPCZi,,4,,4,True,,,,\r
,,3,Os,xNo,country-RWmlNOzBGufzQgliEupaqypCWrvtLUKaqPxSpdQhDtkzRGTXtS,society-name-oiEjDVMxASJEWIZQnWpRWMYfHCHTxeKhdJGmKIjkuHChRnTLFf,,3,,3,True,,,,\r
,,2,Eb,NJu,country-VAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOxg,society-name-NoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgR,,2,,2,True,,,,\r
,,1,gw,wMq,country-OhbVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgf,society-name-ZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkIUpkDyr,,1,,1,True,,,,\r
'''

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
    'name': 'Mock Project for Create API Test',
    'operation_type': 1,
    'operation_type_display': 'Emergency Operation',
    'primary_sector': 7,
    'primary_sector_display': 'NS Strengthening',
    'programme_type': 2,
    'programme_type_display': 'Domestic',
    'project_country': 1,
    'project_country_detail': {
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

snapshots['TestProjectAPI::test_project_delete 1'] = b''

snapshots['TestProjectAPI::test_project_list_zero 1'] = {
    'count': 0,
    'next': None,
    'previous': None,
    'results': [
    ]
}

snapshots['TestProjectAPI::test_project_csv_api 1'] = '''actual_expenditure,budget_amount,dtype,dtype_detail.id,dtype_detail.name,dtype_detail.summary,end_date,event,event_detail.dtype,event_detail.id,event_detail.name,event_detail.parent_event,event_detail.slug,id,modified_at,name,operation_type,operation_type_display,primary_sector,primary_sector_display,programme_type,programme_type_display,project_country,project_country_detail.fdrs,project_country_detail.id,project_country_detail.independent,project_country_detail.is_deprecated,project_country_detail.iso,project_country_detail.iso3,project_country_detail.name,project_country_detail.record_type,project_country_detail.record_type_display,project_country_detail.region,project_country_detail.society_name,project_districts_detail.code,project_districts_detail.id,project_districts_detail.is_deprecated,project_districts_detail.is_enclave,project_districts_detail.name,reached_female,reached_male,reached_other,reached_total,regional_project,regional_project_detail.created_at,regional_project_detail.id,regional_project_detail.modified_at,regional_project_detail.name,reporting_ns,reporting_ns_detail.fdrs,reporting_ns_detail.id,reporting_ns_detail.independent,reporting_ns_detail.is_deprecated,reporting_ns_detail.iso,reporting_ns_detail.iso3,reporting_ns_detail.name,reporting_ns_detail.record_type,reporting_ns_detail.record_type_display,reporting_ns_detail.region,reporting_ns_detail.society_name,secondary_sectors,secondary_sectors_display,start_date,status,status_display,target_female,target_male,target_other,target_total,user,visibility,visibility_display\r
0,1200000,3,3,disaster-type-KOlJVJAVgXOKwRDSQBgkYlJzGvQkIMCwuJuxAWOBUuMpKInyXJ,VqxCCzaUcsMbHitatonubXSrJGJKKjgcDwjiqxLpoqZtfKzKnUeUuYElFSSKgMPtcUZKyfXdXvwBAhXoVPMaOXOydtHcuIKjuGSojdRUzCWMKGfoBsYzjivfEKVdJzqfzGBXSiWiEJmFzPKmJNVHpperXBuRKfhQABxwmuwMPbXtkwNZCNjCcomRxjWUfhVdpNjsavSZhtCEbvnVInnIHWqJENUjSSQbyLQHcqkdsmYSNrdDPaeyQrQQxgbsPyoyGTguFMIflmGDJTbcpHtvFzVkbwRwwOtpGrZdOqybJrojvzQifUyHRNORoApKjBtMvCIinPiLIRZmitSTHiBXjPKkueJIUhlujUbWuAAtCVOVrjXmgilbWNNrMKNoMooRbwfSXEiGMETPxlyFEikmocAWarAoVQmWnelCNFSuDpBzXcMVyUuzNVKMIHPTYcHgCDcpHIzVcJyHWOdmsCztXsDkBsNdSHjDPCfUGhlXLSIizAuCblDL,2008-01-01,2,1,2,event-JEdfryiAmPZHpOZIYbyYTwEIYFwKGuyrlbuMobZXrdZEHwXLok,1,gpqpriyvdwokzywllpluzvswlbtswkkjkmzfitlfcfdomobhea,1,2008-01-01T00:00:00.123456Z,project-TmDfquSPTYkTUhfhTCOxfHTyUYGNkyJycXkvKQjkjlXTdAttUX,0,Programme,4,Health,1,Multilateral,3,,3,,False,ZQ,ANX,country-AlXiXPUPAxyCyyfRQIiPwhlIzHiUoaWbtDRUIBIyopDwjrmUWh,1,Country,3,society-name-bpnegMcCMRTdpVczCoInWXdiGsoUKuKMXRuptjQHoAtrdJLVlO,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,1,2008-01-01T00:00:00.123456Z,1,2008-01-01T00:00:00.123456Z,regional-project-pnLQEDACfMMapJrNOJndljdPwcjcQKMtvfdgAlkRsNQSSMKYJl,2,,2,,False,dE,zBR,country-YMarjiIqZlhQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtD,1,Country,2,society-name-gFTCefuMjeirNOLJTuyMHsDGMBgYShPPXJUnBCoAvDzAUguBuQ,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,2,public,Public\r
0,8470000,6,6,disaster-type-hmscizAVvckQmEQrhAFJFZRTiuWWXzGUVyihgYbijwGaXRpdRv,BMVaBEssFfWBpNjUGlprXhqSpQBmETYZgSUGNlmLOOjohizcrmjBbNmfdyAHtSOoovBEdGBPdthrxrwTApudlcadQVunsErMgBlqFxvthgQaRJXivxVZxVXLHMxpPrnLyfgiOVMhcLPmmTCgeINvtUEWmIUjcimAJTqWJwxCOThBeEAHGYbkMrSiscKdYSmVzFRIGekCWGyJXyzMrnlakKnLSaYGDGTUHqtosTrJhkocIpscOjrirYdPpnIhaPwOMxufTJqUiANsudOawoUrlqbIQXXLgUVSyPqOOMJnCournLOZWzjCoUUBxjEfFlDllmKFUlPsbtklzRMmejeBpDPzgUHiUWZaMgyybhaWPcipXfrjOMaYaYgIVvTfmiEWKCktvEjpdISrOIhbcgIsgGAjaoboByjwPsoRyRThFkhogsweNvhxfcMjlBHvMlRBjQRtNswgrFQxqZTZeYajXPjujyCUYYEehKBUrjfuilXywuFBESAM,2008-01-01,4,4,4,event-vMTQDisUTyARPVxYEZkNnsSVfQEilmkMFgYAFtpnJdbwqwRklG,3,czevbhnohjofqvywxcxjrjsgmqgtdczdwhgynnygjcggkohnxk,2,2008-01-01T00:00:00.123456Z,project-YOviZPpyAJFIIFIIoyfLTAHKXSZVoSfpxanbxJEihdwxXisDjJ,0,Programme,3,Migration,1,Multilateral,5,,5,,False,MM,GdQ,country-sWKQjZKUCvShUEciRJhtbzNoCwfudMPmLHoYXrmbfICRQfGzmF,3,Region,5,society-name-xzjTBxyxaswwtCJfnUCVAZCskZUBUAiLMfjntEHveLWyfaAOrA,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,2,2008-01-01T00:00:00.123456Z,2,2008-01-01T00:00:00.123456Z,regional-project-SgQLeEMkbjxjfpeaKAjWlEViVHStEAUvCYPSashjdPcMWlGkaz,4,,4,,False,UO,FFZ,country-XtuxyeWBJesEihSrvHAHnSnNdgKUOHfEUSMYTsBMuqHKNwiNKF,5,Representative Office,4,society-name-lNoTsmahbDOYhVnZNAAcvwJZOnaOmSsqYettGJuXahRvvzUKNb,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,3,public,Public\r
0,8680000,9,9,disaster-type-vuQziUHnpnTmKmUQYNxDJWYAxPtnzjEgIPCtXNAdmnvJkQyHBl,CbSnyKQlrVRKXjPzKYZmjAuDpViWFuNWNHVOcRgYefbadvfuwmVjntexNuLCEvTlstgZJkjkAhINAkJJOESrSphQjCgWciyEyEkXbLSxCLKlCbFQKwvfxeliNtRzjhYQmOusTYYfwMZFbNLAkxqmGrHbFukdPpStqCBvcrVWQDQfvJciNaVKbtymEyycSRrSyvxZGYBATviwUqJmFsrfCQfZQuGhbZiZWgpelxejKZpXfeaUaVZvNejLODOvYQgNhdTimVflfTfaBYRondTfyuOHmEmTFMTlEsURLdClGaflmqjIKmShSWemluWokzOLsMAGOsnBqwVpHaPRqsWkedeFwUdNWBfRWTCaVRfuLXxSRMReKqUuCwVZExFtWFuIVmoLkcSwADDuYzDDCjjVWyAbiYuyOjzxaBYQljLlngbzEjrvmbFzktJromFMUFBBkFQdwgeuTEMsjpHFZnAFatOkvOtRNBNhMiHsvUxZSixKEebCxApn,2008-01-01,6,7,6,event-ZgcxbNTjTVlifAhdCOTdugIrmPNVbvRuTkLUxHaQzAQQdemWGj,5,urflccrmmsgalovatrjwhvdksfkdfhfluflulobxkyanoxdfup,3,2008-01-01T00:00:00.123456Z,project-uSouOEYrJvKYvSmiuYOKoTLNppFKEbuGgyWjNufHFDMUreCyXm,1,Emergency Operation,2,CEA,1,Multilateral,7,,7,,False,Qg,FRE,country-GelPjwPUKvDTYirYWQtzePEyEMQlKTGXQHqiSuLLwLNzecbUko,1,Country,7,society-name-uWoXZUYpglUyWAedNqhcVeCWxMOblugSCyiOKJmmqFCRsomVkB,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,3,2008-01-01T00:00:00.123456Z,3,2008-01-01T00:00:00.123456Z,regional-project-uFuMImZPmMMhsUdVmHZGspYyBSatqnjsbbPPWAfxDXjCOyJkMC,6,,6,,False,kI,gen,country-qKGtToBkrfHyiVnzNdozlVJMeSDEuPPzykdZxPBmrggexMXvbp,3,Region,6,society-name-MaWtmJmOcprfKKcKYEcduftawWszGmuWzUwiSRgvAVGgGZXjbL,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,4,public,Public\r
0,9820000,12,12,disaster-type-MYypcqvTOmcyMYouUIGjrNovotacSYOVgGeTzCEGsGeBwlrqqQ,xqqBdInIxSeEMNnCTYJgaPRPWZUQupPMhjIDGGQqIVyZNKLBLHGXjWSMdtuELSiEgrCRiqyocZfUMIVyTqlrinJPoLCkHppKYgjhPQJFbzkKnlHGdTKJnkjhchalolabeSHyDByhcbGOMQJZRETyhaJfsmxyYfsdUpJsuPpPfLGWdYErAYWXJPimutALuRYgcamUXbDWzlaxrvVLyCevbScBBQyBrfeaPzxtfTfTosaZCIugzNLrXNEcHNaxXJWmBAJmsJjyIUKKNzkyMDYaHoIBJJHOKhEHRQPFYNexbxZLBlxDeKDybSMpibfiBSWwDOHKJlyatfJaWKxieYDxvGuhDFDsTfQViFsyMlYegIRZPJjrfMTLziBrlkjMEvGLeCdZTqUUxrigJwRsxFcuBXGiaKjixFaTKbUdeOzoTvArdDknirElGkJNuUYradfFHPHlkSqTCpfiAeyIYXxaEedYwJPSWdfhKxaNlDZgQfulBfVcVxoY,2008-01-01,8,10,8,event-zUoZjZgfgTMDHDUYhIdMmpLfORmFnizPuocAcUefWNWGFWuygD,7,gaxjuhaalnbzblgvxahjimhapsyveosfqusmhuaanrnzxnywid,4,2008-01-01T00:00:00.123456Z,project-CdKimccDeZBLuRaaEqSPfGKYtJTuSsoZPjZKHDALJKnAwiMqrE,0,Programme,6,Shelter,0,Bilateral,9,,9,,False,pF,FzL,country-tFUzdLtZqgjJoYopDjgSIGxAVzAKvtfpkNEQeXudBzBjAEbvxh,3,Region,9,society-name-nzBpspNZkvkMuLyfgffYVajIBFfYZSPjdaElcisxRRSwQKfckt,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,4,2008-01-01T00:00:00.123456Z,4,2008-01-01T00:00:00.123456Z,regional-project-cjwXJQNzoRleDsnYYUxCqHWpvjAHdzrIBcVBCmLJoTqtIGmJtl,8,,8,,False,kT,pfW,country-TMDskLiubhduJExjuUyJbOBPuzluNWcPsuKWKcGdUTTiFeeijg,5,Representative Office,8,society-name-xwvfAvWeFzIdHAPYzSjJfnCkhWqopdPRJbdPSoEccoWojiGuuy,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,5,public,Public\r
0,5800000,15,15,disaster-type-TrePaaMvoGvOuEVrlfzUrpuXLMbZcLXoEIeqRBdtFPOAVgsoDG,HqrnDdzUyfIWCPwAqADiRyWozJZYexQtSfHxHVMKcdjCESkKhaXHtvcSDPJybspxAWBcvcoTpCrBLGpnbzEPCQnbzESYhJilVlAAEKPrXfNbXGCGPGBvnGWvRMZcyEWnKAntRkSGSNGWEzbVuZOubQOtKiihSDdqPJBWSWeIzRUCbAznldWezWkKRaEmZLLlXGNfRKIkFhJjASuXnXZoDfDVaIBtNqkzLskbnTSLIRQpfRXputROMSbhswXKNACbyMleNvICmaxqMHkroJGVXrQYpZdSjYSRVeDUIhAEGayOyPrQoRhvPHLWWdgyPqXLUQjPGfvamCXchEdMjAOtcCdnbGOIcHOeDkzjHkMAJlPXstHuWbQbDjHGQLvKlPPDOrfeAIaBLRhUMyhkZEzziaJcHibpNhDdOWZlAmRqrrnuZMyOPlPqvHRFaflaVVsZQQjtkQxnAMbLfjoDxpalJrKCzTdpNyPWCaiWspyuiWStcwwoSWBq,2008-01-01,10,13,10,event-VECVykLZzLetonziLMKqyOYBqvdNLKLYbSchdIMJvEoKbIoRTv,9,kgtfimaqhsskpsyrvgxhtnwqnudlxckjxxfvotkwwhihvhldlj,5,2008-01-01T00:00:00.123456Z,project-GWfSICYxXrRbpzSrGIjhwTKCFpHxrTzAjmioBcyzZDMXNHAsLe,1,Emergency Operation,5,DRR,0,Bilateral,11,,11,,False,MU,EUn,country-tvWqsVotTqYeYtNhzKMLpWMpTqrLCsoKrAqbHWRQSJkjodLvGA,2,Cluster,11,society-name-KQIPXHLrgpkgaWKCidSlhEWcEutHwmsOTYAxvEZLiXicpactrK,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,5,2008-01-01T00:00:00.123456Z,5,2008-01-01T00:00:00.123456Z,regional-project-AKNiayAzeDKLAlmwyNLMQjLVMYUJpnuWJVEzJGDTFCNlxXBath,10,,10,,False,Rb,jvZ,country-dvvdCCrTdzxCNvwfxzknKlUaMcIvXugcFOStUbQMgogfgDXGyg,5,Representative Office,10,society-name-sTCRydRSlkObzTNxourSfRlafQilCuYYKwdakAWZSdfuhvnUlw,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,6,public,Public\r
0,2090000,18,18,disaster-type-gJNIQgaBeFnOZRTuApgAmgkMDxwClVWAgAMtMAnFJGefKnHSTL,PLLdzHkSdhWnPaFeBFwmYRSkhyoZSmAhZpeENHvrLcWctSMdpERkMwVsxHXvGovSApRMLJWhjErUnMOjjuXvgCZreMSVluJeOVqFAlgTlTmzZchSIzoKMqwqgnUXJquoguynXdMpaXZEMzHQVvXNcPLBSQtxYLIDiOrUcJVNMlSgDEOXmvPWfAzGeennNEmBCbESihEQoTsaTltiPkPkVrgSNHYUoZZdARplUpButagIgPYtsrksWJrjQQbkSrpZWxaSMtCAwSfhQVGBQevAraNZKsgtFwmNINTemDcutOitufRONdGlyeQXebPmuyuNrlVKLlcOlpEyTyBLQBMlXkKwooIyfKqfeOIYWmMRbNYoYYtirPOjsayBRlGVmrAmmZtRHIMopqnExgVHyBNqUcGBXZxZslspUJlyNiJvvbCrnvbKwkWJOHZNxMrEOapKBZMBsunuMgEzvcqDhZJHmacWLZLvriJGDnrsVUNPzQyHBBCLINLq,2008-01-01,12,16,12,event-SGCXZgaaOAAIMdRrZWgFiIjaEAkmGUhhwYQkiojJjllJjsaIrE,11,ujhmwmlmtcarfcuwjrcmzhoxygthpwqbxumuxcjkxphliaybsh,6,2008-01-01T00:00:00.123456Z,project-DbASgDSPbBLdfqNCffbWnZHqYTCgvzEwABUuaPveIUGBbRgyFQ,0,Programme,4,Health,1,Multilateral,13,,13,,False,ur,ZTI,country-xfZHZWfDIGjsXjyxvKtANJLbAjpiDUjoPEhCNGLbjkoERKdcTY,4,Country Office,13,society-name-OOCdQJrZDCLuTqeOYCAFuumLHeIINRcCVnDGewLeuFMdJLtxGM,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,6,2008-01-01T00:00:00.123456Z,6,2008-01-01T00:00:00.123456Z,regional-project-PvYAATKYoFvtciTVqlYJBeESILkvZChtcivdRpIuTFBVlWytGY,12,,12,,False,ZK,Fuj,country-ZqMpgumMHVmWMfjizabaestdPQSDzjNUVeYtVPQocsUKenthbn,5,Representative Office,12,society-name-OIEicLNIBPuQytkVYQSisavNTPjdHlovobKFBBMZgNqJNziKXI,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,7,public,Public\r
0,5590000,21,21,disaster-type-qHbuogyciTiCOtppdnCRlZPTWFeIAOPkstDwAmeZZgiOenISaF,IlJFIWZdzAeuStwNGvGzyowBuTsfHbkOJRHlviekQHTIyBLcuNryLTMHWtlIGkSIsCcvjcpfQoRkNIJDfYUWknVkbnByHBsiYCVEIyiBISQXvlEjHDVybUpjaGECJorCfVaAlQIoorOOwWWOTxEpvBlmPiZCFPTXcdqvnvHwTLEndiXDoVOQikJwZCbtTkYqcWUjvvvsAHMUYSRoLYCDPcsggAEJIexYLAOYszPDoHzYvyMatrGQqVQBFVonlTlNeSksIMvwIDSCbaQBkpRNquLLRrkArcFAbOJMundfiTdopKGbShpUGFfWyjIopwBJNduJXecIRbhxnnDrZmuzDbiOPCFkGXDeuyxMBQNxDSLQswFvKvNKxxbvuPpSOyiKTOfChtGxseJoNwkSuiVQxjZdDQXHPGkXWezPugeNOTlftxFsTsujdZncYZQiEOyWNqDmbGUXJjtdmUxRplUfYkVssaVSlLmXBosPYYbKqflZTfJcxTQk,2008-01-01,14,19,14,event-hVAieQQIQxTBpuiaXaDBeucsjduMJQyGZwQPAMCDetmRnSBbGc,13,vwlcgcfswwaugdunmjfghgjgimncrzzqhypjhhagetiuwfhrwa,7,2008-01-01T00:00:00.123456Z,project-wEKuLKdTbsEMqfiZPpjutAafJMfYhnZtVUoqZGTxEemnMXRNBS,1,Emergency Operation,7,NS Strengthening,0,Bilateral,15,,15,,False,No,BzR,country-LBCzRpwmYBFpxRYwTHMAcFdDiiIInrXfnoZwgWmNaermdMDtkF,3,Region,15,society-name-ouETXUKACXeSrHbmTXQaQdDRUoZxXOBxJjybGlvlQApUEZLqTX,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,7,2008-01-01T00:00:00.123456Z,7,2008-01-01T00:00:00.123456Z,regional-project-bXkNfSTnGfocfsLtJckNHMdJIPHTeLyRAtZxkmhKgRKLcGjeQn,14,,14,,False,yu,Ajd,country-sKpWVAJdQymuGwobUfbXfWjCJKyMvfZNPnaWsPGxjTFDwHyWEd,2,Cluster,14,society-name-mVBnqtRsnOMqzGXMyVVTpogIeRjmoxCRAfETVdCohCtrwDDBlR,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,8,public,Public\r
0,3440000,24,24,disaster-type-pWDrmUjwyZREsbYYSvnyiufPQjnhevqgOehLbOibyaFgpVzPLn,dYcxileRtqkPBYCPpVWxmJqQiuXBhhAgRuQWNKTNtrVjAYSfIrvunCWXuIjzHiUPNxdIgrNLQtclZmimwJxLowGdSnQVOvPkGHbvbZFucFTQGfLROCZnxqYYsiwlrTSEFFEqsXrKyqYLpctBsZddBayKIGiytIBiVQDxZxZnFDLoYJwPsPZybLgihbqbDkxqZwUmMBcfWBdKNojOVqDbCKjzixQYgTEsmhRzXdnixdPoVRSXLtpROMGHqrjDJKwjRpBfYFLqKAUqvZtMSVwTNwDUGhlCUmUgFTsRUQZjCUgHoijRrbknMnzQiEygDArTbXQrcrUyvQxgfkJyoGfhbwaiTZiITMkcEXPsROvLwkYHTiCXAFEYrlnNnuSqnWoODmUYiTCHnMAXVLlfwhcaiyaFCWkeqmOOqSHyKQYyYvnFexwEphbwlaJKJmeJDobQZKxdENnoDCogiNEmrfVtHvdXkRSDQxMOSbHjAITbaMdEjlbJPOEf,2008-01-01,16,22,16,event-QsSRasqNiElGdNamhCJGpYQYyZqpVfBFVHuVNGrqrcJJQKuVLn,15,bmlocdoxbatvjbnnxdhvxknpcimmqnzymobmkpwzwqapbcmplh,8,2008-01-01T00:00:00.123456Z,project-kWhHLWrwlpMPSuKAXcipneuZNXNHUDwhDxCYNbmkmaJHIdYBaM,1,Emergency Operation,1,PGI,1,Multilateral,17,,17,,False,Cf,GBY,country-EmYHagbelsZwDgIfxJdyVPZfMsMKXLhmzOYUxcwvhKgQVZLoKA,5,Representative Office,17,society-name-QFeEaIaPtNjMnTkWJTYxbFSgMBfjLonieWmrKwkicKXZqcQdnE,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,8,2008-01-01T00:00:00.123456Z,8,2008-01-01T00:00:00.123456Z,regional-project-PwHSYFuvRIvaLvKWgtvcsNClpzANsRziClGBvgIhsXSictYoPJ,16,,16,,False,eq,HEX,country-ngCjoWBOzFdtTSeEfaPnSJKfNhGYWEscubhpUnYkbWprZqLxBb,4,Country Office,16,society-name-zwdTFDwWTjwTPDjoeyWVnhzbmQFPGUefPQVXduXSWCbmWKNyXn,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,9,public,Public\r
0,5360000,27,27,disaster-type-OSYQZaQGaaTqOwGSElrkQlERPsUSLzBwTQiNtHmcwhDhLDjVve,lPnqnWpuoBDxRCREFCnqUYiyZXvIEudnQeatTPLCMfqaEEeOROlGbYAfQKMcEqzzTAMWFQrEjYVfDhWksXoxyBGQZpYVdnjwWmyKxTjxuICUVyFnuUaEJWfVdQFlHSoPMtZDyrUAVRelRyfqNSOYMnQzQpgXKzlCvzStqoLWcLueOMvzznbdPzmyjThYdwReyqdCGDVZTPdtGgfnVPxWWmSUEVOQOpMAxkEOkWZMuLVIzCDESdvxtHLLTXcEflSLMyMWMgusTJlEadQiKpnXSgnizGKmEqAbkepBWIIsexFEfSiVMeHrlSOPxeULwYAWfEBQxvJMkjoSxxiSIuJFQbBmaYQjXjJXTlMoZpwjICHNFgxUmwZMPAtFkAHQtVFrArRxucDRjHpgWahJwURdHIdIEuzVtwWbVRvIhPauHagaJPJRAFMFZqqFBfLnCIZXUJBymyYOsyWvpootCCrVKAomEKjjYSBkGhNewalnFsnJOFpsuduk,2008-01-01,18,25,18,event-kEnbnWitXHlTCtSynVYuiRUoYvAfhJGSWjapIaRBRTULvGQAiQ,17,ejvmpqetggpkgwfdfymbznozbyzozpuntelgeppkaulgrvammr,9,2008-01-01T00:00:00.123456Z,project-hMsauOaqEiWAbNEPKBkMerwLFCpAybKIWVuLhMJfCWtFUoyBxn,1,Emergency Operation,7,NS Strengthening,2,Domestic,19,,19,,False,Ra,xYm,country-bgVWfzCGhhZBDYVIAViMalugvmGzqWkBCoXbkkcNKtfERZvnPb,3,Region,19,society-name-eMHrXedQvbCuYuaHqGukJsAFCdoYFGqBCNFdUaJPUobPCzrQsc,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,9,2008-01-01T00:00:00.123456Z,9,2008-01-01T00:00:00.123456Z,regional-project-qYUMyeBpKulvEqEEErpCOkfjoGrGDCxyeYNfJWKHEvxFLQIoiU,18,,18,,False,sf,GCN,country-zjgFyqQmsMmKsgBYTWyCqcCJRJRSAKGVSxIuCrNeWfdzPZBDPj,4,Country Office,18,society-name-pPLCINunDEdekrKnhBVrwRQMHjqpCIarCascEOLmyweZGCxzYL,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,10,public,Public\r
0,5670000,30,30,disaster-type-OaxyMvPPWAluOcRLyNteinukJHINLRYaRJGWWHyWbHefaDgsMV,lnTzbpXAGbGPvJQGsqYXrnZFiXhmlBYTTFFAnJYoXeTLeRGdZtoGtSpcXLEKFvXyGTYqlhJhJWceZHVErDkMfTSoghkywNSCtyandiRngieFHhCYWbtlTpiFuHIJffIuNZkbAnbqhywiDkzfJKgaKwogcbeDMQlWueozOkjmIPbenQCclbKPJfMtaeWryNyfTpzcDFjFkcOVsxdSTKJaBVnSRwopnxbhzTlAiuectKryhFpcxQeZUvgnoQibLzCmdLYjsaEtfOmvKORAAvppKdoYyoQHxErmoMgLuGbSabYJtgzjRyFxcfTtBHpPhrzxaYboKqXOxxGTRUTsyVsPkdgGgWPMbinkagywgMHJMazVbMhFXwcDvhVLkyDEOwZbrzgzPkQjROGOsmUMRBwBIVOJWOFYkajaqJFfboyYRvosFyWsfqsYjUTVEhRLCsvnesxLxwaJddjONbBULwtEmuBqiZCSiLqnAOfcYNbKHkqudPHhqTBQ,2008-01-01,20,28,20,event-eTaDZgKeiMXZrpYSpDdlBxCHgsNzoZwubfLnxneQfbhUuGtxzC,19,ofoedscusteqsdrkmfcxabzfoalgtscndnpmezoqcfagqskkak,10,2008-01-01T00:00:00.123456Z,project-tCcjmAaCshFdYBaklxkvumQQfmqVfCAllIbKwteFxrRcgypCNc,1,Emergency Operation,8,Education,1,Multilateral,21,,21,,False,Yu,aBc,country-jiodPBsiVeYfBGqzdoHZMZwgOSvNjprSBzujeWFsBqumWogBWr,5,Representative Office,21,society-name-XuPsggSnEPgoPRsPBVYpOgWRaFIMRcOEIBKRVuCVydhJZXHoar,"gRoEbNJuNo, nPOMbdYvpi","1, 2","False, True","True, True","district-uVAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOx, district-cctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgRxIPwdzrmhDfQ",0,0,0,0,10,2008-01-01T00:00:00.123456Z,10,2008-01-01T00:00:00.123456Z,regional-project-WWIkZLBPQwBgiZdYysyrUAEyqDJwykvdJqwdVRePtpYKLKjwDa,20,,20,,False,bK,zZk,country-uswVhCoyuJxscuUKeKortlsAiQVEgimNopdXWAvpmxYmTxNEuL,5,Representative Office,20,society-name-GlUThMzaHFJFWOuOEGPJjXSYEmDBpdLEDoLPGUpByAbKFQKFGZ,"0, 1","WASH, PGI",2008-01-01,1,Ongoing,0,0,0,0,11,public,Public\r
'''

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
    'name': 'Mock Project for Update API Test',
    'operation_type': 1,
    'operation_type_display': 'Emergency Operation',
    'primary_sector': 7,
    'primary_sector_display': 'NS Strengthening',
    'programme_type': 1,
    'programme_type_display': 'Multilateral',
    'project_country': 3,
    'project_country_detail': {
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

snapshots['TestProjectAPI::test_global_project_api 1'] = {
    'ns_with_ongoing_activities': 16,
    'projects_per_programme_type': [
        {
            'count': 7,
            'programme_type': 0,
            'programme_type_display': 'Bilateral'
        },
        {
            'count': 5,
            'programme_type': 1,
            'programme_type_display': 'Multilateral'
        },
        {
            'count': 4,
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
            'secondary_sector': '14',
            'secondary_sector_display': 'RCCE'
        },
        {
            'count': 4,
            'secondary_sector': '9',
            'secondary_sector_display': 'Livelihoods and basic needs'
        }
    ],
    'projects_per_sector': [
        {
            'count': 2,
            'primary_sector': 0,
            'primary_sector_display': 'WASH'
        },
        {
            'count': 2,
            'primary_sector': 2,
            'primary_sector_display': 'CEA'
        },
        {
            'count': 2,
            'primary_sector': 3,
            'primary_sector_display': 'Migration'
        },
        {
            'count': 1,
            'primary_sector': 4,
            'primary_sector_display': 'Health'
        },
        {
            'count': 2,
            'primary_sector': 5,
            'primary_sector_display': 'DRR'
        },
        {
            'count': 2,
            'primary_sector': 6,
            'primary_sector_display': 'Shelter'
        },
        {
            'count': 2,
            'primary_sector': 8,
            'primary_sector_display': 'Education'
        },
        {
            'count': 3,
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
            'budget_amount_total': 8870000,
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
                    'primary_sector': 2,
                    'primary_sector_display': 'CEA'
                }
            ],
            'society_name': 'society-name-PXGvvlqvZFXJDQgQvWHqeYxBPbIigoDhhJTsiwtCBJfGlzGmjR',
            'target_total': 0
        },
        {
            'budget_amount_total': 150000,
            'id': 11,
            'iso3': 'Ixy',
            'name': 'country-HivaKQuijMsyibLmSxwUyYeZVVPaZnTQKMwiXSLFbXgoDhjrmB',
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
            'society_name': 'society-name-tWinbqeVXjbjEdBhxNkEoJFrdkMNdCUUfBBLbAoiisHPgvuqkR',
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
            'budget_amount_total': 1340000,
            'id': 21,
            'iso3': 'Nqq',
            'name': 'country-WJNPIGxPkqKRLeNzbOHsgUSwRJXvxmDTodTYrnDAnhHuxKzFbF',
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
            'society_name': 'society-name-JTgrVtaadVUrcYCxAcjpXhdUBtXcCXMFkLAHVklUJGQvVYtjDn',
            'target_total': 0
        },
        {
            'budget_amount_total': 8670000,
            'id': 23,
            'iso3': 'Qnl',
            'name': 'country-bVEnSUhjHkeOgYelztOjgQGfuqqXFJGLnXDODdFdxbCbNxPUbO',
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
            'society_name': 'society-name-CzlqTQWmiBvCjaXFMHdqVFcEGNYVPpCMHFFQvkSPmNLNBmyKZg',
            'target_total': 0
        },
        {
            'budget_amount_total': 5380000,
            'id': 25,
            'iso3': 'GvC',
            'name': 'country-LjfTHLuyIGZzqNKnmQLCrwmMeIcloIsJCAfYOttqoUToQRXCoy',
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
                    'primary_sector': 9,
                    'primary_sector_display': 'Livelihoods and basic needs'
                }
            ],
            'society_name': 'society-name-voXVDMtCzWngHTnPqlTKbaksLkPFIYvkmszUQfueYkhWBFzVaH',
            'target_total': 0
        },
        {
            'budget_amount_total': 2600000,
            'id': 27,
            'iso3': 'SWK',
            'name': 'country-rWkcUCAxgZonvlKsMxEBdpTOWKASebIrYORKkWTLEdtXunHBIC',
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
            'society_name': 'society-name-CAFyjhOmvtOuzWerUohwVmQGOmRtJPKLTxpeldcHXvKctdXblr',
            'target_total': 0
        },
        {
            'budget_amount_total': 3170000,
            'id': 29,
            'iso3': 'hWX',
            'name': 'country-yVzFwSjqPtlapgXuELLFazwYJegirxWdYECJoBoucRZNAVGdgK',
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
                    'primary_sector': 4,
                    'primary_sector_display': 'Health'
                }
            ],
            'society_name': 'society-name-AAknMPowlAafDOClAvvGeniYBgmvPYqiCafQJinmPXiPOddkuR',
            'target_total': 0
        },
        {
            'budget_amount_total': 2600000,
            'id': 31,
            'iso3': 'Ece',
            'name': 'country-ervxcfkMbqpfkHBIBBDCwyszNZGXQmypnWjcKsHVgAGwmfLLQM',
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
            'society_name': 'society-name-WtyhGEdYOTkESoNirZyDIXoftSYyrkvXbGZHUlpjXqOmNAKBOU',
            'target_total': 0
        },
        {
            'budget_amount_total': 6000000,
            'id': 33,
            'iso3': 'rZn',
            'name': 'country-MLvoRjfavNEGPtQYlQIfZsPpOuhTPNPtSThNKDMYIfFApbQgMP',
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
            'society_name': 'society-name-UhBSCdfQshatRJHibAqQwyjPObObNJmOlTFmBXxjPSQKnNDixO',
            'target_total': 0
        },
        {
            'budget_amount_total': 2330000,
            'id': 35,
            'iso3': 'KNS',
            'name': 'country-sXHvwhvOCcmqmsYKfCZeQddoPOvFOcvIoPoPYtLrpOFsFxdBnz',
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
                    'primary_sector': 2,
                    'primary_sector_display': 'CEA'
                }
            ],
            'society_name': 'society-name-lGzUnyLPRoqRfeZxiwArYgPzwdBsnTobwsdWUzKBxgrGjyJlDj',
            'target_total': 0
        }
    ]
}
