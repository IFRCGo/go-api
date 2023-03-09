# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TXestProjectAPI::test_personnel_csv_api 1'] = '''event_id,event_glide_id,event_name,event_ifrc_severity_level,event_disaster_type,event_country_name,event_country_iso3,event_country_nationalsociety,event_country_regionname,role,type,name,deployed_id,deployed_to_name,deployed_to_iso3,deployed_to_nationalsociety,deployed_to_regionname,deployed_from_name,deployed_from_iso3,deployed_from_nationalsociety,deployed_from_regionname,start_date,end_date,ongoing,is_active,molnix_id,molnix_sector,molnix_role_profile,molnix_language,molnix_region,molnix_scope,molnix_modality,molnix_operation\r
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

snapshots['TestProjectAPI::test_global_project_api 1'] = {
    'results': [
        {
            'budget_amount_total': 3080000,
            'id': 5,
            'iso3': 'FBn',
            'name': 'country-KrFlWGrzoWKidHZBEIcGwzRXlDhSHDuSaaRnyLguxNqlJqprEN',
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
                    'primary_sector_display': 'sect-yEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjl'
                }
            ],
            'society_name': 'society-name-ASWxxzrClKiKRogUrZpJBymjZVjEZalAFiOHIUuYFtqJKdzgSk',
            'target_total': 0
        },
        {
            'budget_amount_total': 8720000,
            'id': 7,
            'iso3': 'tGS',
            'name': 'country-mVhKxiuyKVatdLImyBuXxZRYiHQMLogzaIDujsoFRDjMsjVQZS',
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
                    'primary_sector_display': 'sect-yEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjl'
                }
            ],
            'society_name': 'society-name-hrTKEOnFsTydZvjTnUZoSVdXlFUztQkbJzvBREwWzzeHUssSmS',
            'target_total': 0
        },
        {
            'budget_amount_total': 9220000,
            'id': 9,
            'iso3': 'weU',
            'name': 'country-weSiuSpYILigYGTEIugZMoUwTSPJoDrKdDNCFLBekbJCJPdwET',
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
                    'primary_sector_display': 'sect-yEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjl'
                }
            ],
            'society_name': 'society-name-rKqUbTMFBTWiznQCtISRtvoKZGAjXIRLuaNdTWwLhXeNeHAUkU',
            'target_total': 0
        },
        {
            'budget_amount_total': 620000,
            'id': 11,
            'iso3': 'QQP',
            'name': 'country-JGjDUWzLQEQOdrcLwoThqYfYLBhwBcFJPplFsRZSJJovUywgXD',
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
                    'primary_sector_display': 'sect-yEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjl'
                }
            ],
            'society_name': 'society-name-zlsOcMASOsNyyIpUqNBbrCGtjeCajJvgyjkwLWpOArIIiaGKYX',
            'target_total': 0
        },
        {
            'budget_amount_total': 1900000,
            'id': 13,
            'iso3': 'ovs',
            'name': 'country-bkcIaQTgKkMcklXexXtpNcrqIKcLolkwmpnlakpwecjZxPZvwd',
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
                    'primary_sector_display': 'sect-yEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjl'
                }
            ],
            'society_name': 'society-name-vYTRcozLGJZJsSYnNmWXpmkspzkLBiaZIbwKVVIPohiYrWrfkL',
            'target_total': 0
        },
        {
            'budget_amount_total': 9390000,
            'id': 15,
            'iso3': 'qiE',
            'name': 'country-vUNLIjiRTUACoRZglWnrYoXHJHctGwfQsPjdjxMpztxcRjJlYU',
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
                    'primary_sector_display': 'sect-yEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjl'
                }
            ],
            'society_name': 'society-name-xXxCyDlMNehTvsLbVsOqmfHTmPtpBNxoYfcRPkQLEEhRPgubAj',
            'target_total': 0
        },
        {
            'budget_amount_total': 8140000,
            'id': 17,
            'iso3': 'bPB',
            'name': 'country-DXdusNJuFVIICYkJjdzmjkSQHSVVbfkAKJdsqATAxGLuiVrFAa',
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
                    'primary_sector_display': 'sect-yEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjl'
                }
            ],
            'society_name': 'society-name-qCjSOqvlxDnCJDSqEFJIqaCaZSSMrAuEDDXdBfjNGGMDjItjzH',
            'target_total': 0
        },
        {
            'budget_amount_total': 6020000,
            'id': 19,
            'iso3': 'Tgb',
            'name': 'country-YwDyGATAiXepIaZuLweNXqJrVwrVkkxLvvgmmTcVuNewsgLAnQ',
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
                    'primary_sector_display': 'sect-yEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjl'
                }
            ],
            'society_name': 'society-name-MAFtvgRoZBozWwUMavUbqeFpFjjpqiASFGYZDcTmRlnOIhiHfC',
            'target_total': 0
        },
        {
            'budget_amount_total': 3180000,
            'id': 21,
            'iso3': 'JVh',
            'name': 'country-XJMQqpCXYtJQWPUUhZizGhFWMpaUaHbuGIZLMavPGcIhrbmnsT',
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
                    'primary_sector_display': 'sect-yEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjl'
                }
            ],
            'society_name': 'society-name-SUdvyTovPHUQBZZLLcOlgXpegASAKtAbiOeksBCBXqjGhjTRUU',
            'target_total': 0
        },
        {
            'budget_amount_total': 4650000,
            'id': 23,
            'iso3': 'BlC',
            'name': 'country-RmgMKsACcKNyRdJDrNAejjMGobGQWFIHtTECKIGGjqXnDwNzHV',
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
                    'primary_sector_display': 'sect-yEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjl'
                }
            ],
            'society_name': 'society-name-qGlSoaXcKTCeuqFvLwbhZmWZnyCjUQfeuyCWUHerbIkIlsWztM',
            'target_total': 0
        },
        {
            'budget_amount_total': 1470000,
            'id': 25,
            'iso3': 'QlF',
            'name': 'country-HorPPXrobiLNSQDTpJutrlZrdjNXqIWatSBGHySUONTJONcITC',
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
                    'primary_sector_display': 'sect-yEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjl'
                }
            ],
            'society_name': 'society-name-ktCZDghwCJDmEYIfvAhzkeVFnyEfpVHUFmesbSOneKShzBAXTh',
            'target_total': 0
        },
        {
            'budget_amount_total': 2620000,
            'id': 27,
            'iso3': 'ZXI',
            'name': 'country-ONpEIFoUOxihLMHbyHqMzbQmnslMXNUwdIzDjUjAQOBlIfdCzC',
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
                    'primary_sector_display': 'sect-yEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjl'
                }
            ],
            'society_name': 'society-name-ACQToSMEeIeMcwPKCqBGYKKoncxnSFrcQBkqiyhdTppjrJSEFm',
            'target_total': 0
        },
        {
            'budget_amount_total': 9670000,
            'id': 29,
            'iso3': 'AYD',
            'name': 'country-hOxDiNVLfqiyTdEeomYLfroIiCzYsQzhXinUMwuqxVOjvUKXhn',
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
                    'primary_sector_display': 'sect-yEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjl'
                }
            ],
            'society_name': 'society-name-COQndNRDJbpNNUnqzJzkdTEvnKhMfWQYOLmJkHRKfGUnUuaCpN',
            'target_total': 0
        },
        {
            'budget_amount_total': 9950000,
            'id': 31,
            'iso3': 'Joo',
            'name': 'country-pkjxFdkhgAIVyzQckIMQSlHfqNGMzwBQLQgTEJhWxqRWJSmyZf',
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
                    'primary_sector_display': 'sect-yEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjl'
                }
            ],
            'society_name': 'society-name-yyWOXtsLmsDSsodosPjBDJVXrZvZzBUegXvwzJPeAaMytQdxCG',
            'target_total': 0
        },
        {
            'budget_amount_total': 1540000,
            'id': 33,
            'iso3': 'KAD',
            'name': 'country-qyUCnvNjSGmURNyZjxWEDqSgQzhZBxARzWuDztaznpywvGzhCh',
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
                    'primary_sector_display': 'sect-yEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjl'
                }
            ],
            'society_name': 'society-name-KyMoNlrLPAjotsmBMlGufwAlTHnFMXsCCOseFVnoSpAVdhdEIB',
            'target_total': 0
        },
        {
            'budget_amount_total': 7770000,
            'id': 35,
            'iso3': 'dCs',
            'name': 'country-ghWYeodZInjVflgXBgWYPCAiwfWYKDnRgObjYOQMHOpngjBuZj',
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
                    'primary_sector_display': 'sect-yEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjl'
                }
            ],
            'society_name': 'society-name-ZWNIJQPIEeawqHscrYpZJddIyAAvHPeunNpyjjpXpNnyrXBKwr',
            'target_total': 0
        }
    ]
}

