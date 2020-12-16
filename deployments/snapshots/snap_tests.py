# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestProjectAPI::test_project_list_zero 1'] = {
    'count': 0,
    'next': None,
    'previous': None,
    'results': [
    ]
}

snapshots['TestProjectAPI::test_project_list_one 1'] = {
    'count': 1,
    'next': None,
    'previous': None,
    'results': [
        {
            'actual_expenditure': 0,
            'budget_amount': 0,
            'dtype': 3,
            'dtype_detail': {
                'id': 3,
                'name': 'VLHCAklbiUpQqVSVfnkzggeEJdbXzHWfgqNjfPytopVsCOiiHkbcQwuEDIrJCiSIlLMDOVOKBHOOItwEIoZfCtxAqjtaaHWiwsEI',
                'summary': 'aSFWEtaXBZsMoYaJxmAJBzpkTVPyyoqfBOpHWZNZSRrsPVIZrAmelishODNCrSNFmubjdIblgsriTCUaofjaFnvAtYZFxDSYcvfWjdrXzeIElmqyahXTpyXCpVcmDVXgHQnEyRtukOUcVJHhqEOtmxdQnhpOBuakYrLhzYpacLYSESMjxXfpkFfRNvWOddwPjSIYgiFouJYPWwZCUmbSywUiqcFTCJsISFmKlIwuUDrMJkeHjCsqIxDaXOGyUlbNxXNpuUeQIymHRFXJjNsuAPuhgHQecilcmgFmgcKPyQFHNSLqdxoMTeanPFfDZOdxJVAxYTdNrHcUetenHggUoIymmHQpKOlJVJAVgXOKwRDSQBgkYlJzGvQkIMCwuJuxAWOBUuMpKInyXJVqxCCzaUcsMbHitatonubXSrJGJKKjgcDwjiqxLpoqZtfKzKnUeUuYElFSSKgMPtcUZKyfXdXvwBAhXoVPMaOXOydtHcuIKjuGSojd'
            },
            'end_date': '2008-01-01',
            'event': 2,
            'event_detail': {
                'dtype': 1,
                'id': 2,
                'name': 'WptcCqwfChXZpnZVLSwTNOBkNiYnnZdKwIrMIkuTssKrGRgiWYAdrPiSipjTupWRzFjKOrOAyCeOYXfzGVrSxDFuLaXUfUDOQSwe',
                'parent_event': 1,
                'slug': 'yiznbnfrusvjkikfyvrwdcgoydbhkcdabmsiptkrfpxqfxqpkd'
            },
            'id': 1,
            'modified_at': '2019-03-23T00:00:00.123456Z',
            'name': 'RUzCWMKGfoBsYzjivfEKVdJzqfzGBXSiWiEJmFzPKmJNVHpperXBuRKfhQABxwmuwMPbXtkwNZCNjCcomRxjWUfhVdpNjsavSZhtCEbvnVInnIHWqJENUjSSQbyLQHcqkdsmYSNrdDPaeyQrQQxgbsPyoyGTguFMIflmGDJTbcpHtvFzVkbwRwwOtpGrZdOqybJrojvzQifUyHRNORoApKjBtMvCIinPiLIRZmitSTHiBXjPKkueJIUhlujUbWuAAtCVOVrjXmgilbWNNrMKNoMooRbwfSXEiGMETPxlyFEikmocAWarAoVQmWnelCNFSuDpBzXcMVyUuzNVKMIHPTYcHgCDcpHIzVcJyHWOdmsCztXsDkBsNdSHjDPCfUGhlXLSIizAuCblDLTmDfquSPTYkTUhfhTCOxfHTyUYGNkyJycXkvKQjkjlXTdAttUXCsOlhimaNWqaDFFIZaMFpnLQEDACfMMapJrNOJndljdPwcjcQKMt',
            'operation_type': 0,
            'operation_type_display': 'Programme',
            'primary_sector': 1,
            'primary_sector_display': 'PGI',
            'programme_type': 1,
            'programme_type_display': 'Multilateral',
            'project_country': 2,
            'project_country_detail': {
                'fdrs': None,
                'id': 2,
                'independent': None,
                'is_deprecated': False,
                'iso': 'tJ',
                'iso3': 'yPY',
                'name': 'eECOtYrLdwGetDCcdxsePfNMGyDLJYVcCZKPmuMEGjdCgZvTfGPlcpTCCHHNkxxsyAXvRMdYOPvevgJRysqUQMjvfLQjwtPSQziM',
                'record_type': 1,
                'record_type_display': 'Country',
                'region': 2,
                'society_name': 'viQSVRHfPQBGxbxtlnvXFmoijesYgGXIVHcQvXNiMyjklSXNZkUCcAxRUpCNsWVYCoIptZYEmxRKCDXsXyGHAkmZMiqdPExJgTHhsfWkrCGjBfoCwbAdzGxpyfxobugTPvYjicsESiWTECNafbqnjJUMHBhXspthdpAOYNDehFMIbOGKpTjsBaNwpKAlQQfHxeHIGYGJbyEcOyxqVbwYewpUQOgXLVWvicwIvPlXRDSEOlZieTXDcsmcYmcutGzIEqcWPmswXdPvrhZxBzVCyvlFSFxZHrZfUBfBMlIsugfuQstCMTBkSCwCcUwNBrOYdeQOzxGZVRkbjMRYCciepXPxxyKcMjRCxxCWeKiHxzuPrphbVlFHyJhqXqTCnNsSFmhieClTCfZRuQwTeJIstkTTSOlYxGohmYipYFbxJKxDZJiNfetzTUEHAXAKeiuPeCDRHwiXJOLlXiBGdhHjtkkuTowHsfqmOJriOtNIfGPkLLjkQNUM'
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
                'name': 'uxyeWBJesEihSrvHAHnSnNdgKUOHfEUSMYTsBMuqHKNwiNKFHUOFFZlNoTsmahbDOYhVnZNAAcvwJZOnaOmSsqYettGJuXahRvvz'
            },
            'reporting_ns': 1,
            'reporting_ns_detail': {
                'fdrs': None,
                'id': 1,
                'independent': None,
                'is_deprecated': False,
                'iso': 'Dy',
                'iso3': 'rOS',
                'name': 'bVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgfygwwMqZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkIUp',
                'record_type': 2,
                'record_type_display': 'Cluster',
                'region': 1,
                'society_name': 'JoRuXXdocZuzrenKTunPFzPDjqipVJIqVLBLzxoiGFfWdhjOkYRBMeyyMDHqJaRUhRIWrXPvhsBkDaUUqGWlGgOtOGMmjxWkIXHaMuFbhxZtpdpKffUFeWIXiiQEJkqHMBnIWUSmTtzQPxCHChpoevbLJoLoaeTOdoecveGprQFnIiUKKEpYEZAmggQBwBADUdRPPgdzUvZgpmmICiBlrDpeCZJgdPIafWpkAFEnzdkyayqYYDsBSUYJQTFjmsndLVIdVuddLEGHkdGfleMeRpzhKpLMcNfAQLKHuqnQTupqziQPtDuWeaDNKgeInGqiwepxskCITtNZPHaQJtQgiqhgVJjrsMnTvnROqGFqdfOBrcavXiOqkVCJTBJaheSjIcxLJjBictxYcwnRpQgwXJANVjpkZZlAblVvYAZQVZprkYSgycEomDwtYoobQmzvreXrwPGzRIvbhqlLqcgMBwUYuBMGhyKmqcTBaHZIRUVVQmxBeQvN'
            },
            'secondary_sectors': [
            ],
            'secondary_sectors_display': [
            ],
            'start_date': '2008-01-01',
            'status': 0,
            'status_display': 'Planned',
            'target_female': 0,
            'target_male': 0,
            'target_other': 0,
            'target_total': 0,
            'user': 2,
            'visibility': 'public'
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
            'budget_amount': 0,
            'dtype': 3,
            'dtype_detail': {
                'id': 3,
                'name': 'VLHCAklbiUpQqVSVfnkzggeEJdbXzHWfgqNjfPytopVsCOiiHkbcQwuEDIrJCiSIlLMDOVOKBHOOItwEIoZfCtxAqjtaaHWiwsEI',
                'summary': 'aSFWEtaXBZsMoYaJxmAJBzpkTVPyyoqfBOpHWZNZSRrsPVIZrAmelishODNCrSNFmubjdIblgsriTCUaofjaFnvAtYZFxDSYcvfWjdrXzeIElmqyahXTpyXCpVcmDVXgHQnEyRtukOUcVJHhqEOtmxdQnhpOBuakYrLhzYpacLYSESMjxXfpkFfRNvWOddwPjSIYgiFouJYPWwZCUmbSywUiqcFTCJsISFmKlIwuUDrMJkeHjCsqIxDaXOGyUlbNxXNpuUeQIymHRFXJjNsuAPuhgHQecilcmgFmgcKPyQFHNSLqdxoMTeanPFfDZOdxJVAxYTdNrHcUetenHggUoIymmHQpKOlJVJAVgXOKwRDSQBgkYlJzGvQkIMCwuJuxAWOBUuMpKInyXJVqxCCzaUcsMbHitatonubXSrJGJKKjgcDwjiqxLpoqZtfKzKnUeUuYElFSSKgMPtcUZKyfXdXvwBAhXoVPMaOXOydtHcuIKjuGSojd'
            },
            'end_date': '2008-01-01',
            'event': 2,
            'event_detail': {
                'dtype': 1,
                'id': 2,
                'name': 'WptcCqwfChXZpnZVLSwTNOBkNiYnnZdKwIrMIkuTssKrGRgiWYAdrPiSipjTupWRzFjKOrOAyCeOYXfzGVrSxDFuLaXUfUDOQSwe',
                'parent_event': 1,
                'slug': 'yiznbnfrusvjkikfyvrwdcgoydbhkcdabmsiptkrfpxqfxqpkd'
            },
            'id': 1,
            'modified_at': '2019-03-23T00:00:00.123456Z',
            'name': 'RUzCWMKGfoBsYzjivfEKVdJzqfzGBXSiWiEJmFzPKmJNVHpperXBuRKfhQABxwmuwMPbXtkwNZCNjCcomRxjWUfhVdpNjsavSZhtCEbvnVInnIHWqJENUjSSQbyLQHcqkdsmYSNrdDPaeyQrQQxgbsPyoyGTguFMIflmGDJTbcpHtvFzVkbwRwwOtpGrZdOqybJrojvzQifUyHRNORoApKjBtMvCIinPiLIRZmitSTHiBXjPKkueJIUhlujUbWuAAtCVOVrjXmgilbWNNrMKNoMooRbwfSXEiGMETPxlyFEikmocAWarAoVQmWnelCNFSuDpBzXcMVyUuzNVKMIHPTYcHgCDcpHIzVcJyHWOdmsCztXsDkBsNdSHjDPCfUGhlXLSIizAuCblDLTmDfquSPTYkTUhfhTCOxfHTyUYGNkyJycXkvKQjkjlXTdAttUXCsOlhimaNWqaDFFIZaMFpnLQEDACfMMapJrNOJndljdPwcjcQKMt',
            'operation_type': 0,
            'operation_type_display': 'Programme',
            'primary_sector': 1,
            'primary_sector_display': 'PGI',
            'programme_type': 1,
            'programme_type_display': 'Multilateral',
            'project_country': 2,
            'project_country_detail': {
                'fdrs': None,
                'id': 2,
                'independent': None,
                'is_deprecated': False,
                'iso': 'tJ',
                'iso3': 'yPY',
                'name': 'eECOtYrLdwGetDCcdxsePfNMGyDLJYVcCZKPmuMEGjdCgZvTfGPlcpTCCHHNkxxsyAXvRMdYOPvevgJRysqUQMjvfLQjwtPSQziM',
                'record_type': 1,
                'record_type_display': 'Country',
                'region': 2,
                'society_name': 'viQSVRHfPQBGxbxtlnvXFmoijesYgGXIVHcQvXNiMyjklSXNZkUCcAxRUpCNsWVYCoIptZYEmxRKCDXsXyGHAkmZMiqdPExJgTHhsfWkrCGjBfoCwbAdzGxpyfxobugTPvYjicsESiWTECNafbqnjJUMHBhXspthdpAOYNDehFMIbOGKpTjsBaNwpKAlQQfHxeHIGYGJbyEcOyxqVbwYewpUQOgXLVWvicwIvPlXRDSEOlZieTXDcsmcYmcutGzIEqcWPmswXdPvrhZxBzVCyvlFSFxZHrZfUBfBMlIsugfuQstCMTBkSCwCcUwNBrOYdeQOzxGZVRkbjMRYCciepXPxxyKcMjRCxxCWeKiHxzuPrphbVlFHyJhqXqTCnNsSFmhieClTCfZRuQwTeJIstkTTSOlYxGohmYipYFbxJKxDZJiNfetzTUEHAXAKeiuPeCDRHwiXJOLlXiBGdhHjtkkuTowHsfqmOJriOtNIfGPkLLjkQNUM'
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
                'name': 'uxyeWBJesEihSrvHAHnSnNdgKUOHfEUSMYTsBMuqHKNwiNKFHUOFFZlNoTsmahbDOYhVnZNAAcvwJZOnaOmSsqYettGJuXahRvvz'
            },
            'reporting_ns': 1,
            'reporting_ns_detail': {
                'fdrs': None,
                'id': 1,
                'independent': None,
                'is_deprecated': False,
                'iso': 'Dy',
                'iso3': 'rOS',
                'name': 'bVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgfygwwMqZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkIUp',
                'record_type': 2,
                'record_type_display': 'Cluster',
                'region': 1,
                'society_name': 'JoRuXXdocZuzrenKTunPFzPDjqipVJIqVLBLzxoiGFfWdhjOkYRBMeyyMDHqJaRUhRIWrXPvhsBkDaUUqGWlGgOtOGMmjxWkIXHaMuFbhxZtpdpKffUFeWIXiiQEJkqHMBnIWUSmTtzQPxCHChpoevbLJoLoaeTOdoecveGprQFnIiUKKEpYEZAmggQBwBADUdRPPgdzUvZgpmmICiBlrDpeCZJgdPIafWpkAFEnzdkyayqYYDsBSUYJQTFjmsndLVIdVuddLEGHkdGfleMeRpzhKpLMcNfAQLKHuqnQTupqziQPtDuWeaDNKgeInGqiwepxskCITtNZPHaQJtQgiqhgVJjrsMnTvnROqGFqdfOBrcavXiOqkVCJTBJaheSjIcxLJjBictxYcwnRpQgwXJANVjpkZZlAblVvYAZQVZprkYSgycEomDwtYoobQmzvreXrwPGzRIvbhqlLqcgMBwUYuBMGhyKmqcTBaHZIRUVVQmxBeQvN'
            },
            'secondary_sectors': [
            ],
            'secondary_sectors_display': [
            ],
            'start_date': '2008-01-01',
            'status': 0,
            'status_display': 'Planned',
            'target_female': 0,
            'target_male': 0,
            'target_other': 0,
            'target_total': 0,
            'user': 2,
            'visibility': 'public'
        },
        {
            'actual_expenditure': 0,
            'budget_amount': 0,
            'dtype': 6,
            'dtype_detail': {
                'id': 6,
                'name': 'qhmMbIbHGWjnxhnbuiofUSirrEmfwTJPsDVZFBGzmqlmRTrzgLYXLtkYnUFBCBMVruNgMyBmKwxOeCkcGqLAsMPHwzbhlZuBYlwp',
                'summary': 'enQxxjXuhauSaTvnDKYuoJeysMnHngJrTMZQeKPARWBuummdZFFcrAhhCkMuLypKbsbPYKaDsizcIHcvPbeEgZAUtruWwzfJXuFNdztSDFPhxNgbodaiguSUBokfmUZxIaSdqYchdteqvSNYZyrSkiLDhiujWLAOCQhHHpKEQFruXUEofqXsTfwJpQPVnSeeFdnaQnDymFgvnLWHGuWtTDPjGgioxyCNGmXzmerBkRtKPgjDgVhpbDlrbEQHCwqhJfwBnjzGBGvdCrxgdPyUBmsmzlMrHMFHBgRdPphohdcKrpeIgroNSTzzzgoUSrFnkYnwOsTMsUaglGSNEVtSpkuReklvDjaQEBvblqekRWaMwELaFpEhcbKRsoHGkWjXggtZVvCFVwIqQFqxDawtTvHXQMEhrRHUObjAoQjwFbpKVSBxnVfmyOgrORICHlqRwvzLArtmcLHSvNhBYDKYYwshaFRjDRjHsNJQktFseZsaDcnsLhdF'
            },
            'end_date': '2008-01-01',
            'event': 4,
            'event_detail': {
                'dtype': 4,
                'id': 4,
                'name': 'WGxFHDluTxHSETFErLzOYLPcnomCpzntByKkxqJfiWfsCHwoLcDGNvBCDBAxZFuryblCoqPewfsGGIPfYroghexcImvmRvqtVXRr',
                'parent_event': 3,
                'slug': 'mtmiwtviqaxtswyzzlwpaepgwjzoouvneohlyjwdudvyfumbxs'
            },
            'id': 2,
            'modified_at': '2019-03-23T00:00:00.123456Z',
            'name': 'taBwQadqiwsYGQXJjfTrjUmBLfsocEwpZROyBzgqtMtlKBRuZLiRXmqiAJmttftKODIlyYBgiHCSuGRTwDwBDAADbJbXAfWiNtYpLGxiNIKsdWzizQaDZWHDdfdrPgvMgsKESvdhVLRGVTdSnHjJVFioROjtOtUaZFNSmheajMhHgpngEbGCzdhtzElpIqNRCQNhBjObljVQpkGVSImEEssQgLFxQrzySZgDABjbsDhKyaLtcPPQNCcwiDUDrakwGGnwTHyGelPjwPUKvDTYirYWQtzePEyEMQlKTGXQHqiSuLLwLNzecbUkogQgFREuWoXZUYpglUyWAedNqhcVeCWxMOblugSCyiOKJmmqFCRsomVkBHZYmfLbOQgncZiaxXAKIevlRUUPHFmnKEGwwNJiZeCBOyeKfiYHtghFodMIvbosqyTwekseIKpHNGtzNdIShLEqPbcvAqmvWdinJUvWQdpFeZKNSWZcweAMVNfJEirUcgcF',
            'operation_type': 1,
            'operation_type_display': 'Emergency Operation',
            'primary_sector': 3,
            'primary_sector_display': 'Migration',
            'programme_type': 2,
            'programme_type_display': 'Domestic',
            'project_country': 4,
            'project_country_detail': {
                'fdrs': None,
                'id': 4,
                'independent': None,
                'is_deprecated': False,
                'iso': 'ZN',
                'iso3': 'XBK',
                'name': 'KGArbSELbuyKyuKgZFgSRnvFGZWQvkNtxBmFOYeInsqdtKzZoNVfTLgLvreKZHEBnwYePtGZtBQIumAzqNGDQWJlbOTHlKFnQVDr',
                'record_type': 5,
                'record_type_display': 'Representative Office',
                'region': 4,
                'society_name': 'UOdHmxDjpjVRWtBAueOnArsPkqRMpzphjmbpZtDFJBBPcmkribqYZrQJlPcUFYbdfuMteAxQQfzUiphKVGhHQLXHqFfpMhXZuvLVyZVVpBnjglnrCAqLdFIxShuIBERprYjxETxtbPMcVQZdSYQpqJytOSxZRhIpCyazqtfWptnkCOuZXPAYcrfXFEVAvTBgkSqGewAMUJVuDSbWdPPlOCYPiazmOtuKfhkpHTXPWiMRAYuCEViqlRLuZsmfAxlzyKobbJPNOofDmqSkdzNBMqjfxkKhaTHBXDRFhoTnmYrsVFyiBnMnsURmAlAYjbsqpNCpxLRPDfaEiuSzRnTyTBVMqegJddvpEwMQZMTVZcaqGNytzQxiJcLlqkGFvDifuTHBjqhuciFrVxBsqNWqHuBkuVFWjJQOZCdmjdolcEqkTDBhFcCwTJFDFhUjhwfnslkVGrKQLnLaHXKlAepXFRgvbsRRhzxLgujbfDTQEDOrMQavcPNC'
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
                'created_at': '2019-03-23T00:00:00.123456Z',
                'id': 2,
                'modified_at': '2019-03-23T00:00:00.123456Z',
                'name': 'dyXySiBSBJihChNxwmvBdpofLaoAVWZYIKcZaUpdediClscuwMPpsiMzEQhQeeqInFTVwoCTtxXJsPpHruSIGgdwATNFrfniHotV'
            },
            'reporting_ns': 3,
            'reporting_ns_detail': {
                'fdrs': None,
                'id': 3,
                'independent': None,
                'is_deprecated': False,
                'iso': 'ha',
                'iso3': 'tcR',
                'name': 'EZcPiEjODIvDYAVdHtKURuJIbnKRvZYwejrbvyOIkKMylMhYWtTuTcrAfFpxCtnHtlhxYcXmfCGbZEGjmvEUHtXujXgHRinUcDyT',
                'record_type': 5,
                'record_type_display': 'Representative Office',
                'region': 3,
                'society_name': 'MfvDcgHXQVtbKWtOnummsrIuXCQhrjkrhaNJGgnIwJurjTZsKpketNvICdibERdgydfBzlTMLOSSCNwtvmTWQZIfWWDKifZSDgDtRPTXDEoojNqxzlSQvYuDFbeEhwEDksXwMKiGgzTYguJPeYtIDzLApNpJkEyevnSLBYBKYvISplQQeVTKFhLMDuJgCltzeMgRMXyuFPQdfniLWOZaWjQjCIsyNKCmnRutKYRtBTwfLaNGzisdxJdaTJwhsbpBSLzOuTyzyBInQlEimJyxAjsQiiaePbjUFQBifiPZADYSMBNlDGBJCywolBMaKFUpTGrAIKxccKETxhLESfjUUHWXrDHfHNfpEOVQQeROIZLtNdvIXaEDGEKUvAwZsskcSMVtUYKqdOELkKdQsZVNbsFfiGeYrqiNrrqaVhMlLVjQCxZlqYSpFlZHcvfjMjFWAXypQCUOknKUwdPqWhdkDzEtEVWIoyRTyEqjHBasZCyRuHRcgIOw'
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
            'visibility': 'public'
        }
    ]
}

snapshots['TestProjectAPI::test_project_create 1'] = {
    'actual_expenditure': 0,
    'budget_amount': 0,
    'dtype': None,
    'dtype_detail': None,
    'end_date': '2008-01-01',
    'event': None,
    'event_detail': None,
    'id': 1,
    'modified_at': '2019-03-23T00:00:00.123456Z',
    'name': 'Mock Project for Create API Test',
    'operation_type': 1,
    'operation_type_display': 'Emergency Operation',
    'primary_sector': 6,
    'primary_sector_display': 'Shelter',
    'programme_type': 2,
    'programme_type_display': 'Domestic',
    'project_country': 1,
    'project_country_detail': {
        'fdrs': None,
        'id': 1,
        'independent': None,
        'is_deprecated': False,
        'iso': 'IR',
        'iso3': 'Zmi',
        'name': 'HcqkdsmYSNrdDPaeyQrQQxgbsPyoyGTguFMIflmGDJTbcpHtvFzVkbwRwwOtpGrZdOqybJrojvzQifUyHRNORoApKjBtMvCIinPi',
        'record_type': 5,
        'record_type_display': 'Representative Office',
        'region': 1,
        'society_name': 'tSTHiBXjPKkueJIUhlujUbWuAAtCVOVrjXmgilbWNNrMKNoMooRbwfSXEiGMETPxlyFEikmocAWarAoVQmWnelCNFSuDpBzXcMVyUuzNVKMIHPTYcHgCDcpHIzVcJyHWOdmsCztXsDkBsNdSHjDPCfUGhlXLSIizAuCblDLTmDfquSPTYkTUhfhTCOxfHTyUYGNkyJycXkvKQjkjlXTdAttUXCsOlhimaNWqaDFFIZaMFpnLQEDACfMMapJrNOJndljdPwcjcQKMtvfdgAlkRsNQSSMKYJlDVLxcfXtuxyeWBJesEihSrvHAHnSnNdgKUOHfEUSMYTsBMuqHKNwiNKFHUOFFZlNoTsmahbDOYhVnZNAAcvwJZOnaOmSsqYettGJuXahRvvzUKNblmvvREEZcPiEjODIvDYAVdHtKURuJIbnKRvZYwejrbvyOIkKMylMhYWtTuTcrAfFpxCtnHtlhxYcXmfCGbZEGjmvEUHtXujXgHRin'
    },
    'project_districts': [
        1
    ],
    'project_districts_detail': [
        {
            'code': 'gMWkIuuRZt',
            'country_iso': 'rR',
            'country_name': 'SSxgILwjaiHsxXFAvkgnjGomYJNSHITJSWZhADehibEwtSxiCMHWvlTtbVhoiSjSotinifBSWYhebXEWBcmgcYQGLdEhqcetQaWg',
            'id': 1,
            'is_deprecated': True,
            'is_enclave': True,
            'name': 'faAOrAlJDTKWimlysJFctLtFJVDobYajqtOOEhPQsAlFSPpbhWrFeMVxLEKBqOREShxGUKbqkLdjuDSiwkdrxAOwdssHOeGmXOlW'
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
        'iso': 'IR',
        'iso3': 'Zmi',
        'name': 'HcqkdsmYSNrdDPaeyQrQQxgbsPyoyGTguFMIflmGDJTbcpHtvFzVkbwRwwOtpGrZdOqybJrojvzQifUyHRNORoApKjBtMvCIinPi',
        'record_type': 5,
        'record_type_display': 'Representative Office',
        'region': 1,
        'society_name': 'tSTHiBXjPKkueJIUhlujUbWuAAtCVOVrjXmgilbWNNrMKNoMooRbwfSXEiGMETPxlyFEikmocAWarAoVQmWnelCNFSuDpBzXcMVyUuzNVKMIHPTYcHgCDcpHIzVcJyHWOdmsCztXsDkBsNdSHjDPCfUGhlXLSIizAuCblDLTmDfquSPTYkTUhfhTCOxfHTyUYGNkyJycXkvKQjkjlXTdAttUXCsOlhimaNWqaDFFIZaMFpnLQEDACfMMapJrNOJndljdPwcjcQKMtvfdgAlkRsNQSSMKYJlDVLxcfXtuxyeWBJesEihSrvHAHnSnNdgKUOHfEUSMYTsBMuqHKNwiNKFHUOFFZlNoTsmahbDOYhVnZNAAcvwJZOnaOmSsqYettGJuXahRvvzUKNblmvvREEZcPiEjODIvDYAVdHtKURuJIbnKRvZYwejrbvyOIkKMylMhYWtTuTcrAfFpxCtnHtlhxYcXmfCGbZEGjmvEUHtXujXgHRin'
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
    'visibility': 'public'
}

snapshots['TestProjectAPI::test_project_read 1'] = {
    'actual_expenditure': 0,
    'budget_amount': 0,
    'dtype': 3,
    'dtype_detail': {
        'id': 3,
        'name': 'VLHCAklbiUpQqVSVfnkzggeEJdbXzHWfgqNjfPytopVsCOiiHkbcQwuEDIrJCiSIlLMDOVOKBHOOItwEIoZfCtxAqjtaaHWiwsEI',
        'summary': 'aSFWEtaXBZsMoYaJxmAJBzpkTVPyyoqfBOpHWZNZSRrsPVIZrAmelishODNCrSNFmubjdIblgsriTCUaofjaFnvAtYZFxDSYcvfWjdrXzeIElmqyahXTpyXCpVcmDVXgHQnEyRtukOUcVJHhqEOtmxdQnhpOBuakYrLhzYpacLYSESMjxXfpkFfRNvWOddwPjSIYgiFouJYPWwZCUmbSywUiqcFTCJsISFmKlIwuUDrMJkeHjCsqIxDaXOGyUlbNxXNpuUeQIymHRFXJjNsuAPuhgHQecilcmgFmgcKPyQFHNSLqdxoMTeanPFfDZOdxJVAxYTdNrHcUetenHggUoIymmHQpKOlJVJAVgXOKwRDSQBgkYlJzGvQkIMCwuJuxAWOBUuMpKInyXJVqxCCzaUcsMbHitatonubXSrJGJKKjgcDwjiqxLpoqZtfKzKnUeUuYElFSSKgMPtcUZKyfXdXvwBAhXoVPMaOXOydtHcuIKjuGSojd'
    },
    'end_date': '2008-01-01',
    'event': 2,
    'event_detail': {
        'dtype': 1,
        'id': 2,
        'name': 'WptcCqwfChXZpnZVLSwTNOBkNiYnnZdKwIrMIkuTssKrGRgiWYAdrPiSipjTupWRzFjKOrOAyCeOYXfzGVrSxDFuLaXUfUDOQSwe',
        'parent_event': 1,
        'slug': 'yiznbnfrusvjkikfyvrwdcgoydbhkcdabmsiptkrfpxqfxqpkd'
    },
    'id': 1,
    'modified_at': '2019-03-23T00:00:00.123456Z',
    'name': 'RUzCWMKGfoBsYzjivfEKVdJzqfzGBXSiWiEJmFzPKmJNVHpperXBuRKfhQABxwmuwMPbXtkwNZCNjCcomRxjWUfhVdpNjsavSZhtCEbvnVInnIHWqJENUjSSQbyLQHcqkdsmYSNrdDPaeyQrQQxgbsPyoyGTguFMIflmGDJTbcpHtvFzVkbwRwwOtpGrZdOqybJrojvzQifUyHRNORoApKjBtMvCIinPiLIRZmitSTHiBXjPKkueJIUhlujUbWuAAtCVOVrjXmgilbWNNrMKNoMooRbwfSXEiGMETPxlyFEikmocAWarAoVQmWnelCNFSuDpBzXcMVyUuzNVKMIHPTYcHgCDcpHIzVcJyHWOdmsCztXsDkBsNdSHjDPCfUGhlXLSIizAuCblDLTmDfquSPTYkTUhfhTCOxfHTyUYGNkyJycXkvKQjkjlXTdAttUXCsOlhimaNWqaDFFIZaMFpnLQEDACfMMapJrNOJndljdPwcjcQKMt',
    'operation_type': 0,
    'operation_type_display': 'Programme',
    'primary_sector': 1,
    'primary_sector_display': 'PGI',
    'programme_type': 1,
    'programme_type_display': 'Multilateral',
    'project_country': 2,
    'project_country_detail': {
        'fdrs': None,
        'id': 2,
        'independent': None,
        'is_deprecated': False,
        'iso': 'tJ',
        'iso3': 'yPY',
        'name': 'eECOtYrLdwGetDCcdxsePfNMGyDLJYVcCZKPmuMEGjdCgZvTfGPlcpTCCHHNkxxsyAXvRMdYOPvevgJRysqUQMjvfLQjwtPSQziM',
        'record_type': 1,
        'record_type_display': 'Country',
        'region': 2,
        'society_name': 'viQSVRHfPQBGxbxtlnvXFmoijesYgGXIVHcQvXNiMyjklSXNZkUCcAxRUpCNsWVYCoIptZYEmxRKCDXsXyGHAkmZMiqdPExJgTHhsfWkrCGjBfoCwbAdzGxpyfxobugTPvYjicsESiWTECNafbqnjJUMHBhXspthdpAOYNDehFMIbOGKpTjsBaNwpKAlQQfHxeHIGYGJbyEcOyxqVbwYewpUQOgXLVWvicwIvPlXRDSEOlZieTXDcsmcYmcutGzIEqcWPmswXdPvrhZxBzVCyvlFSFxZHrZfUBfBMlIsugfuQstCMTBkSCwCcUwNBrOYdeQOzxGZVRkbjMRYCciepXPxxyKcMjRCxxCWeKiHxzuPrphbVlFHyJhqXqTCnNsSFmhieClTCfZRuQwTeJIstkTTSOlYxGohmYipYFbxJKxDZJiNfetzTUEHAXAKeiuPeCDRHwiXJOLlXiBGdhHjtkkuTowHsfqmOJriOtNIfGPkLLjkQNUM'
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
        'name': 'uxyeWBJesEihSrvHAHnSnNdgKUOHfEUSMYTsBMuqHKNwiNKFHUOFFZlNoTsmahbDOYhVnZNAAcvwJZOnaOmSsqYettGJuXahRvvz'
    },
    'reporting_ns': 1,
    'reporting_ns_detail': {
        'fdrs': None,
        'id': 1,
        'independent': None,
        'is_deprecated': False,
        'iso': 'Dy',
        'iso3': 'rOS',
        'name': 'bVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgfygwwMqZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkIUp',
        'record_type': 2,
        'record_type_display': 'Cluster',
        'region': 1,
        'society_name': 'JoRuXXdocZuzrenKTunPFzPDjqipVJIqVLBLzxoiGFfWdhjOkYRBMeyyMDHqJaRUhRIWrXPvhsBkDaUUqGWlGgOtOGMmjxWkIXHaMuFbhxZtpdpKffUFeWIXiiQEJkqHMBnIWUSmTtzQPxCHChpoevbLJoLoaeTOdoecveGprQFnIiUKKEpYEZAmggQBwBADUdRPPgdzUvZgpmmICiBlrDpeCZJgdPIafWpkAFEnzdkyayqYYDsBSUYJQTFjmsndLVIdVuddLEGHkdGfleMeRpzhKpLMcNfAQLKHuqnQTupqziQPtDuWeaDNKgeInGqiwepxskCITtNZPHaQJtQgiqhgVJjrsMnTvnROqGFqdfOBrcavXiOqkVCJTBJaheSjIcxLJjBictxYcwnRpQgwXJANVjpkZZlAblVvYAZQVZprkYSgycEomDwtYoobQmzvreXrwPGzRIvbhqlLqcgMBwUYuBMGhyKmqcTBaHZIRUVVQmxBeQvN'
    },
    'secondary_sectors': [
    ],
    'secondary_sectors_display': [
    ],
    'start_date': '2008-01-01',
    'status': 0,
    'status_display': 'Planned',
    'target_female': 0,
    'target_male': 0,
    'target_other': 0,
    'target_total': 0,
    'user': 2,
    'visibility': 'public'
}

snapshots['TestProjectAPI::test_project_update 1'] = {
    'actual_expenditure': 0,
    'budget_amount': 0,
    'dtype': 3,
    'dtype_detail': {
        'id': 3,
        'name': 'VLHCAklbiUpQqVSVfnkzggeEJdbXzHWfgqNjfPytopVsCOiiHkbcQwuEDIrJCiSIlLMDOVOKBHOOItwEIoZfCtxAqjtaaHWiwsEI',
        'summary': 'aSFWEtaXBZsMoYaJxmAJBzpkTVPyyoqfBOpHWZNZSRrsPVIZrAmelishODNCrSNFmubjdIblgsriTCUaofjaFnvAtYZFxDSYcvfWjdrXzeIElmqyahXTpyXCpVcmDVXgHQnEyRtukOUcVJHhqEOtmxdQnhpOBuakYrLhzYpacLYSESMjxXfpkFfRNvWOddwPjSIYgiFouJYPWwZCUmbSywUiqcFTCJsISFmKlIwuUDrMJkeHjCsqIxDaXOGyUlbNxXNpuUeQIymHRFXJjNsuAPuhgHQecilcmgFmgcKPyQFHNSLqdxoMTeanPFfDZOdxJVAxYTdNrHcUetenHggUoIymmHQpKOlJVJAVgXOKwRDSQBgkYlJzGvQkIMCwuJuxAWOBUuMpKInyXJVqxCCzaUcsMbHitatonubXSrJGJKKjgcDwjiqxLpoqZtfKzKnUeUuYElFSSKgMPtcUZKyfXdXvwBAhXoVPMaOXOydtHcuIKjuGSojd'
    },
    'end_date': '2008-01-01',
    'event': 2,
    'event_detail': {
        'dtype': 1,
        'id': 2,
        'name': 'WptcCqwfChXZpnZVLSwTNOBkNiYnnZdKwIrMIkuTssKrGRgiWYAdrPiSipjTupWRzFjKOrOAyCeOYXfzGVrSxDFuLaXUfUDOQSwe',
        'parent_event': 1,
        'slug': 'yiznbnfrusvjkikfyvrwdcgoydbhkcdabmsiptkrfpxqfxqpkd'
    },
    'id': 1,
    'modified_at': '2019-03-23T00:00:00.123456Z',
    'name': 'Mock Project for Update API Test',
    'operation_type': 0,
    'operation_type_display': 'Programme',
    'primary_sector': 1,
    'primary_sector_display': 'PGI',
    'programme_type': 1,
    'programme_type_display': 'Multilateral',
    'project_country': 3,
    'project_country_detail': {
        'fdrs': None,
        'id': 3,
        'independent': None,
        'is_deprecated': False,
        'iso': 'Dy',
        'iso3': 'THh',
        'name': 'vvREEZcPiEjODIvDYAVdHtKURuJIbnKRvZYwejrbvyOIkKMylMhYWtTuTcrAfFpxCtnHtlhxYcXmfCGbZEGjmvEUHtXujXgHRinU',
        'record_type': 1,
        'record_type_display': 'Country',
        'region': 3,
        'society_name': 'atcRMfvDcgHXQVtbKWtOnummsrIuXCQhrjkrhaNJGgnIwJurjTZsKpketNvICdibERdgydfBzlTMLOSSCNwtvmTWQZIfWWDKifZSDgDtRPTXDEoojNqxzlSQvYuDFbeEhwEDksXwMKiGgzTYguJPeYtIDzLApNpJkEyevnSLBYBKYvISplQQeVTKFhLMDuJgCltzeMgRMXyuFPQdfniLWOZaWjQjCIsyNKCmnRutKYRtBTwfLaNGzisdxJdaTJwhsbpBSLzOuTyzyBInQlEimJyxAjsQiiaePbjUFQBifiPZADYSMBNlDGBJCywolBMaKFUpTGrAIKxccKETxhLESfjUUHWXrDHfHNfpEOVQQeROIZLtNdvIXaEDGEKUvAwZsskcSMVtUYKqdOELkKdQsZVNbsFfiGeYrqiNrrqaVhMlLVjQCxZlqYSpFlZHcvfjMjFWAXypQCUOknKUwdPqWhdkDzEtEVWIoyRTyEqjHBasZCyRuHRc'
    },
    'project_districts': [
        1
    ],
    'project_districts_detail': [
        {
            'code': 'FnQVDrOIZN',
            'country_iso': 'XB',
            'country_name': 'KUOdHmxDjpjVRWtBAueOnArsPkqRMpzphjmbpZtDFJBBPcmkribqYZrQJlPcUFYbdfuMteAxQQfzUiphKVGhHQLXHqFfpMhXZuvL',
            'id': 1,
            'is_deprecated': True,
            'is_enclave': False,
            'name': 'IucDQBKGArbSELbuyKyuKgZFgSRnvFGZWQvkNtxBmFOYeInsqdtKzZoNVfTLgLvreKZHEBnwYePtGZtBQIumAzqNGDQWJlbOTHlK'
        }
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
        'name': 'uxyeWBJesEihSrvHAHnSnNdgKUOHfEUSMYTsBMuqHKNwiNKFHUOFFZlNoTsmahbDOYhVnZNAAcvwJZOnaOmSsqYettGJuXahRvvz'
    },
    'reporting_ns': 3,
    'reporting_ns_detail': {
        'fdrs': None,
        'id': 3,
        'independent': None,
        'is_deprecated': False,
        'iso': 'Dy',
        'iso3': 'THh',
        'name': 'vvREEZcPiEjODIvDYAVdHtKURuJIbnKRvZYwejrbvyOIkKMylMhYWtTuTcrAfFpxCtnHtlhxYcXmfCGbZEGjmvEUHtXujXgHRinU',
        'record_type': 1,
        'record_type_display': 'Country',
        'region': 3,
        'society_name': 'atcRMfvDcgHXQVtbKWtOnummsrIuXCQhrjkrhaNJGgnIwJurjTZsKpketNvICdibERdgydfBzlTMLOSSCNwtvmTWQZIfWWDKifZSDgDtRPTXDEoojNqxzlSQvYuDFbeEhwEDksXwMKiGgzTYguJPeYtIDzLApNpJkEyevnSLBYBKYvISplQQeVTKFhLMDuJgCltzeMgRMXyuFPQdfniLWOZaWjQjCIsyNKCmnRutKYRtBTwfLaNGzisdxJdaTJwhsbpBSLzOuTyzyBInQlEimJyxAjsQiiaePbjUFQBifiPZADYSMBNlDGBJCywolBMaKFUpTGrAIKxccKETxhLESfjUUHWXrDHfHNfpEOVQQeROIZLtNdvIXaEDGEKUvAwZsskcSMVtUYKqdOELkKdQsZVNbsFfiGeYrqiNrrqaVhMlLVjQCxZlqYSpFlZHcvfjMjFWAXypQCUOknKUwdPqWhdkDzEtEVWIoyRTyEqjHBasZCyRuHRc'
    },
    'secondary_sectors': [
    ],
    'secondary_sectors_display': [
    ],
    'start_date': '2008-01-01',
    'status': 0,
    'status_display': 'Planned',
    'target_female': 0,
    'target_male': 0,
    'target_other': 0,
    'target_total': 0,
    'user': 2,
    'visibility': 'public'
}

snapshots['TestProjectAPI::test_project_delete 1'] = b''
