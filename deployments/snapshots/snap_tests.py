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
            'dtype': 72,
            'dtype_detail': {
                'id': 72,
                'name': 'CXxVLHCAklbiUpQqVSVfnkzggeEJdbXzHWfgqNjfPytopVsCOiiHkbcQwuEDIrJCiSIlLMDOVOKBHOOItwEIoZfCtxAqjtaaHWiw',
                'summary': 'sEIaSFWEtaXBZsMoYaJxmAJBzpkTVPyyoqfBOpHWZNZSRrsPVIZrAmelishODNCrSNFmubjdIblgsriTCUaofjaFnvAtYZFxDSYcvfWjdrXzeIElmqyahXTpyXCpVcmDVXgHQnEyRtukOUcVJHhqEOtmxdQnhpOBuakYrLhzYpacLYSESMjxXfpkFfRNvWOddwPjSIYgiFouJYPWwZCUmbSywUiqcFTCJsISFmKlIwuUDrMJkeHjCsqIxDaXOGyUlbNxXNpuUeQIymHRFXJjNsuAPuhgHQecilcmgFmgcKPyQFHNSLqdxoMTeanPFfDZOdxJVAxYTdNrHcUetenHggUoIymmHQpKOlJVJAVgXOKwRDSQBgkYlJzGvQkIMCwuJuxAWOBUuMpKInyXJVqxCCzaUcsMbHitatonubXSrJGJKKjgcDwjiqxLpoqZtfKzKnUeUuYElFSSKgMPtcUZKyfXdXvwBAhXoVPMaOXOydtHcuIKjuGS'
            },
            'end_date': '2008-01-01',
            'event': 8,
            'event_detail': {
                'dtype': 70,
                'id': 8,
                'name': 'WptcCqwfChXZpnZVLSwTNOBkNiYnnZdKwIrMIkuTssKrGRgiWYAdrPiSipjTupWRzFjKOrOAyCeOYXfzGVrSxDFuLaXUfUDOQSwe',
                'parent_event': 7,
                'slug': 'yiznbnfrusvjkikfyvrwdcgoydbhkcdabmsiptkrfpxqfxqpkd'
            },
            'id': 25,
            'modified_at': '2019-03-23T00:00:00.123456Z',
            'name': 'ojdRUzCWMKGfoBsYzjivfEKVdJzqfzGBXSiWiEJmFzPKmJNVHpperXBuRKfhQABxwmuwMPbXtkwNZCNjCcomRxjWUfhVdpNjsavSZhtCEbvnVInnIHWqJENUjSSQbyLQHcqkdsmYSNrdDPaeyQrQQxgbsPyoyGTguFMIflmGDJTbcpHtvFzVkbwRwwOtpGrZdOqybJrojvzQifUyHRNORoApKjBtMvCIinPiLIRZmitSTHiBXjPKkueJIUhlujUbWuAAtCVOVrjXmgilbWNNrMKNoMooRbwfSXEiGMETPxlyFEikmocAWarAoVQmWnelCNFSuDpBzXcMVyUuzNVKMIHPTYcHgCDcpHIzVcJyHWOdmsCztXsDkBsNdSHjDPCfUGhlXLSIizAuCblDLTmDfquSPTYkTUhfhTCOxfHTyUYGNkyJycXkvKQjkjlXTdAttUXCsOlhimaNWqaDFFIZaMFpnLQEDACfMMapJrNOJndljdPwcjcQ',
            'operation_type': 1,
            'operation_type_display': 'Emergency Operation',
            'primary_sector': 9,
            'primary_sector_display': 'Livelihoods and basic needs',
            'programme_type': 2,
            'programme_type_display': 'Domestic',
            'project_country': 328,
            'project_country_detail': {
                'id': 328,
                'independent': None,
                'is_deprecated': False,
                'iso': 'tJ',
                'iso3': 'yPY',
                'name': 'eECOtYrLdwGetDCcdxsePfNMGyDLJYVcCZKPmuMEGjdCgZvTfGPlcpTCCHHNkxxsyAXvRMdYOPvevgJRysqUQMjvfLQjwtPSQziM',
                'record_type': 1,
                'region': 16,
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
                'name': 'cfXtuxyeWBJesEihSrvHAHnSnNdgKUOHfEUSMYTsBMuqHKNwiNKFHUOFFZlNoTsmahbDOYhVnZNAAcvwJZOnaOmSsqYettGJuXah'
            },
            'reporting_ns': 327,
            'reporting_ns_detail': {
                'id': 327,
                'independent': None,
                'is_deprecated': False,
                'iso': 'Dy',
                'iso3': 'rOS',
                'name': 'bVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgfygwwMqZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkIUp',
                'record_type': 2,
                'region': 15,
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
            'user': 48,
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
            'dtype': 75,
            'dtype_detail': {
                'id': 75,
                'name': 'CXxVLHCAklbiUpQqVSVfnkzggeEJdbXzHWfgqNjfPytopVsCOiiHkbcQwuEDIrJCiSIlLMDOVOKBHOOItwEIoZfCtxAqjtaaHWiw',
                'summary': 'sEIaSFWEtaXBZsMoYaJxmAJBzpkTVPyyoqfBOpHWZNZSRrsPVIZrAmelishODNCrSNFmubjdIblgsriTCUaofjaFnvAtYZFxDSYcvfWjdrXzeIElmqyahXTpyXCpVcmDVXgHQnEyRtukOUcVJHhqEOtmxdQnhpOBuakYrLhzYpacLYSESMjxXfpkFfRNvWOddwPjSIYgiFouJYPWwZCUmbSywUiqcFTCJsISFmKlIwuUDrMJkeHjCsqIxDaXOGyUlbNxXNpuUeQIymHRFXJjNsuAPuhgHQecilcmgFmgcKPyQFHNSLqdxoMTeanPFfDZOdxJVAxYTdNrHcUetenHggUoIymmHQpKOlJVJAVgXOKwRDSQBgkYlJzGvQkIMCwuJuxAWOBUuMpKInyXJVqxCCzaUcsMbHitatonubXSrJGJKKjgcDwjiqxLpoqZtfKzKnUeUuYElFSSKgMPtcUZKyfXdXvwBAhXoVPMaOXOydtHcuIKjuGS'
            },
            'end_date': '2008-01-01',
            'event': 10,
            'event_detail': {
                'dtype': 73,
                'id': 10,
                'name': 'WptcCqwfChXZpnZVLSwTNOBkNiYnnZdKwIrMIkuTssKrGRgiWYAdrPiSipjTupWRzFjKOrOAyCeOYXfzGVrSxDFuLaXUfUDOQSwe',
                'parent_event': 9,
                'slug': 'yiznbnfrusvjkikfyvrwdcgoydbhkcdabmsiptkrfpxqfxqpkd'
            },
            'id': 26,
            'modified_at': '2019-03-23T00:00:00.123456Z',
            'name': 'ojdRUzCWMKGfoBsYzjivfEKVdJzqfzGBXSiWiEJmFzPKmJNVHpperXBuRKfhQABxwmuwMPbXtkwNZCNjCcomRxjWUfhVdpNjsavSZhtCEbvnVInnIHWqJENUjSSQbyLQHcqkdsmYSNrdDPaeyQrQQxgbsPyoyGTguFMIflmGDJTbcpHtvFzVkbwRwwOtpGrZdOqybJrojvzQifUyHRNORoApKjBtMvCIinPiLIRZmitSTHiBXjPKkueJIUhlujUbWuAAtCVOVrjXmgilbWNNrMKNoMooRbwfSXEiGMETPxlyFEikmocAWarAoVQmWnelCNFSuDpBzXcMVyUuzNVKMIHPTYcHgCDcpHIzVcJyHWOdmsCztXsDkBsNdSHjDPCfUGhlXLSIizAuCblDLTmDfquSPTYkTUhfhTCOxfHTyUYGNkyJycXkvKQjkjlXTdAttUXCsOlhimaNWqaDFFIZaMFpnLQEDACfMMapJrNOJndljdPwcjcQ',
            'operation_type': 1,
            'operation_type_display': 'Emergency Operation',
            'primary_sector': 9,
            'primary_sector_display': 'Livelihoods and basic needs',
            'programme_type': 2,
            'programme_type_display': 'Domestic',
            'project_country': 330,
            'project_country_detail': {
                'id': 330,
                'independent': None,
                'is_deprecated': False,
                'iso': 'tJ',
                'iso3': 'yPY',
                'name': 'eECOtYrLdwGetDCcdxsePfNMGyDLJYVcCZKPmuMEGjdCgZvTfGPlcpTCCHHNkxxsyAXvRMdYOPvevgJRysqUQMjvfLQjwtPSQziM',
                'record_type': 1,
                'region': 18,
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
            'regional_project': 2,
            'regional_project_detail': {
                'created_at': '2019-03-23T00:00:00.123456Z',
                'id': 2,
                'modified_at': '2019-03-23T00:00:00.123456Z',
                'name': 'cfXtuxyeWBJesEihSrvHAHnSnNdgKUOHfEUSMYTsBMuqHKNwiNKFHUOFFZlNoTsmahbDOYhVnZNAAcvwJZOnaOmSsqYettGJuXah'
            },
            'reporting_ns': 329,
            'reporting_ns_detail': {
                'id': 329,
                'independent': None,
                'is_deprecated': False,
                'iso': 'Dy',
                'iso3': 'rOS',
                'name': 'bVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgfygwwMqZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkIUp',
                'record_type': 2,
                'region': 17,
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
            'user': 49,
            'visibility': 'public'
        },
        {
            'actual_expenditure': 0,
            'budget_amount': 0,
            'dtype': 78,
            'dtype_detail': {
                'id': 78,
                'name': 'RAyuOCZkltalQKOMchvwENMIakHVqhmMbIbHGWjnxhnbuiofUSirrEmfwTJPsDVZFBGzmqlmRTrzgLYXLtkYnUFBCBMVruNgMyBm',
                'summary': 'KwxOeCkcGqLAsMPHwzbhlZuBYlwpenQxxjXuhauSaTvnDKYuoJeysMnHngJrTMZQeKPARWBuummdZFFcrAhhCkMuLypKbsbPYKaDsizcIHcvPbeEgZAUtruWwzfJXuFNdztSDFPhxNgbodaiguSUBokfmUZxIaSdqYchdteqvSNYZyrSkiLDhiujWLAOCQhHHpKEQFruXUEofqXsTfwJpQPVnSeeFdnaQnDymFgvnLWHGuWtTDPjGgioxyCNGmXzmerBkRtKPgjDgVhpbDlrbEQHCwqhJfwBnjzGBGvdCrxgdPyUBmsmzlMrHMFHBgRdPphohdcKrpeIgroNSTzzzgoUSrFnkYnwOsTMsUaglGSNEVtSpkuReklvDjaQEBvblqekRWaMwELaFpEhcbKRsoHGkWjXggtZVvCFVwIqQFqxDawtTvHXQMEhrRHUObjAoQjwFbpKVSBxnVfmyOgrORICHlqRwvzLArtmcLHSvNhBYDKYYwsh'
            },
            'end_date': '2008-01-01',
            'event': 12,
            'event_detail': {
                'dtype': 76,
                'id': 12,
                'name': 'EYQNekGyWPWGxFHDluTxHSETFErLzOYLPcnomCpzntByKkxqJfiWfsCHwoLcDGNvBCDBAxZFuryblCoqPewfsGGIPfYroghexcIm',
                'parent_event': 11,
                'slug': 'vmrvqtvxrrmtmiwtviqaxtswyzzlwpaepgwjzoouvneohlyjwd'
            },
            'id': 27,
            'modified_at': '2019-03-23T00:00:00.123456Z',
            'name': 'aFRjDRjHsNJQktFseZsaDcnsLhdFtaBwQadqiwsYGQXJjfTrjUmBLfsocEwpZROyBzgqtMtlKBRuZLiRXmqiAJmttftKODIlyYBgiHCSuGRTwDwBDAADbJbXAfWiNtYpLGxiNIKsdWzizQaDZWHDdfdrPgvMgsKESvdhVLRGVTdSnHjJVFioROjtOtUaZFNSmheajMhHgpngEbGCzdhtzElpIqNRCQNhBjObljVQpkGVSImEEssQgLFxQrzySZgDABjbsDhKyaLtcPPQNCcwiDUDrakwGGnwTHyGelPjwPUKvDTYirYWQtzePEyEMQlKTGXQHqiSuLLwLNzecbUkogQgFREuWoXZUYpglUyWAedNqhcVeCWxMOblugSCyiOKJmmqFCRsomVkBHZYmfLbOQgncZiaxXAKIevlRUUPHFmnKEGwwNJiZeCBOyeKfiYHtghFodMIvbosqyTwekseIKpHNGtzNdIShLEqPbcvAqmvWdinJUvW',
            'operation_type': 0,
            'operation_type_display': 'Programme',
            'primary_sector': 0,
            'primary_sector_display': 'WASH',
            'programme_type': 2,
            'programme_type_display': 'Domestic',
            'project_country': 332,
            'project_country_detail': {
                'id': 332,
                'independent': None,
                'is_deprecated': False,
                'iso': 'Fn',
                'iso3': 'QVD',
                'name': 'bIucDQBKGArbSELbuyKyuKgZFgSRnvFGZWQvkNtxBmFOYeInsqdtKzZoNVfTLgLvreKZHEBnwYePtGZtBQIumAzqNGDQWJlbOTHl',
                'record_type': 5,
                'region': 20,
                'society_name': 'rOIZNXBKUOdHmxDjpjVRWtBAueOnArsPkqRMpzphjmbpZtDFJBBPcmkribqYZrQJlPcUFYbdfuMteAxQQfzUiphKVGhHQLXHqFfpMhXZuvLVyZVVpBnjglnrCAqLdFIxShuIBERprYjxETxtbPMcVQZdSYQpqJytOSxZRhIpCyazqtfWptnkCOuZXPAYcrfXFEVAvTBgkSqGewAMUJVuDSbWdPPlOCYPiazmOtuKfhkpHTXPWiMRAYuCEViqlRLuZsmfAxlzyKobbJPNOofDmqSkdzNBMqjfxkKhaTHBXDRFhoTnmYrsVFyiBnMnsURmAlAYjbsqpNCpxLRPDfaEiuSzRnTyTBVMqegJddvpEwMQZMTVZcaqGNytzQxiJcLlqkGFvDifuTHBjqhuciFrVxBsqNWqHuBkuVFWjJQOZCdmjdolcEqkTDBhFcCwTJFDFhUjhwfnslkVGrKQLnLaHXKlAepXFRgvbsRRhzxLgujbfDTQEDOr'
            },
            'project_districts': [
            ],
            'project_districts_detail': [
            ],
            'reached_female': 0,
            'reached_male': 0,
            'reached_other': 0,
            'reached_total': 0,
            'regional_project': 3,
            'regional_project_detail': {
                'created_at': '2019-03-23T00:00:00.123456Z',
                'id': 3,
                'modified_at': '2019-03-23T00:00:00.123456Z',
                'name': 'UcgcFGoPwBEtYobdbXYZmIMyRRVbJEdyXySiBSBJihChNxwmvBdpofLaoAVWZYIKcZaUpdediClscuwMPpsiMzEQhQeeqInFTVwo'
            },
            'reporting_ns': 331,
            'reporting_ns_detail': {
                'id': 331,
                'independent': None,
                'is_deprecated': False,
                'iso': 'nU',
                'iso3': 'cDy',
                'name': 'NblmvvREEZcPiEjODIvDYAVdHtKURuJIbnKRvZYwejrbvyOIkKMylMhYWtTuTcrAfFpxCtnHtlhxYcXmfCGbZEGjmvEUHtXujXgH',
                'record_type': 2,
                'region': 19,
                'society_name': 'THhatcRMfvDcgHXQVtbKWtOnummsrIuXCQhrjkrhaNJGgnIwJurjTZsKpketNvICdibERdgydfBzlTMLOSSCNwtvmTWQZIfWWDKifZSDgDtRPTXDEoojNqxzlSQvYuDFbeEhwEDksXwMKiGgzTYguJPeYtIDzLApNpJkEyevnSLBYBKYvISplQQeVTKFhLMDuJgCltzeMgRMXyuFPQdfniLWOZaWjQjCIsyNKCmnRutKYRtBTwfLaNGzisdxJdaTJwhsbpBSLzOuTyzyBInQlEimJyxAjsQiiaePbjUFQBifiPZADYSMBNlDGBJCywolBMaKFUpTGrAIKxccKETxhLESfjUUHWXrDHfHNfpEOVQQeROIZLtNdvIXaEDGEKUvAwZsskcSMVtUYKqdOELkKdQsZVNbsFfiGeYrqiNrrqaVhMlLVjQCxZlqYSpFlZHcvfjMjFWAXypQCUOknKUwdPqWhdkDzEtEVWIoyRTyEqjHBasZCyRu'
            },
            'secondary_sectors': [
            ],
            'secondary_sectors_display': [
            ],
            'start_date': '2008-01-01',
            'status': 2,
            'status_display': 'Completed',
            'target_female': 0,
            'target_male': 0,
            'target_other': 0,
            'target_total': 0,
            'user': 50,
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
    'id': 24,
    'modified_at': '2019-03-23T00:00:00.123456Z',
    'name': 'Mock Project for Create API Test',
    'operation_type': 0,
    'operation_type_display': 'Programme',
    'primary_sector': 2,
    'primary_sector_display': 'CEA',
    'programme_type': 0,
    'programme_type_display': 'Bilateral',
    'project_country': 326,
    'project_country_detail': {
        'id': 326,
        'independent': None,
        'is_deprecated': False,
        'iso': 'in',
        'iso3': 'PiL',
        'name': None,
        'record_type': 5,
        'region': 14,
        'society_name': None
    },
    'project_districts': [
        16
    ],
    'project_districts_detail': [
        {
            'code': 'mXOlWgMWkI',
            'country_iso': 'uu',
            'country_name': 'RZtrRSSxgILwjaiHsxXFAvkgnjGomYJNSHITJSWZhADehibEwtSxiCMHWvlTtbVhoiSjSotinifBSWYhebXEWBcmgcYQGLdEhqce',
            'id': 16,
            'is_deprecated': True,
            'is_enclave': False,
            'name': 'veLWyfaAOrAlJDTKWimlysJFctLtFJVDobYajqtOOEhPQsAlFSPpbhWrFeMVxLEKBqOREShxGUKbqkLdjuDSiwkdrxAOwdssHOeG'
        }
    ],
    'reached_female': 0,
    'reached_male': 0,
    'reached_other': 0,
    'reached_total': 0,
    'regional_project': None,
    'regional_project_detail': None,
    'reporting_ns': 326,
    'reporting_ns_detail': {
        'id': 326,
        'independent': None,
        'is_deprecated': False,
        'iso': 'in',
        'iso3': 'PiL',
        'name': None,
        'record_type': 5,
        'region': 14,
        'society_name': None
    },
    'secondary_sectors': [
    ],
    'secondary_sectors_display': [
    ],
    'start_date': '2008-01-01',
    'status': 2,
    'status_display': 'Completed',
    'target_female': 0,
    'target_male': 0,
    'target_other': 0,
    'target_total': 0,
    'user': 47,
    'visibility': 'public'
}

snapshots['TestProjectAPI::test_project_read 1'] = {
    'actual_expenditure': 0,
    'budget_amount': 0,
    'dtype': 81,
    'dtype_detail': {
        'id': 81,
        'name': 'CXxVLHCAklbiUpQqVSVfnkzggeEJdbXzHWfgqNjfPytopVsCOiiHkbcQwuEDIrJCiSIlLMDOVOKBHOOItwEIoZfCtxAqjtaaHWiw',
        'summary': 'sEIaSFWEtaXBZsMoYaJxmAJBzpkTVPyyoqfBOpHWZNZSRrsPVIZrAmelishODNCrSNFmubjdIblgsriTCUaofjaFnvAtYZFxDSYcvfWjdrXzeIElmqyahXTpyXCpVcmDVXgHQnEyRtukOUcVJHhqEOtmxdQnhpOBuakYrLhzYpacLYSESMjxXfpkFfRNvWOddwPjSIYgiFouJYPWwZCUmbSywUiqcFTCJsISFmKlIwuUDrMJkeHjCsqIxDaXOGyUlbNxXNpuUeQIymHRFXJjNsuAPuhgHQecilcmgFmgcKPyQFHNSLqdxoMTeanPFfDZOdxJVAxYTdNrHcUetenHggUoIymmHQpKOlJVJAVgXOKwRDSQBgkYlJzGvQkIMCwuJuxAWOBUuMpKInyXJVqxCCzaUcsMbHitatonubXSrJGJKKjgcDwjiqxLpoqZtfKzKnUeUuYElFSSKgMPtcUZKyfXdXvwBAhXoVPMaOXOydtHcuIKjuGS'
    },
    'end_date': '2008-01-01',
    'event': 14,
    'event_detail': {
        'dtype': 79,
        'id': 14,
        'name': 'WptcCqwfChXZpnZVLSwTNOBkNiYnnZdKwIrMIkuTssKrGRgiWYAdrPiSipjTupWRzFjKOrOAyCeOYXfzGVrSxDFuLaXUfUDOQSwe',
        'parent_event': 13,
        'slug': 'yiznbnfrusvjkikfyvrwdcgoydbhkcdabmsiptkrfpxqfxqpkd'
    },
    'id': 28,
    'modified_at': '2019-03-23T00:00:00.123456Z',
    'name': 'ojdRUzCWMKGfoBsYzjivfEKVdJzqfzGBXSiWiEJmFzPKmJNVHpperXBuRKfhQABxwmuwMPbXtkwNZCNjCcomRxjWUfhVdpNjsavSZhtCEbvnVInnIHWqJENUjSSQbyLQHcqkdsmYSNrdDPaeyQrQQxgbsPyoyGTguFMIflmGDJTbcpHtvFzVkbwRwwOtpGrZdOqybJrojvzQifUyHRNORoApKjBtMvCIinPiLIRZmitSTHiBXjPKkueJIUhlujUbWuAAtCVOVrjXmgilbWNNrMKNoMooRbwfSXEiGMETPxlyFEikmocAWarAoVQmWnelCNFSuDpBzXcMVyUuzNVKMIHPTYcHgCDcpHIzVcJyHWOdmsCztXsDkBsNdSHjDPCfUGhlXLSIizAuCblDLTmDfquSPTYkTUhfhTCOxfHTyUYGNkyJycXkvKQjkjlXTdAttUXCsOlhimaNWqaDFFIZaMFpnLQEDACfMMapJrNOJndljdPwcjcQ',
    'operation_type': 1,
    'operation_type_display': 'Emergency Operation',
    'primary_sector': 9,
    'primary_sector_display': 'Livelihoods and basic needs',
    'programme_type': 2,
    'programme_type_display': 'Domestic',
    'project_country': 334,
    'project_country_detail': {
        'id': 334,
        'independent': None,
        'is_deprecated': False,
        'iso': 'tJ',
        'iso3': 'yPY',
        'name': 'eECOtYrLdwGetDCcdxsePfNMGyDLJYVcCZKPmuMEGjdCgZvTfGPlcpTCCHHNkxxsyAXvRMdYOPvevgJRysqUQMjvfLQjwtPSQziM',
        'record_type': 1,
        'region': 22,
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
    'regional_project': 4,
    'regional_project_detail': {
        'created_at': '2019-03-23T00:00:00.123456Z',
        'id': 4,
        'modified_at': '2019-03-23T00:00:00.123456Z',
        'name': 'cfXtuxyeWBJesEihSrvHAHnSnNdgKUOHfEUSMYTsBMuqHKNwiNKFHUOFFZlNoTsmahbDOYhVnZNAAcvwJZOnaOmSsqYettGJuXah'
    },
    'reporting_ns': 333,
    'reporting_ns_detail': {
        'id': 333,
        'independent': None,
        'is_deprecated': False,
        'iso': 'Dy',
        'iso3': 'rOS',
        'name': 'bVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgfygwwMqZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkIUp',
        'record_type': 2,
        'region': 21,
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
    'user': 51,
    'visibility': 'public'
}