snapshots['TestProjectAPI::test_global_project_api 2'] = {
    'results': [
        {
            'budget_amount_total': 3080000,
            'id': 5,
            'iso3': 'FBn',
            'name': 'country-KrFlWGrzoWKidHZBEIcGwzRXlDhSHDuSaaRnyLguxNqlJqprEN',
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
            'budget_amount_total': 6630000,
            'id': 13,
            'iso3': 'poQ',
            'name': 'country-XqYksnSVShNIoKisIsGeobatgVBMZZeauocjgxeyEUxWZTJySs',
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
            'society_name': 'society-name-NvotJffaubhWrFAqXjFGZLYBhuEpJvuVWhiIXeCFvZgioLxWKF',
            'target_total': 0
        },
        {
            'budget_amount_total': 1200000,
            'id': 15,
            'iso3': 'wzw',
            'name': 'country-aDsLLpZuKIgiuvNEEDjBuMFysbJmJxVIbubeTshXCgXyvEJLmK',
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
            'society_name': 'society-name-ZfIICfPhtHBcdPxXcaTMlqrMTOlHCJFwODdOoPbXjLmbhgUjvO',
            'target_total': 0
        },
        {
            'budget_amount_total': 1610000,
            'id': 17,
            'iso3': 'vSz',
            'name': 'country-lhXnmyTHMXydaGmrDBRVeiQGOKHLNUoaRFrygVhVpUKMWOEKMi',
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
            'society_name': 'society-name-dYonHRFVIHRwjGxUPJNGzGPgIXXqXpKDzSpdTKaPaEpFLsNLNY',
            'target_total': 0
        },
        {
            'budget_amount_total': 8290000,
            'id': 19,
            'iso3': 'ovT',
            'name': 'country-IONANNPhnjWOLpxCunHtYGOegfuTFcmtDxzdPfAsRkyltvusAk',
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
            'society_name': 'society-name-qYyNTSkjQpKsaFfWCpQsoryydZNvqERdUQdAdYYpKHedCKXwgz',
            'target_total': 0
        },
        {
            'budget_amount_total': 5920000,
            'id': 21,
            'iso3': 'hBW',
            'name': 'country-hkFWJNPIGxPkqKRLeNzbOHsgUSwRJXvxmDTodTYrnDAnhHuxKz',
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
            'society_name': 'society-name-NqqJTgrVtaadVUrcYCxAcjpXhdUBtXcCXMFkLAHVklUJGQvVYt',
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
            'budget_amount_total': 7050000,
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
                    'primary_sector': 0,
                    'primary_sector_display': 'WASH'
                }
            ],
            'society_name': 'society-name-DCwyszNZGXQmypnWjcKsHVgAGwmfLLQMaSHEceWtyhGEdYOTkE',
            'target_total': 0
        },
        {
            'budget_amount_total': 4260000,
            'id': 33,
            'iso3': 'PNP',
            'name': 'country-TIuGhslFoucligTrYZNfzfdSWfMLvoRjfavNEGPtQYlQIfZsPp',
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
            'society_name': 'society-name-tSThNKDMYIfFApbQgMPVWggwrZnUhBSCdfQshatRJHibAqQwyj',
            'target_total': 0
        },
        {
            'budget_amount_total': 3040000,
            'id': 35,
            'iso3': 'PYt',
            'name': 'country-fdGdNQeaEPjKNUBFklsXHvwhvOCcmqmsYKfCZeQddoPOvFOcvI',
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
            'society_name': 'society-name-LrpOFsFxdBnzJvnKNSlGzUnyLPRoqRfeZxiwArYgPzwdBsnTob',
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
    'primary_sector_display': 'sect-ttUXCsOlhimaNWqaDFFIZaMFpnLQEDACfMMapJrNOJndljdPwc',
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
        'sect-tag-SnNdgKUOHfEUSMYTsBMuqHKNwiNKFHUOFFZlNoTsmahbDOYhVn',
        'sect-tag-DYAVdHtKURuJIbnKRvZYwejrbvyOIkKMylMhYWtTuTcrAfFpxC'
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

snapshots['TestProjectAPI::test_project_csv_api 1'] = '''actual_expenditure,budget_amount,description,document,dtype,dtype_detail.id,dtype_detail.name,dtype_detail.summary,end_date,event,event_detail.dtype,event_detail.emergency_response_contact_email,event_detail.id,event_detail.name,event_detail.parent_event,event_detail.slug,id,modified_at,modified_by,modified_by_detail,name,operation_type,operation_type_display,primary_sector,primary_sector_display,programme_type,programme_type_display,project_country,project_country_detail.average_household_size,project_country_detail.fdrs,project_country_detail.id,project_country_detail.independent,project_country_detail.is_deprecated,project_country_detail.iso,project_country_detail.iso3,project_country_detail.name,project_country_detail.record_type,project_country_detail.record_type_display,project_country_detail.region,project_country_detail.society_name,project_districts_detail.code,project_districts_detail.id,project_districts_detail.is_deprecated,project_districts_detail.is_enclave,project_districts_detail.name,reached_female,reached_male,reached_other,reached_total,regional_project,regional_project_detail.created_at,regional_project_detail.id,regional_project_detail.modified_at,regional_project_detail.name,reporting_ns,reporting_ns_contact_email,reporting_ns_contact_name,reporting_ns_contact_role,reporting_ns_detail.average_household_size,reporting_ns_detail.fdrs,reporting_ns_detail.id,reporting_ns_detail.independent,reporting_ns_detail.is_deprecated,reporting_ns_detail.iso,reporting_ns_detail.iso3,reporting_ns_detail.name,reporting_ns_detail.record_type,reporting_ns_detail.record_type_display,reporting_ns_detail.region,reporting_ns_detail.society_name,secondary_sectors,secondary_sectors_display,start_date,status,status_display,target_female,target_male,target_other,target_total,user,visibility,visibility_display\r
0,3410000,,,3,3,disaster-type-eyQrQQxgbsPyoyGTguFMIflmGDJTbcpHtvFzVkbwRwwOtpGrZd,OqybJrojvzQifUyHRNORoApKjBtMvCIinPiLIRZmitSTHiBXjPKkueJIUhlujUbWuAAtCVOVrjXmgilbWNNrMKNoMooRbwfSXEiGMETPxlyFEikmocAWarAoVQmWnelCNFSuDpBzXcMVyUuzNVKMIHPTYcHgCDcpHIzVcJyHWOdmsCztXsDkBsNdSHjDPCfUGhlXLSIizAuCblDLTmDfquSPTYkTUhfhTCOxfHTyUYGNkyJycXkvKQjkjlXTdAttUXCsOlhimaNWqaDFFIZaMFpnLQEDACfMMapJrNOJndljdPwcjcQKMtvfdgAlkRsNQSSMKYJlDVLxcfXtuxyeWBJesEihSrvHAHnSnNdgKUOHfEUSMYTsBMuqHKNwiNKFHUOFFZlNoTsmahbDOYhVnZNAAcvwJZOnaOmSsqYettGJuXahRvvzUKNblmvvREEZcPiEjODIvDYAVdHtKURuJIbnKRvZYwejrbvyOIkKMylMhYWtTuTc,2008-01-01,2,1,,2,event-htYzEFQqfPIylxyxlCcqCDqorKdjWSQgfQwZIAWLoJdyHAIREK,1,petfztcgkhzkrnjhwclknzmicbfrbmojmquuzefyjzjurhdays,1,2008-01-01T00:00:00.123456Z,,,project-rAfFpxCtnHtlhxYcXmfCGbZEGjmvEUHtXujXgHRinUcDyTHhat,0,Programme,1,sect-gRoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcS,0,Bilateral,3,,,3,,False,BP,YvK,country-rIsbGSRBZlggHjpmNHqwrYzfxzDKpSotRfPPWcfzyyJEdOaSkf,4,Country Office,3,society-name-gHconSKErceRrIKQclubnLjWTzetkKpKyRIvyWViYSUfGVwdgB,"euKBKzTOAs, kWNdRfrCQB","2, 1","False, False","True, False","district-hwBhsRRLFHQtcozMdantnXiWqsuhaFVBliyIToGJQZwezVcBbD, district-JXNNRPJbMQSrblrSWtvwaljKQzejVObfVHnyADvkxtUuXKMfdj",0,0,0,0,1,2008-01-01T00:00:00.123456Z,1,2008-01-01T00:00:00.123456Z,regional-project-srIuXCQhrjkrhaNJGgnIwJurjTZsKpketNvICdibERdgydfBzl,2,,,,,,2,,False,WL,CRK,country-SxfBgpBLzHfztVvovXkeGOhHGmXwwUPjpgjqmlMjWWPelXOFDW,5,Representative Office,2,society-name-PONuOujCeECOtYrLdwGetDCcdxsePfNMGyDLJYVcCZKPmuMEGj,"1, 2","sect-tag-ZlhQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRg, sect-tag-jREefffBgVVxZiJdLJJvQhAwQWBUdsMtwgKGnjQEogwJxhWrKo",2008-01-01,1,Ongoing,0,0,0,0,2,public,Public\r
0,2690000,,,6,6,disaster-type-pscOjrirYdPpnIhaPwOMxufTJqUiANsudOawoUrlqbIQXXLgUV,SyPqOOMJnCournLOZWzjCoUUBxjEfFlDllmKFUlPsbtklzRMmejeBpDPzgUHiUWZaMgyybhaWPcipXfrjOMaYaYgIVvTfmiEWKCktvEjpdISrOIhbcgIsgGAjaoboByjwPsoRyRThFkhogsweNvhxfcMjlBHvMlRBjQRtNswgrFQxqZTZeYajXPjujyCUYYEehKBUrjfuilXywuFBESAMYOviZPpyAJFIIFIIoyfLTAHKXSZVoSfpxanbxJEihdwxXisDjJApnodVihSTjyUbSBxdSgQLeEMkbjxjfpeaKAjWlEViVHStEAUvCYPSashjdPcMWlGkazBRDJTqKGtToBkrfHyiVnzNdozlVJMeSDEuPPzykdZxPBmrggexMXvbpskIgenMaWtmJmOcprfKKcKYEcduftawWszGmuWzUwiSRgvAVGgGZXjbLYyELcskjRDfOfTonZRPjXTkGHUMPHXvCYivsxNBcTXRypnNMejKOFgZajX,2008-01-01,4,4,,4,event-YTKRiTyHVpguHLmXxDgjTBAffdBiEnCexRHzLJHXzqLFOBCSFU,3,akjgiftditghhsndecvkjxhmahhxkschjhxtxtsfbyjjyladts,2,2008-01-01T00:00:00.123456Z,,,project-tJZYfFgDukskerKxwfelTXDqEqWCPihKFcxszANRiCxGNuxfRA,1,Emergency Operation,1,sect-gRoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcS,2,Domestic,5,,,5,,False,Hn,Tms,country-WBcmgcYQGLdEhqcetQaWgYhMnLmlQwbfjVrLwwkGXUNpGKegLW,1,Country,5,society-name-kWIaUgnGTExSLlCRglwyBnGoAhWuhDhHiFWxTsJUcfuFhysDMV,"euKBKzTOAs, kWNdRfrCQB","2, 1","False, False","True, False","district-hwBhsRRLFHQtcozMdantnXiWqsuhaFVBliyIToGJQZwezVcBbD, district-JXNNRPJbMQSrblrSWtvwaljKQzejVObfVHnyADvkxtUuXKMfdj",0,0,0,0,2,2008-01-01T00:00:00.123456Z,2,2008-01-01T00:00:00.123456Z,regional-project-KzeoyDQfwDDPIDgflUgzXBmzveuvMFnSVEhrDcIjEjOnuKcMXy,4,,,,,,4,,False,wE,Dks,country-SSCNwtvmTWQZIfWWDKifZSDgDtRPTXDEoojNqxzlSQvYuDFbeE,1,Country,4,society-name-XwMKiGgzTYguJPeYtIDzLApNpJkEyevnSLBYBKYvISplQQeVTK,"1, 2","sect-tag-ZlhQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRg, sect-tag-jREefffBgVVxZiJdLJJvQhAwQWBUdsMtwgKGnjQEogwJxhWrKo",2008-01-01,1,Ongoing,0,0,0,0,3,public,Public\r
0,4000000,,,9,9,disaster-type-vNejLODOvYQgNhdTimVflfTfaBYRondTfyuOHmEmTFMTlEsURL,dClGaflmqjIKmShSWemluWokzOLsMAGOsnBqwVpHaPRqsWkedeFwUdNWBfRWTCaVRfuLXxSRMReKqUuCwVZExFtWFuIVmoLkcSwADDuYzDDCjjVWyAbiYuyOjzxaBYQljLlngbzEjrvmbFzktJromFMUFBBkFQdwgeuTEMsjpHFZnAFatOkvOtRNBNhMiHsvUxZSixKEebCxApnuSouOEYrJvKYvSmiuYOKoTLNppFKEbuGgyWjNufHFDMUreCyXmYXrTjxXdEpoOauwNEJjYruFuMImZPmMMhsUdVmHZGspYyBSatqnjsbbPPWAfxDXjCOyJkMCWugrDrmTMDskLiubhduJExjuUyJbOBPuzluNWcPsuKWKcGdUTTiFeeijgHkTpfWxwvfAvWeFzIdHAPYzSjJfnCkhWqopdPRJbdPSoEccoWojiGuuyWOQzbGWsFbQTSAJecmLcnoLFawSfLxGkznjIaOVNsrJxGykmWMqvmuqzhPs,2008-01-01,6,7,,6,event-RJXxaEkwgEJRzSnEQyDTpWgyiuWizXusRUBMzIewFQVLboMlXp,5,xxvganmwzepoifmcntbfvyplbjstyrecqalkzrhgdzfwrugpzz,3,2008-01-01T00:00:00.123456Z,,,project-CbCMPQGXznlhcyZgVnmWKVVtSRnLtxDdPOoKqnGbtanlvnFUyU,1,Emergency Operation,1,sect-gRoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcS,1,Multilateral,7,,,7,,False,Hr,uSI,country-VWZYIKcZaUpdediClscuwMPpsiMzEQhQeeqInFTVwoCTtxXJsP,2,Cluster,7,society-name-GgdwATNFrfniHotVJnhxUYjcpSCPWDhbFcrrLytfdrNyFbyyCc,"euKBKzTOAs, kWNdRfrCQB","2, 1","False, False","True, False","district-hwBhsRRLFHQtcozMdantnXiWqsuhaFVBliyIToGJQZwezVcBbD, district-JXNNRPJbMQSrblrSWtvwaljKQzejVObfVHnyADvkxtUuXKMfdj",0,0,0,0,3,2008-01-01T00:00:00.123456Z,3,2008-01-01T00:00:00.123456Z,regional-project-aratCyUKkgdxnPmBVxerAPbtXchtjqDZnhOVRYbElahfUpDLSJ,6,,,,,,6,,False,me,UQL,country-ndnbWRBrqOlfjerzftTCAHnQqldfBvWtkmwAEEISYkSBwSKyaJ,5,Representative Office,6,society-name-NjuQUVVUuajDjFuhYRAqHUaCiOCOLgcnVmASIXkMynwnmRKaxx,"1, 2","sect-tag-ZlhQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRg, sect-tag-jREefffBgVVxZiJdLJJvQhAwQWBUdsMtwgKGnjQEogwJxhWrKo",2008-01-01,1,Ongoing,0,0,0,0,4,public,Public\r
0,4900000,,,12,12,disaster-type-mBAJmsJjyIUKKNzkyMDYaHoIBJJHOKhEHRQPFYNexbxZLBlxDe,KDybSMpibfiBSWwDOHKJlyatfJaWKxieYDxvGuhDFDsTfQViFsyMlYegIRZPJjrfMTLziBrlkjMEvGLeCdZTqUUxrigJwRsxFcuBXGiaKjixFaTKbUdeOzoTvArdDknirElGkJNuUYradfFHPHlkSqTCpfiAeyIYXxaEedYwJPSWdfhKxaNlDZgQfulBfVcVxoYCdKimccDeZBLuRaaEqSPfGKYtJTuSsoZPjZKHDALJKnAwiMqrEXhAUfNYUGjEmZtZIfnXUXecqvcjwXJQNzoRleDsnYYUxCqHWpvjAHdzrIBcVBCmLJoTqtIGmJtluZoyZOtziIdvvdCCrTdzxCNvwfxzknKlUaMcIvXugcFOStUbQMgogfgDXGygMRbjvZsTCRydRSlkObzTNxourSfRlafQilCuYYKwdakAWZSdfuhvnUlwZPRRLqCONvcCscFgWCTmiDMJdwTVLRxPboQWedazsRNntXUanSLharwicnBcGNSW,2008-01-01,8,10,,8,event-PMWMVURRWDfHsjIYxLyOKpjvKgsbXGtKNYmlmglXZosXjXBzKJ,7,dansbjejzohdwabpclvntjuohmouqqmxpphiqjwbsawaqhjskn,4,2008-01-01T00:00:00.123456Z,,,project-seeItONgoPvNNlIwwWWpxRKvjcxyecdAFKKaPbzKBJdeIyTCEq,0,Programme,1,sect-gRoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcS,0,Bilateral,9,,,9,,False,II,AbG,country-cDULJsIWDcsvbALOYeEADMKouLoCqtPcoQLqzqaHocoCpzaBde,3,Region,9,society-name-UYXOYtXMQdFLnIQJsXhpyJUvlIPmaRBfvPpEbgiVUqkQsQqAkB,"euKBKzTOAs, kWNdRfrCQB","2, 1","False, False","True, False","district-hwBhsRRLFHQtcozMdantnXiWqsuhaFVBliyIToGJQZwezVcBbD, district-JXNNRPJbMQSrblrSWtvwaljKQzejVObfVHnyADvkxtUuXKMfdj",0,0,0,0,4,2008-01-01T00:00:00.123456Z,4,2008-01-01T00:00:00.123456Z,regional-project-azFDyWkvuankOwaeFnyuqizlsgDIqlLdOlQKSXjoYotvgeaVYc,8,,,,,,8,,False,sx,fMx,country-eUSjnezRybcFBDAlaKcQeXrTsUEmZrbQrmpSCZaPcKBJSFYoTV,1,Country,8,society-name-DEIkxQxUJIjuVOwAlLzxDwXsjRWFRIAxBfMqivwPDCWIRkcvGO,"1, 2","sect-tag-ZlhQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRg, sect-tag-jREefffBgVVxZiJdLJJvQhAwQWBUdsMtwgKGnjQEogwJxhWrKo",2008-01-01,1,Ongoing,0,0,0,0,5,public,Public\r
0,8860000,,,15,15,disaster-type-utROMSbhswXKNACbyMleNvICmaxqMHkroJGVXrQYpZdSjYSRVe,DUIhAEGayOyPrQoRhvPHLWWdgyPqXLUQjPGfvamCXchEdMjAOtcCdnbGOIcHOeDkzjHkMAJlPXstHuWbQbDjHGQLvKlPPDOrfeAIaBLRhUMyhkZEzziaJcHibpNhDdOWZlAmRqrrnuZMyOPlPqvHRFaflaVVsZQQjtkQxnAMbLfjoDxpalJrKCzTdpNyPWCaiWspyuiWStcwwoSWBqGWfSICYxXrRbpzSrGIjhwTKCFpHxrTzAjmioBcyzZDMXNHAsLeixLtKFQliVdqlMHylkAKNiayAzeDKLAlmwyNLMQjLVMYUJpnuWJVEzJGDTFCNlxXBathpqHldHZqMpgumMHVmWMfjizabaestdPQSDzjNUVeYtVPQocsUKenthbnHZKFujOIEicLNIBPuQytkVYQSisavNTPjdHlovobKFBBMZgNqJNziKXIcPxzIiafEQxpOaCNAAgHBKvEjWWPUPXsatpYtFqhTkuoeQmEQNuzgadFFFmP,2008-01-01,10,13,,10,event-WBfxOsCQpfPvyypLFKlwwYhgyspzRNcQiGpEFlDbkIMAXPyAav,9,pslhfyzqqetraecgnsduonviotaqcxhcmqjiaifnaqjfanbigg,5,2008-01-01T00:00:00.123456Z,,,project-keFwdoAfWKWQlcjSvNVLMUeLmHEmnDcmtUlZstrCsJMaXrFBbC,1,Emergency Operation,1,sect-gRoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcS,2,Domestic,11,,,11,,False,fD,Tkk,country-xaCBjXENNwWupVdlrPxndfloVLJXqFkpbnrTYiciIsDeZLZVZX,1,Country,11,society-name-QZisdxdCUAqQIDUXgEPOSFuqAgNYMlqdyxOIoICjYREOjvGelj,"euKBKzTOAs, kWNdRfrCQB","2, 1","False, False","True, False","district-hwBhsRRLFHQtcozMdantnXiWqsuhaFVBliyIToGJQZwezVcBbD, district-JXNNRPJbMQSrblrSWtvwaljKQzejVObfVHnyADvkxtUuXKMfdj",0,0,0,0,5,2008-01-01T00:00:00.123456Z,5,2008-01-01T00:00:00.123456Z,regional-project-YEOcSJXwfESpQkILwfrwymqcMeJYwGawwIVfUVZguCqrTZNzQx,10,,,,,,10,,False,AQ,ZlZ,country-cwpaOWIJAGqpajhfyzCoYiNasRvDvWKJYICuKlfkLVLXBtkzco,2,Cluster,10,society-name-aSjDxwHleqDDbSMiaChfZwkoTWJalmBSkgPYMUQkewHYhHKFUa,"1, 2","sect-tag-ZlhQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRg, sect-tag-jREefffBgVVxZiJdLJJvQhAwQWBUdsMtwgKGnjQEogwJxhWrKo",2008-01-01,1,Ongoing,0,0,0,0,6,public,Public\r
0,9640000,,,18,18,disaster-type-kSrpZWxaSMtCAwSfhQVGBQevAraNZKsgtFwmNINTemDcutOitu,fRONdGlyeQXebPmuyuNrlVKLlcOlpEyTyBLQBMlXkKwooIyfKqfeOIYWmMRbNYoYYtirPOjsayBRlGVmrAmmZtRHIMopqnExgVHyBNqUcGBXZxZslspUJlyNiJvvbCrnvbKwkWJOHZNxMrEOapKBZMBsunuMgEzvcqDhZJHmacWLZLvriJGDnrsVUNPzQyHBBCLINLqDbASgDSPbBLdfqNCffbWnZHqYTCgvzEwABUuaPveIUGBbRgyFQsqKURlnsSnxNOBKHubruWbPvYAATKYoFvtciTVqlYJBeESILkvZChtcivdRpIuTFBVlWytGYeOAWWpHPsKpWVAJdQymuGwobUfbXfWjCJKyMvfZNPnaWsPGxjTFDwHyWEdnyuAjdmVBnqtRsnOMqzGXMyVVTpogIeRjmoxCRAfETVdCohCtrwDDBlRAiypzCIuScGNJMFFqYFXxNrRsPpsGTviLwmCVDYqbWYpEyDAJEsbqjbEADwftMCwm,2008-01-01,12,16,,12,event-pVjqlntGaXcrfDTithUvvpzMguIvuDsLbylFKZyakrkxCdpWno,11,qjnyvrmswlofuoizihyocrbimbzlsnmfckgfskmiibtfadixlh,6,2008-01-01T00:00:00.123456Z,,,project-tfeuWEXnPXndNLdYcPTcKrVcYAxzwUGjpVsUqvpHZvPQBxpvlm,0,Programme,1,sect-gRoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcS,2,Domestic,13,,,13,,False,Nu,EnW,country-ChuOWzXIMeVcLOCCNCIdjoOtZXOrwBGsqAEKZsbWoXBUBtbeBn,2,Cluster,13,society-name-FGQnhwLFxCTkMTQjQCogGzJXVnTciKfvJxTQtPkooltfyVxeJw,"euKBKzTOAs, kWNdRfrCQB","2, 1","False, False","True, False","district-hwBhsRRLFHQtcozMdantnXiWqsuhaFVBliyIToGJQZwezVcBbD, district-JXNNRPJbMQSrblrSWtvwaljKQzejVObfVHnyADvkxtUuXKMfdj",0,0,0,0,6,2008-01-01T00:00:00.123456Z,6,2008-01-01T00:00:00.123456Z,regional-project-dVptLWQxAefMSWMGKLVzuffJgRuGnVCYrzBetUtECBfGPWPAGF,12,,,,,,12,,False,OS,VbQ,country-dPFEadsaLpZaTtuthIrbWpMYTIjlfZIbRnLyzXkXVUcpGxIJzR,3,Region,12,society-name-CIIajzukMSvfysSBTMnnUpvUAimdmMDtqbGGdWXBFcGUMJEcMk,"1, 2","sect-tag-ZlhQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRg, sect-tag-jREefffBgVVxZiJdLJJvQhAwQWBUdsMtwgKGnjQEogwJxhWrKo",2008-01-01,1,Ongoing,0,0,0,0,7,public,Public\r
0,5070000,,,21,21,disaster-type-DoHzYvyMatrGQqVQBFVonlTlNeSksIMvwIDSCbaQBkpRNquLLR,rkArcFAbOJMundfiTdopKGbShpUGFfWyjIopwBJNduJXecIRbhxnnDrZmuzDbiOPCFkGXDeuyxMBQNxDSLQswFvKvNKxxbvuPpSOyiKTOfChtGxseJoNwkSuiVQxjZdDQXHPGkXWezPugeNOTlftxFsTsujdZncYZQiEOyWNqDmbGUXJjtdmUxRplUfYkVssaVSlLmXBosPYYbKqflZTfJcxTQkwEKuLKdTbsEMqfiZPpjutAafJMfYhnZtVUoqZGTxEemnMXRNBSlDBIAflFpsihXhjbXkNfSTnGfocfsLtJckNHMdJIPHTeLyRAtZxkmhKgRKLcGjeQnmuzJUSngCjoWBOzFdtTSeEfaPnSJKfNhGYWEscubhpUnYkbWprZqLxBbFeqHEXzwdTFDwWTjwTPDjoeyWVnhzbmQFPGUefPQVXduXSWCbmWKNyXndBzDbawMMrzMzzRMpTiXpnSDdbFgVRuHaYbLFerPdJAmplntnbZWzv,2008-01-01,14,19,,14,event-DpHGEitygznamZYXspHoXQdbbLfsoukNtNobFSTrgCKKPAurAW,13,yjgnfsmwghmzykjvjcxuozdakipcioscxyvdcglxfqxhkvcqgh,7,2008-01-01T00:00:00.123456Z,,,project-IXFssSISHJmNPkpDvMUaKFljHuISjRxJvVrwuhnNXhKAYbntHk,1,Emergency Operation,1,sect-gRoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcS,0,Bilateral,15,,,15,,False,CR,dhJ,country-coQkytPvYzqNBDtgLNfzcuTRWoMRbyYqYZKcKUTWFPaotivQhT,5,Representative Office,15,society-name-eVxJKgmzIjLzDaDrlhvpeMpOzUiXvkzYailhBKVWbJTGDxYrGa,"euKBKzTOAs, kWNdRfrCQB","2, 1","False, False","True, False","district-hwBhsRRLFHQtcozMdantnXiWqsuhaFVBliyIToGJQZwezVcBbD, district-JXNNRPJbMQSrblrSWtvwaljKQzejVObfVHnyADvkxtUuXKMfdj",0,0,0,0,7,2008-01-01T00:00:00.123456Z,7,2008-01-01T00:00:00.123456Z,regional-project-qSpAqCxHtAAZrHBVETrgzoFXficzogDvwkKCEzchqwGtaGghVX,14,,,,,,14,,False,Bl,jeq,country-LAzQPYyJjTNbVxTixzvMLxbHPNerTkSoSoaUlKTlFBsburERpN,5,Representative Office,14,society-name-dwenfIyyctFtCpnJLfqDUVGvkqDttiamuMqsgbVRkUoYGEPowf,"1, 2","sect-tag-ZlhQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRg, sect-tag-jREefffBgVVxZiJdLJJvQhAwQWBUdsMtwgKGnjQEogwJxhWrKo",2008-01-01,1,Ongoing,0,0,0,0,8,public,Public\r
0,2780000,,,24,24,disaster-type-dPoVRSXLtpROMGHqrjDJKwjRpBfYFLqKAUqvZtMSVwTNwDUGhl,CUmUgFTsRUQZjCUgHoijRrbknMnzQiEygDArTbXQrcrUyvQxgfkJyoGfhbwaiTZiITMkcEXPsROvLwkYHTiCXAFEYrlnNnuSqnWoODmUYiTCHnMAXVLlfwhcaiyaFCWkeqmOOqSHyKQYyYvnFexwEphbwlaJKJmeJDobQZKxdENnoDCogiNEmrfVtHvdXkRSDQxMOSbHjAITbaMdEjlbJPOEfkWhHLWrwlpMPSuKAXcipneuZNXNHUDwhDxCYNbmkmaJHIdYBaMseDvakYUrhobdCGOIBFPwHSYFuvRIvaLvKWgtvcsNClpzANsRziClGBvgIhsXSictYoPJrWQucRSqzjgFyqQmsMmKsgBYTWyCqcCJRJRSAKGVSxIuCrNeWfdzPZBDPjBsfGCNpPLCINunDEdekrKnhBVrwRQMHjqpCIarCascEOLmyweZGCxzYLlBSLiWdXXoQUkEnvXFhjxyElejpabJXvDQGKwYLhxojTtlvXyy,2008-01-01,16,22,,16,event-XvtCXCOFFrxKlxsThinGCjsVLZZpEMENcbFdTsvxMsJtKSVADq,15,ugbbimrkvyaqfhjvxlovbkxcbcqnuybythyjxjfjrezxmzesxh,8,2008-01-01T00:00:00.123456Z,,,project-baLIYUavFZInAPMcSnbmrepOzvPmiLGuBUIrNRMCUZCbVFZcBc,1,Emergency Operation,1,sect-gRoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcS,0,Bilateral,17,,,17,,False,Es,RTy,country-wKPcFqjMrftjQNQbsNwDPCBlumRWOIsDzWyMfMZwmcgzsFiHOz,1,Country,17,society-name-HuLaiYRyiMZCyfhWyyiXUIzBaXmtMHirZzJMOYRAEPchzxykFV,"euKBKzTOAs, kWNdRfrCQB","2, 1","False, False","True, False","district-hwBhsRRLFHQtcozMdantnXiWqsuhaFVBliyIToGJQZwezVcBbD, district-JXNNRPJbMQSrblrSWtvwaljKQzejVObfVHnyADvkxtUuXKMfdj",0,0,0,0,8,2008-01-01T00:00:00.123456Z,8,2008-01-01T00:00:00.123456Z,regional-project-UQFtsmyJCfQUOypGSDBlfwETFZtaVuqxGBBhHjsWIUFterkFGx,16,,,,,,16,,False,FC,frZ,country-lIhTtTnSyeeAIyhgtybmyefHMkzVVbYvvvTOrywqlVzGpyGWqX,2,Cluster,16,society-name-bmsZRrORurvKwRAYBbaoaffMAPijFXjoHyZLErRiSgPUXCVZny,"1, 2","sect-tag-ZlhQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRg, sect-tag-jREefffBgVVxZiJdLJJvQhAwQWBUdsMtwgKGnjQEogwJxhWrKo",2008-01-01,1,Ongoing,0,0,0,0,9,public,Public\r
0,7070000,,,27,27,disaster-type-LVIzCDESdvxtHLLTXcEflSLMyMWMgusTJlEadQiKpnXSgnizGK,mEqAbkepBWIIsexFEfSiVMeHrlSOPxeULwYAWfEBQxvJMkjoSxxiSIuJFQbBmaYQjXjJXTlMoZpwjICHNFgxUmwZMPAtFkAHQtVFrArRxucDRjHpgWahJwURdHIdIEuzVtwWbVRvIhPauHagaJPJRAFMFZqqFBfLnCIZXUJBymyYOsyWvpootCCrVKAomEKjjYSBkGhNewalnFsnJOFpsudukhMsauOaqEiWAbNEPKBkMerwLFCpAybKIWVuLhMJfCWtFUoyBxnNCPHHwHCZtGVMRRwPxChphZONIqqqYUMyeBpKulvEqEEErpCOkfjoGrGDCxyeYNfJWKHEvxFLQIoiUlMcOXbduLauswVhCoyuJxscuUKeKortlsAiQVEgimNopdXWAvpmxYmTxNEuLQIbKzZkGlUThMzaHFJFWOuOEGPJjXSYEmDBpdLEDoLPGUpByAbKFQKFGZuvaYWdRPsrxQcCTiMzkNUXVbRfbCNoTlSjzwjC,2008-01-01,18,25,,18,event-LXsfjODbAygJXuQoAcTHFIcCiaQiboOTnJJgekaWKNBzEBoCkb,17,mpcosxqgoyxaeadoglosawzqufzsmlafecuqzcmmpezqumalvv,9,2008-01-01T00:00:00.123456Z,,,project-HkwsypbvNtQfVwBFheDCunLJXUYCkrZOuJfTLYJDQcGQGtaFvT,0,Programme,1,sect-gRoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcS,1,Multilateral,19,,,19,,False,Is,riR,country-LPSlIrHKJEYpxTGFlDkNMmnOUvSERObkSqbNpKGzQBmTMZHtXy,3,Region,19,society-name-DpLJouUWzYRwiTpMeJUJAQDzkYjEpvoptayOkdgABmprXdhqSi,"euKBKzTOAs, kWNdRfrCQB","2, 1","False, False","True, False","district-hwBhsRRLFHQtcozMdantnXiWqsuhaFVBliyIToGJQZwezVcBbD, district-JXNNRPJbMQSrblrSWtvwaljKQzejVObfVHnyADvkxtUuXKMfdj",0,0,0,0,9,2008-01-01T00:00:00.123456Z,9,2008-01-01T00:00:00.123456Z,regional-project-cXDVSbwfZmcAMACleXiIguyJpJCYblEHvoCKJXjhsUKktfoEgE,18,,,,,,18,,False,ex,Qrh,country-UUMGGElAnTqRKlfOkinToKLZHkhuKYbaDShniQSasTrGqXwADY,4,Country Office,18,society-name-UDPSyyasuAJLoKfgzRVtxCPzFYQCWzxEUByzqEzcJwiaGQVvPi,"1, 2","sect-tag-ZlhQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRg, sect-tag-jREefffBgVVxZiJdLJJvQhAwQWBUdsMtwgKGnjQEogwJxhWrKo",2008-01-01,1,Ongoing,0,0,0,0,10,public,Public\r
0,4520000,,,30,30,disaster-type-ectKryhFpcxQeZUvgnoQibLzCmdLYjsaEtfOmvKORAAvppKdoY,yoQHxErmoMgLuGbSabYJtgzjRyFxcfTtBHpPhrzxaYboKqXOxxGTRUTsyVsPkdgGgWPMbinkagywgMHJMazVbMhFXwcDvhVLkyDEOwZbrzgzPkQjROGOsmUMRBwBIVOJWOFYkajaqJFfboyYRvosFyWsfqsYjUTVEhRLCsvnesxLxwaJddjONbBULwtEmuBqiZCSiLqnAOfcYNbKHkqudPHhqTBQtCcjmAaCshFdYBaklxkvumQQfmqVfCAllIbKwteFxrRcgypCNcwXJrJkJhCmNnnWNVzNOgbWWIkZLBPQwBgiZdYysyrUAEyqDJwykvdJqwdVRePtpYKLKjwDaLLkGBhajHwOvWgqpHRjuRvjaplRUIWAvKhIWhKYHcXwlHnZMXcvmaBFoaUQIoZdoJHsbgVBOEDYzLjSSeLPhVbvaFgLDcMwFsWtwTrbBLhtpGDZBEnJPtphXSOuVZxAFBMuMDNkKylVAokTEnkqoFWcmRONfKQc,2008-01-01,20,28,,20,event-vhoCQGQAXlAGqNCcsjqeAUKQGhsjaCyQIfCPacBIeqoBxKEjQo,19,mvpydzavgrduqhdyfucbyfbafsdwwhtviaacejqlgsxxdbghob,10,2008-01-01T00:00:00.123456Z,,,project-uAzWuRZgqeRotmbCzHPojKXGCyZSJfPOVBcwZUOfLgEYakRrlp,0,Programme,1,sect-gRoEbNJuNoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcS,1,Multilateral,21,,,21,,False,TN,sjv,country-hBlSDShqfmrYlFPTFmjmuPFoSFqlYgRtUjaMqlcCMpEqhxPGDe,5,Representative Office,21,society-name-dQvKiQYvoPZaXKxwSVRJFFMZTMozsQYlFnDLwDjoHUOgBRYeiL,"euKBKzTOAs, kWNdRfrCQB","2, 1","False, False","True, False","district-hwBhsRRLFHQtcozMdantnXiWqsuhaFVBliyIToGJQZwezVcBbD, district-JXNNRPJbMQSrblrSWtvwaljKQzejVObfVHnyADvkxtUuXKMfdj",0,0,0,0,10,2008-01-01T00:00:00.123456Z,10,2008-01-01T00:00:00.123456Z,regional-project-msemwREThZBVJjAhegVsDykbCnqDIEYWoUwthruwYAtCmePgXz,20,,,,,,20,,False,EQ,iwa,country-cHxHncAJqRGnBXWHhBCkmIzBvQAczEExwKwCYpVWYusgZauVWO,4,Country Office,20,society-name-sclvSZVIPNVGJebOIuZuHCjnvFGsWxYEOjcHbjshbYsfxdYDVW,"1, 2","sect-tag-ZlhQbiawYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRg, sect-tag-jREefffBgVVxZiJdLJJvQhAwQWBUdsMtwgKGnjQEogwJxhWrKo",2008-01-01,1,Ongoing,0,0,0,0,11,public,Public\r
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
            'budget_amount': 4870000,
            'description': '',
            'document': None,
            'dtype': 3,
            'dtype_detail': {
                'id': 3,
                'name': 'disaster-type-sRqjdSYsnWIcwCgNRVJoVPJypGYYZSsSQdyyAYRuJdaVqmNXCo',
                'summary': 'OTTPxWLIVMmXUmsClRellVGhycBrJqikLqavDTjcjuMdXONQtFYKJweYTuHolHeYGkAIIzfwonQvvxsnWNHEJWPahQwCpPNNpcRuyYhyqIUsbHXxGZGCFcsPmuGfgkXIIaOenQOXnRBgnISVXBPeVRjbDTvcfedlYqJeKoqAyCOzBubyRhIaPUNeWVLcSewGgsYRtMfsWCyzQbEkIoiVzYZIsOjtRYUPxaJJjhcaKMzIJftnVVUwnAPGjkloNqmhlQZKdWJDPJesQeqgmULFvwiQPpgsNemuFCvNQtSLjKKxZuBkaupYoTVPBrxiRUvEDCwXtFJglPMfriImqUOeUebGObLLzXLncJqIIEPXjxzoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYxyEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjlkxMThQoAZvUhEREEnLkPAbpciKLkiOGcKjdkql'
            },
            'end_date': '2008-01-01',
            'event': 2,
            'event_detail': {
                'countries_for_preview': [
                ],
                'dtype': 1,
                'emergency_response_contact_email': None,
                'id': 2,
                'name': 'event-hRnTLFfGCZdDiGADKdJDRZtUbzqaVnLecBwSeIdeEcsAlXiXPU',
                'parent_event': 1,
                'slug': 'paxycyyfrqiipwhlizhiuoawbtdruibiyopdwjrmuwhczqanxb'
            },
            'id': 1,
            'modified_at': '2008-01-01T00:00:00.123456Z',
            'modified_by': None,
            'modified_by_detail': None,
            'name': 'project-HzMKObUUQsfnCMEEkoAMjYLXlNQGqkURvDMLeoyyigbmHGRAjM',
            'operation_type': 0,
            'operation_type_display': 'Programme',
            'primary_sector': 1,
            'primary_sector_display': 'sect-ygwwMqZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkI',
            'programme_type': 0,
            'programme_type_display': 'Bilateral',
            'project_country': 2,
            'project_country_detail': {
                'average_household_size': None,
                'fdrs': None,
                'id': 2,
                'independent': None,
                'is_deprecated': False,
                'iso': 'hQ',
                'iso3': 'bia',
                'name': 'country-CCpxgRxIPwdzrmhDfQnPOMbdYvpiYKneWJnLnovXjYMarjiIqZ',
                'record_type': 2,
                'record_type_display': 'Cluster',
                'region': 2,
                'society_name': 'society-name-wYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRgFTCefuM'
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
                'name': 'regional-project-cSHBoZEYXywLZVWSKgBiqEXofsMIAqmaTVYaKHhHayPnSZuAxg'
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
                'iso': 'Ok',
                'iso3': 'YRB',
                'name': 'country-yrOSJoRuXXdocZuzrenKTunPFzPDjqipVJIqVLBLzxoiGFfWdh',
                'record_type': 2,
                'record_type_display': 'Cluster',
                'region': 1,
                'society_name': 'society-name-MeyyMDHqJaRUhRIWrXPvhsBkDaUUqGWlGgOtOGMmjxWkIXHaMu'
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
            'annual_split_detail': [
            ],
            'budget_amount': 4870000,
            'description': '',
            'document': None,
            'dtype': 3,
            'dtype_detail': {
                'id': 3,
                'name': 'disaster-type-sRqjdSYsnWIcwCgNRVJoVPJypGYYZSsSQdyyAYRuJdaVqmNXCo',
                'summary': 'OTTPxWLIVMmXUmsClRellVGhycBrJqikLqavDTjcjuMdXONQtFYKJweYTuHolHeYGkAIIzfwonQvvxsnWNHEJWPahQwCpPNNpcRuyYhyqIUsbHXxGZGCFcsPmuGfgkXIIaOenQOXnRBgnISVXBPeVRjbDTvcfedlYqJeKoqAyCOzBubyRhIaPUNeWVLcSewGgsYRtMfsWCyzQbEkIoiVzYZIsOjtRYUPxaJJjhcaKMzIJftnVVUwnAPGjkloNqmhlQZKdWJDPJesQeqgmULFvwiQPpgsNemuFCvNQtSLjKKxZuBkaupYoTVPBrxiRUvEDCwXtFJglPMfriImqUOeUebGObLLzXLncJqIIEPXjxzoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYxyEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjlkxMThQoAZvUhEREEnLkPAbpciKLkiOGcKjdkql'
            },
            'end_date': '2008-01-01',
            'event': 2,
            'event_detail': {
                'countries_for_preview': [
                ],
                'dtype': 1,
                'emergency_response_contact_email': None,
                'id': 2,
                'name': 'event-hRnTLFfGCZdDiGADKdJDRZtUbzqaVnLecBwSeIdeEcsAlXiXPU',
                'parent_event': 1,
                'slug': 'paxycyyfrqiipwhlizhiuoawbtdruibiyopdwjrmuwhczqanxb'
            },
            'id': 1,
            'modified_at': '2008-01-01T00:00:00.123456Z',
            'modified_by': None,
            'modified_by_detail': None,
            'name': 'project-HzMKObUUQsfnCMEEkoAMjYLXlNQGqkURvDMLeoyyigbmHGRAjM',
            'operation_type': 0,
            'operation_type_display': 'Programme',
            'primary_sector': 1,
            'primary_sector_display': 'sect-ygwwMqZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkI',
            'programme_type': 0,
            'programme_type_display': 'Bilateral',
            'project_country': 2,
            'project_country_detail': {
                'average_household_size': None,
                'fdrs': None,
                'id': 2,
                'independent': None,
                'is_deprecated': False,
                'iso': 'hQ',
                'iso3': 'bia',
                'name': 'country-CCpxgRxIPwdzrmhDfQnPOMbdYvpiYKneWJnLnovXjYMarjiIqZ',
                'record_type': 2,
                'record_type_display': 'Cluster',
                'region': 2,
                'society_name': 'society-name-wYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRgFTCefuM'
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
                'name': 'regional-project-cSHBoZEYXywLZVWSKgBiqEXofsMIAqmaTVYaKHhHayPnSZuAxg'
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
                'iso': 'Ok',
                'iso3': 'YRB',
                'name': 'country-yrOSJoRuXXdocZuzrenKTunPFzPDjqipVJIqVLBLzxoiGFfWdh',
                'record_type': 2,
                'record_type_display': 'Cluster',
                'region': 1,
                'society_name': 'society-name-MeyyMDHqJaRUhRIWrXPvhsBkDaUUqGWlGgOtOGMmjxWkIXHaMu'
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
            'annual_split_detail': [
            ],
            'budget_amount': 7890000,
            'description': '',
            'document': None,
            'dtype': 6,
            'dtype_detail': {
                'id': 6,
                'name': 'disaster-type-WPaEPGWjzooUVnEoHLYJWDUDvYfumBXSAnCCJbxiKitVaFZQwv',
                'summary': 'oABRWzWXSItuLbKYcijvKOZMMKzynzeIymEgvKCOtfkgRJlcSMFblmeysnosQHeDdxHakuAzkhiIAEVeynintBTQEkMKtLmGTRDrmajCezMZpHvKFDDKcVfsPDwSTYtzNZlAplNUBDyQlSKgzScpkrOIsQeSUUnFAWJhxeWgGXXuACkqnGcDbeOSRVDyvVzmzcaqhTiuQVDFDefJQpTCiErkkbMglshIVzkeQWaRrjCwlnTcRInCSdOZHPQTQgyStCdMadXyXmpxpmfbAbavmRQeogZQkUkcAGguuJOmNnIzBhongwulazPuaynDoeQrPNxcenAtXMFgTIYKkqgMuOSyRXSivlOWSuQEevbMLCyGOVoGLTaobNWhtpVBWpNfdixFsmjynPcpUMCVviruPYWcHYAPsWboUvvpnIdQpZRSUoMyHulCOaeFemdOjniflLJYnpGfBUDtkUmpBlMptsKCOmrYEfxzykECBGNVBWjYEbWyBfWt'
            },
            'end_date': '2008-01-01',
            'event': 4,
            'event_detail': {
                'countries_for_preview': [
                ],
                'dtype': 4,
                'emergency_response_contact_email': None,
                'id': 4,
                'name': 'event-qxlnJTcQuwjxCIkIthbzFXjDujaVIGvPTsEsWKQjZKUCvShUEc',
                'parent_event': 3,
                'slug': 'irjhtbznocwfudmpmlhoyxrmbficrqfgzmfummgdqxzjtbxyxa'
            },
            'id': 2,
            'modified_at': '2008-01-01T00:00:00.123456Z',
            'modified_by': None,
            'modified_by_detail': None,
            'name': 'project-MIjJUlqyDtDsyJMEeviTEmjmaaGUUxFzAzVxyFtPLeAchyKkmW',
            'operation_type': 1,
            'operation_type_display': 'Emergency Operation',
            'primary_sector': 1,
            'primary_sector_display': 'sect-ygwwMqZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkI',
            'programme_type': 1,
            'programme_type_display': 'Multilateral',
            'project_country': 4,
            'project_country_detail': {
                'average_household_size': None,
                'fdrs': None,
                'id': 4,
                'independent': None,
                'is_deprecated': False,
                'iso': 'AH',
                'iso3': 'nSn',
                'name': 'country-PwcjcQKMtvfdgAlkRsNQSSMKYJlDVLxcfXtuxyeWBJesEihSrv',
                'record_type': 5,
                'record_type_display': 'Representative Office',
                'region': 4,
                'society_name': 'society-name-NdgKUOHfEUSMYTsBMuqHKNwiNKFHUOFFZlNoTsmahbDOYhVnZN'
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
                'name': 'regional-project-cxOTRbSQPjqMDRjqpMLQkahXfPTyzTLfHmBkBqStGIQyLtUAWU'
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
                'iso': 'yO',
                'iso3': 'aZf',
                'name': 'country-IBKxNrRzWnAJYJElxJJEqtKwXTzViQhVoCYSkgnGzYvZJNSRTd',
                'record_type': 2,
                'record_type_display': 'Cluster',
                'region': 3,
                'society_name': 'society-name-jEMBfeqoxfMcUyzNPHsTMdXlOFCamQZHsmcYMGHSoNkRcxpPak'
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
    'annual_split_detail': [
    ],
    'budget_amount': 4870000,
    'description': '',
    'document': None,
    'dtype': 3,
    'dtype_detail': {
        'id': 3,
        'name': 'disaster-type-sRqjdSYsnWIcwCgNRVJoVPJypGYYZSsSQdyyAYRuJdaVqmNXCo',
        'summary': 'OTTPxWLIVMmXUmsClRellVGhycBrJqikLqavDTjcjuMdXONQtFYKJweYTuHolHeYGkAIIzfwonQvvxsnWNHEJWPahQwCpPNNpcRuyYhyqIUsbHXxGZGCFcsPmuGfgkXIIaOenQOXnRBgnISVXBPeVRjbDTvcfedlYqJeKoqAyCOzBubyRhIaPUNeWVLcSewGgsYRtMfsWCyzQbEkIoiVzYZIsOjtRYUPxaJJjhcaKMzIJftnVVUwnAPGjkloNqmhlQZKdWJDPJesQeqgmULFvwiQPpgsNemuFCvNQtSLjKKxZuBkaupYoTVPBrxiRUvEDCwXtFJglPMfriImqUOeUebGObLLzXLncJqIIEPXjxzoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYxyEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjlkxMThQoAZvUhEREEnLkPAbpciKLkiOGcKjdkql'
    },
    'end_date': '2008-01-01',
    'event': 2,
    'event_detail': {
        'countries_for_preview': [
        ],
        'dtype': 1,
        'emergency_response_contact_email': None,
        'id': 2,
        'name': 'event-hRnTLFfGCZdDiGADKdJDRZtUbzqaVnLecBwSeIdeEcsAlXiXPU',
        'parent_event': 1,
        'slug': 'paxycyyfrqiipwhlizhiuoawbtdruibiyopdwjrmuwhczqanxb'
    },
    'id': 1,
    'modified_at': '2008-01-01T00:00:00.123456Z',
    'modified_by': None,
    'modified_by_detail': None,
    'name': 'project-HzMKObUUQsfnCMEEkoAMjYLXlNQGqkURvDMLeoyyigbmHGRAjM',
    'operation_type': 0,
    'operation_type_display': 'Programme',
    'primary_sector': 1,
    'primary_sector_display': 'sect-ygwwMqZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkI',
    'programme_type': 0,
    'programme_type_display': 'Bilateral',
    'project_country': 2,
    'project_country_detail': {
        'average_household_size': None,
        'fdrs': None,
        'id': 2,
        'independent': None,
        'is_deprecated': False,
        'iso': 'hQ',
        'iso3': 'bia',
        'name': 'country-CCpxgRxIPwdzrmhDfQnPOMbdYvpiYKneWJnLnovXjYMarjiIqZ',
        'record_type': 2,
        'record_type_display': 'Cluster',
        'region': 2,
        'society_name': 'society-name-wYYpLublqdiVAHhVeECXxGLgCGoNcUYQHtDPbdEzBRgFTCefuM'
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
        'name': 'regional-project-cSHBoZEYXywLZVWSKgBiqEXofsMIAqmaTVYaKHhHayPnSZuAxg'
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
        'iso': 'Ok',
        'iso3': 'YRB',
        'name': 'country-yrOSJoRuXXdocZuzrenKTunPFzPDjqipVJIqVLBLzxoiGFfWdh',
        'record_type': 2,
        'record_type_display': 'Cluster',
        'region': 1,
        'society_name': 'society-name-MeyyMDHqJaRUhRIWrXPvhsBkDaUUqGWlGgOtOGMmjxWkIXHaMu'
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
    'annual_split_detail': [
    ],
    'budget_amount': 4870000,
    'description': '',
    'document': None,
    'dtype': 3,
    'dtype_detail': {
        'id': 3,
        'name': 'disaster-type-sRqjdSYsnWIcwCgNRVJoVPJypGYYZSsSQdyyAYRuJdaVqmNXCo',
        'summary': 'OTTPxWLIVMmXUmsClRellVGhycBrJqikLqavDTjcjuMdXONQtFYKJweYTuHolHeYGkAIIzfwonQvvxsnWNHEJWPahQwCpPNNpcRuyYhyqIUsbHXxGZGCFcsPmuGfgkXIIaOenQOXnRBgnISVXBPeVRjbDTvcfedlYqJeKoqAyCOzBubyRhIaPUNeWVLcSewGgsYRtMfsWCyzQbEkIoiVzYZIsOjtRYUPxaJJjhcaKMzIJftnVVUwnAPGjkloNqmhlQZKdWJDPJesQeqgmULFvwiQPpgsNemuFCvNQtSLjKKxZuBkaupYoTVPBrxiRUvEDCwXtFJglPMfriImqUOeUebGObLLzXLncJqIIEPXjxzoXLUsiDGGfzxGaQpZNRkWGiCklKKQjVUEwcoWFoeqxocQnHYxyEDccPugTHOrVqLIKlyPyxLPeHqyoHzwwFYEMaGiCkoeGPrnjlkxMThQoAZvUhEREEnLkPAbpciKLkiOGcKjdkql'
    },
    'end_date': '2008-01-01',
    'event': 2,
    'event_detail': {
        'countries_for_preview': [
        ],
        'dtype': 1,
        'emergency_response_contact_email': None,
        'id': 2,
        'name': 'event-hRnTLFfGCZdDiGADKdJDRZtUbzqaVnLecBwSeIdeEcsAlXiXPU',
        'parent_event': 1,
        'slug': 'paxycyyfrqiipwhlizhiuoawbtdruibiyopdwjrmuwhczqanxb'
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
    'operation_type': 0,
    'operation_type_display': 'Programme',
    'primary_sector': 1,
    'primary_sector_display': 'sect-ygwwMqZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkI',
    'programme_type': 0,
    'programme_type_display': 'Bilateral',
    'project_country': 3,
    'project_country_detail': {
        'average_household_size': None,
        'fdrs': None,
        'id': 3,
        'independent': None,
        'is_deprecated': False,
        'iso': 'ky',
        'iso3': 'OaZ',
        'name': 'country-qqIBKxNrRzWnAJYJElxJJEqtKwXTzViQhVoCYSkgnGzYvZJNSR',
        'record_type': 1,
        'record_type_display': 'Country',
        'region': 3,
        'society_name': 'society-name-fjEMBfeqoxfMcUyzNPHsTMdXlOFCamQZHsmcYMGHSoNkRcxpPa'
    },
    'project_districts': [
        1
    ],
    'project_districts_detail': [
        {
            'code': 'HAHnSnNdgK',
            'id': 1,
            'is_deprecated': False,
            'is_enclave': True,
            'name': 'district-PwcjcQKMtvfdgAlkRsNQSSMKYJlDVLxcfXtuxyeWBJesEihSrv'
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
        'name': 'regional-project-cSHBoZEYXywLZVWSKgBiqEXofsMIAqmaTVYaKHhHayPnSZuAxg'
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
        'iso': 'ky',
        'iso3': 'OaZ',
        'name': 'country-qqIBKxNrRzWnAJYJElxJJEqtKwXTzViQhVoCYSkgnGzYvZJNSR',
        'record_type': 1,
        'record_type_display': 'Country',
        'region': 3,
        'society_name': 'society-name-fjEMBfeqoxfMcUyzNPHsTMdXlOFCamQZHsmcYMGHSoNkRcxpPa'
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
