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
                'name': 'CXxVLHCAklbiUpQqVSVfnkzggeEJdbXzHWfgqNjfPytopVsCOiiHkbcQwuEDIrJCiSIlLMDOVOKBHOOItwEIoZfCtxAqjtaaHWiw',
                'summary': 'sEIaSFWEtaXBZsMoYaJxmAJBzpkTVPyyoqfBOpHWZNZSRrsPVIZrAmelishODNCrSNFmubjdIblgsriTCUaofjaFnvAtYZFxDSYcvfWjdrXzeIElmqyahXTpyXCpVcmDVXgHQnEyRtukOUcVJHhqEOtmxdQnhpOBuakYrLhzYpacLYSESMjxXfpkFfRNvWOddwPjSIYgiFouJYPWwZCUmbSywUiqcFTCJsISFmKlIwuUDrMJkeHjCsqIxDaXOGyUlbNxXNpuUeQIymHRFXJjNsuAPuhgHQecilcmgFmgcKPyQFHNSLqdxoMTeanPFfDZOdxJVAxYTdNrHcUetenHggUoIymmHQpKOlJVJAVgXOKwRDSQBgkYlJzGvQkIMCwuJuxAWOBUuMpKInyXJVqxCCzaUcsMbHitatonubXSrJGJKKjgcDwjiqxLpoqZtfKzKnUeUuYElFSSKgMPtcUZKyfXdXvwBAhXoVPMaOXOydtHcuIKjuGS'
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
            'name': 'ojdRUzCWMKGfoBsYzjivfEKVdJzqfzGBXSiWiEJmFzPKmJNVHpperXBuRKfhQABxwmuwMPbXtkwNZCNjCcomRxjWUfhVdpNjsavSZhtCEbvnVInnIHWqJENUjSSQbyLQHcqkdsmYSNrdDPaeyQrQQxgbsPyoyGTguFMIflmGDJTbcpHtvFzVkbwRwwOtpGrZdOqybJrojvzQifUyHRNORoApKjBtMvCIinPiLIRZmitSTHiBXjPKkueJIUhlujUbWuAAtCVOVrjXmgilbWNNrMKNoMooRbwfSXEiGMETPxlyFEikmocAWarAoVQmWnelCNFSuDpBzXcMVyUuzNVKMIHPTYcHgCDcpHIzVcJyHWOdmsCztXsDkBsNdSHjDPCfUGhlXLSIizAuCblDLTmDfquSPTYkTUhfhTCOxfHTyUYGNkyJycXkvKQjkjlXTdAttUXCsOlhimaNWqaDFFIZaMFpnLQEDACfMMapJrNOJndljdPwcjcQ',
            'operation_type': 1,
            'operation_type_display': 'Emergency Operation',
            'primary_sector': 9,
            'primary_sector_display': 'Livelihoods and basic needs',
            'programme_type': 2,
            'programme_type_display': 'Domestic',
            'project_country': 2,
            'project_country_detail': {
                'id': 2,
                'independent': None,
                'is_deprecated': False,
                'iso': 'tJ',
                'iso3': 'yPY',
                'name': 'eECOtYrLdwGetDCcdxsePfNMGyDLJYVcCZKPmuMEGjdCgZvTfGPlcpTCCHHNkxxsyAXvRMdYOPvevgJRysqUQMjvfLQjwtPSQziM',
                'record_type': 1,
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
                'name': 'cfXtuxyeWBJesEihSrvHAHnSnNdgKUOHfEUSMYTsBMuqHKNwiNKFHUOFFZlNoTsmahbDOYhVnZNAAcvwJZOnaOmSsqYettGJuXah'
            },
            'reporting_ns': 1,
            'reporting_ns_detail': {
                'id': 1,
                'independent': None,
                'is_deprecated': False,
                'iso': 'Dy',
                'iso3': 'rOS',
                'name': 'bVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgfygwwMqZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkIUp',
                'record_type': 2,
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
                'name': 'CXxVLHCAklbiUpQqVSVfnkzggeEJdbXzHWfgqNjfPytopVsCOiiHkbcQwuEDIrJCiSIlLMDOVOKBHOOItwEIoZfCtxAqjtaaHWiw',
                'summary': 'sEIaSFWEtaXBZsMoYaJxmAJBzpkTVPyyoqfBOpHWZNZSRrsPVIZrAmelishODNCrSNFmubjdIblgsriTCUaofjaFnvAtYZFxDSYcvfWjdrXzeIElmqyahXTpyXCpVcmDVXgHQnEyRtukOUcVJHhqEOtmxdQnhpOBuakYrLhzYpacLYSESMjxXfpkFfRNvWOddwPjSIYgiFouJYPWwZCUmbSywUiqcFTCJsISFmKlIwuUDrMJkeHjCsqIxDaXOGyUlbNxXNpuUeQIymHRFXJjNsuAPuhgHQecilcmgFmgcKPyQFHNSLqdxoMTeanPFfDZOdxJVAxYTdNrHcUetenHggUoIymmHQpKOlJVJAVgXOKwRDSQBgkYlJzGvQkIMCwuJuxAWOBUuMpKInyXJVqxCCzaUcsMbHitatonubXSrJGJKKjgcDwjiqxLpoqZtfKzKnUeUuYElFSSKgMPtcUZKyfXdXvwBAhXoVPMaOXOydtHcuIKjuGS'
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
            'name': 'ojdRUzCWMKGfoBsYzjivfEKVdJzqfzGBXSiWiEJmFzPKmJNVHpperXBuRKfhQABxwmuwMPbXtkwNZCNjCcomRxjWUfhVdpNjsavSZhtCEbvnVInnIHWqJENUjSSQbyLQHcqkdsmYSNrdDPaeyQrQQxgbsPyoyGTguFMIflmGDJTbcpHtvFzVkbwRwwOtpGrZdOqybJrojvzQifUyHRNORoApKjBtMvCIinPiLIRZmitSTHiBXjPKkueJIUhlujUbWuAAtCVOVrjXmgilbWNNrMKNoMooRbwfSXEiGMETPxlyFEikmocAWarAoVQmWnelCNFSuDpBzXcMVyUuzNVKMIHPTYcHgCDcpHIzVcJyHWOdmsCztXsDkBsNdSHjDPCfUGhlXLSIizAuCblDLTmDfquSPTYkTUhfhTCOxfHTyUYGNkyJycXkvKQjkjlXTdAttUXCsOlhimaNWqaDFFIZaMFpnLQEDACfMMapJrNOJndljdPwcjcQ',
            'operation_type': 1,
            'operation_type_display': 'Emergency Operation',
            'primary_sector': 9,
            'primary_sector_display': 'Livelihoods and basic needs',
            'programme_type': 2,
            'programme_type_display': 'Domestic',
            'project_country': 2,
            'project_country_detail': {
                'id': 2,
                'independent': None,
                'is_deprecated': False,
                'iso': 'tJ',
                'iso3': 'yPY',
                'name': 'eECOtYrLdwGetDCcdxsePfNMGyDLJYVcCZKPmuMEGjdCgZvTfGPlcpTCCHHNkxxsyAXvRMdYOPvevgJRysqUQMjvfLQjwtPSQziM',
                'record_type': 1,
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
                'name': 'cfXtuxyeWBJesEihSrvHAHnSnNdgKUOHfEUSMYTsBMuqHKNwiNKFHUOFFZlNoTsmahbDOYhVnZNAAcvwJZOnaOmSsqYettGJuXah'
            },
            'reporting_ns': 1,
            'reporting_ns_detail': {
                'id': 1,
                'independent': None,
                'is_deprecated': False,
                'iso': 'Dy',
                'iso3': 'rOS',
                'name': 'bVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgfygwwMqZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkIUp',
                'record_type': 2,
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
                'name': 'RAyuOCZkltalQKOMchvwENMIakHVqhmMbIbHGWjnxhnbuiofUSirrEmfwTJPsDVZFBGzmqlmRTrzgLYXLtkYnUFBCBMVruNgMyBm',
                'summary': 'KwxOeCkcGqLAsMPHwzbhlZuBYlwpenQxxjXuhauSaTvnDKYuoJeysMnHngJrTMZQeKPARWBuummdZFFcrAhhCkMuLypKbsbPYKaDsizcIHcvPbeEgZAUtruWwzfJXuFNdztSDFPhxNgbodaiguSUBokfmUZxIaSdqYchdteqvSNYZyrSkiLDhiujWLAOCQhHHpKEQFruXUEofqXsTfwJpQPVnSeeFdnaQnDymFgvnLWHGuWtTDPjGgioxyCNGmXzmerBkRtKPgjDgVhpbDlrbEQHCwqhJfwBnjzGBGvdCrxgdPyUBmsmzlMrHMFHBgRdPphohdcKrpeIgroNSTzzzgoUSrFnkYnwOsTMsUaglGSNEVtSpkuReklvDjaQEBvblqekRWaMwELaFpEhcbKRsoHGkWjXggtZVvCFVwIqQFqxDawtTvHXQMEhrRHUObjAoQjwFbpKVSBxnVfmyOgrORICHlqRwvzLArtmcLHSvNhBYDKYYwsh'
            },
            'end_date': '2008-01-01',
            'event': 4,
            'event_detail': {
                'dtype': 4,
                'id': 4,
                'name': 'EYQNekGyWPWGxFHDluTxHSETFErLzOYLPcnomCpzntByKkxqJfiWfsCHwoLcDGNvBCDBAxZFuryblCoqPewfsGGIPfYroghexcIm',
                'parent_event': 3,
                'slug': 'vmrvqtvxrrmtmiwtviqaxtswyzzlwpaepgwjzoouvneohlyjwd'
            },
            'id': 2,
            'modified_at': '2019-03-23T00:00:00.123456Z',
            'name': 'aFRjDRjHsNJQktFseZsaDcnsLhdFtaBwQadqiwsYGQXJjfTrjUmBLfsocEwpZROyBzgqtMtlKBRuZLiRXmqiAJmttftKODIlyYBgiHCSuGRTwDwBDAADbJbXAfWiNtYpLGxiNIKsdWzizQaDZWHDdfdrPgvMgsKESvdhVLRGVTdSnHjJVFioROjtOtUaZFNSmheajMhHgpngEbGCzdhtzElpIqNRCQNhBjObljVQpkGVSImEEssQgLFxQrzySZgDABjbsDhKyaLtcPPQNCcwiDUDrakwGGnwTHyGelPjwPUKvDTYirYWQtzePEyEMQlKTGXQHqiSuLLwLNzecbUkogQgFREuWoXZUYpglUyWAedNqhcVeCWxMOblugSCyiOKJmmqFCRsomVkBHZYmfLbOQgncZiaxXAKIevlRUUPHFmnKEGwwNJiZeCBOyeKfiYHtghFodMIvbosqyTwekseIKpHNGtzNdIShLEqPbcvAqmvWdinJUvW',
            'operation_type': 0,
            'operation_type_display': 'Programme',
            'primary_sector': 0,
            'primary_sector_display': 'WASH',
            'programme_type': 2,
            'programme_type_display': 'Domestic',
            'project_country': 4,
            'project_country_detail': {
                'id': 4,
                'independent': None,
                'is_deprecated': False,
                'iso': 'Fn',
                'iso3': 'QVD',
                'name': 'bIucDQBKGArbSELbuyKyuKgZFgSRnvFGZWQvkNtxBmFOYeInsqdtKzZoNVfTLgLvreKZHEBnwYePtGZtBQIumAzqNGDQWJlbOTHl',
                'record_type': 5,
                'region': 4,
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
            'regional_project': 2,
            'regional_project_detail': {
                'created_at': '2019-03-23T00:00:00.123456Z',
                'id': 2,
                'modified_at': '2019-03-23T00:00:00.123456Z',
                'name': 'UcgcFGoPwBEtYobdbXYZmIMyRRVbJEdyXySiBSBJihChNxwmvBdpofLaoAVWZYIKcZaUpdediClscuwMPpsiMzEQhQeeqInFTVwo'
            },
            'reporting_ns': 3,
            'reporting_ns_detail': {
                'id': 3,
                'independent': None,
                'is_deprecated': False,
                'iso': 'nU',
                'iso3': 'cDy',
                'name': 'NblmvvREEZcPiEjODIvDYAVdHtKURuJIbnKRvZYwejrbvyOIkKMylMhYWtTuTcrAfFpxCtnHtlhxYcXmfCGbZEGjmvEUHtXujXgH',
                'record_type': 2,
                'region': 3,
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
    'operation_type': 0,
    'operation_type_display': 'Programme',
    'primary_sector': 2,
    'primary_sector_display': 'CEA',
    'programme_type': 0,
    'programme_type_display': 'Bilateral',
    'project_country': 1,
    'project_country_detail': {
        'id': 1,
        'independent': None,
        'is_deprecated': False,
        'iso': 'in',
        'iso3': 'PiL',
        'name': None,
        'record_type': 5,
        'region': 1,
        'society_name': None
    },
    'project_districts': [
        1
    ],
    'project_districts_detail': [
        {
            'code': 'mXOlWgMWkI',
            'country_iso': 'uu',
            'country_name': 'RZtrRSSxgILwjaiHsxXFAvkgnjGomYJNSHITJSWZhADehibEwtSxiCMHWvlTtbVhoiSjSotinifBSWYhebXEWBcmgcYQGLdEhqce',
            'id': 1,
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
    'reporting_ns': 1,
    'reporting_ns_detail': {
        'id': 1,
        'independent': None,
        'is_deprecated': False,
        'iso': 'in',
        'iso3': 'PiL',
        'name': None,
        'record_type': 5,
        'region': 1,
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
    'user': 2,
    'visibility': 'public'
}

snapshots['TestProjectAPI::test_project_read 1'] = {
    'actual_expenditure': 0,
    'budget_amount': 0,
    'dtype': 3,
    'dtype_detail': {
        'id': 3,
        'name': 'CXxVLHCAklbiUpQqVSVfnkzggeEJdbXzHWfgqNjfPytopVsCOiiHkbcQwuEDIrJCiSIlLMDOVOKBHOOItwEIoZfCtxAqjtaaHWiw',
        'summary': 'sEIaSFWEtaXBZsMoYaJxmAJBzpkTVPyyoqfBOpHWZNZSRrsPVIZrAmelishODNCrSNFmubjdIblgsriTCUaofjaFnvAtYZFxDSYcvfWjdrXzeIElmqyahXTpyXCpVcmDVXgHQnEyRtukOUcVJHhqEOtmxdQnhpOBuakYrLhzYpacLYSESMjxXfpkFfRNvWOddwPjSIYgiFouJYPWwZCUmbSywUiqcFTCJsISFmKlIwuUDrMJkeHjCsqIxDaXOGyUlbNxXNpuUeQIymHRFXJjNsuAPuhgHQecilcmgFmgcKPyQFHNSLqdxoMTeanPFfDZOdxJVAxYTdNrHcUetenHggUoIymmHQpKOlJVJAVgXOKwRDSQBgkYlJzGvQkIMCwuJuxAWOBUuMpKInyXJVqxCCzaUcsMbHitatonubXSrJGJKKjgcDwjiqxLpoqZtfKzKnUeUuYElFSSKgMPtcUZKyfXdXvwBAhXoVPMaOXOydtHcuIKjuGS'
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
    'name': 'ojdRUzCWMKGfoBsYzjivfEKVdJzqfzGBXSiWiEJmFzPKmJNVHpperXBuRKfhQABxwmuwMPbXtkwNZCNjCcomRxjWUfhVdpNjsavSZhtCEbvnVInnIHWqJENUjSSQbyLQHcqkdsmYSNrdDPaeyQrQQxgbsPyoyGTguFMIflmGDJTbcpHtvFzVkbwRwwOtpGrZdOqybJrojvzQifUyHRNORoApKjBtMvCIinPiLIRZmitSTHiBXjPKkueJIUhlujUbWuAAtCVOVrjXmgilbWNNrMKNoMooRbwfSXEiGMETPxlyFEikmocAWarAoVQmWnelCNFSuDpBzXcMVyUuzNVKMIHPTYcHgCDcpHIzVcJyHWOdmsCztXsDkBsNdSHjDPCfUGhlXLSIizAuCblDLTmDfquSPTYkTUhfhTCOxfHTyUYGNkyJycXkvKQjkjlXTdAttUXCsOlhimaNWqaDFFIZaMFpnLQEDACfMMapJrNOJndljdPwcjcQ',
    'operation_type': 1,
    'operation_type_display': 'Emergency Operation',
    'primary_sector': 9,
    'primary_sector_display': 'Livelihoods and basic needs',
    'programme_type': 2,
    'programme_type_display': 'Domestic',
    'project_country': 2,
    'project_country_detail': {
        'id': 2,
        'independent': None,
        'is_deprecated': False,
        'iso': 'tJ',
        'iso3': 'yPY',
        'name': 'eECOtYrLdwGetDCcdxsePfNMGyDLJYVcCZKPmuMEGjdCgZvTfGPlcpTCCHHNkxxsyAXvRMdYOPvevgJRysqUQMjvfLQjwtPSQziM',
        'record_type': 1,
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
        'name': 'cfXtuxyeWBJesEihSrvHAHnSnNdgKUOHfEUSMYTsBMuqHKNwiNKFHUOFFZlNoTsmahbDOYhVnZNAAcvwJZOnaOmSsqYettGJuXah'
    },
    'reporting_ns': 1,
    'reporting_ns_detail': {
        'id': 1,
        'independent': None,
        'is_deprecated': False,
        'iso': 'Dy',
        'iso3': 'rOS',
        'name': 'bVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgfygwwMqZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkIUp',
        'record_type': 2,
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
        'name': 'CXxVLHCAklbiUpQqVSVfnkzggeEJdbXzHWfgqNjfPytopVsCOiiHkbcQwuEDIrJCiSIlLMDOVOKBHOOItwEIoZfCtxAqjtaaHWiw',
        'summary': 'sEIaSFWEtaXBZsMoYaJxmAJBzpkTVPyyoqfBOpHWZNZSRrsPVIZrAmelishODNCrSNFmubjdIblgsriTCUaofjaFnvAtYZFxDSYcvfWjdrXzeIElmqyahXTpyXCpVcmDVXgHQnEyRtukOUcVJHhqEOtmxdQnhpOBuakYrLhzYpacLYSESMjxXfpkFfRNvWOddwPjSIYgiFouJYPWwZCUmbSywUiqcFTCJsISFmKlIwuUDrMJkeHjCsqIxDaXOGyUlbNxXNpuUeQIymHRFXJjNsuAPuhgHQecilcmgFmgcKPyQFHNSLqdxoMTeanPFfDZOdxJVAxYTdNrHcUetenHggUoIymmHQpKOlJVJAVgXOKwRDSQBgkYlJzGvQkIMCwuJuxAWOBUuMpKInyXJVqxCCzaUcsMbHitatonubXSrJGJKKjgcDwjiqxLpoqZtfKzKnUeUuYElFSSKgMPtcUZKyfXdXvwBAhXoVPMaOXOydtHcuIKjuGS'
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
    'operation_type': 1,
    'operation_type_display': 'Emergency Operation',
    'primary_sector': 9,
    'primary_sector_display': 'Livelihoods and basic needs',
    'programme_type': 2,
    'programme_type_display': 'Domestic',
    'project_country': 3,
    'project_country_detail': {
        'id': 3,
        'independent': None,
        'is_deprecated': False,
        'iso': 'HR',
        'iso3': 'inU',
        'name': 'UKNblmvvREEZcPiEjODIvDYAVdHtKURuJIbnKRvZYwejrbvyOIkKMylMhYWtTuTcrAfFpxCtnHtlhxYcXmfCGbZEGjmvEUHtXujX',
        'record_type': 1,
        'region': 3,
        'society_name': 'cDyTHhatcRMfvDcgHXQVtbKWtOnummsrIuXCQhrjkrhaNJGgnIwJurjTZsKpketNvICdibERdgydfBzlTMLOSSCNwtvmTWQZIfWWDKifZSDgDtRPTXDEoojNqxzlSQvYuDFbeEhwEDksXwMKiGgzTYguJPeYtIDzLApNpJkEyevnSLBYBKYvISplQQeVTKFhLMDuJgCltzeMgRMXyuFPQdfniLWOZaWjQjCIsyNKCmnRutKYRtBTwfLaNGzisdxJdaTJwhsbpBSLzOuTyzyBInQlEimJyxAjsQiiaePbjUFQBifiPZADYSMBNlDGBJCywolBMaKFUpTGrAIKxccKETxhLESfjUUHWXrDHfHNfpEOVQQeROIZLtNdvIXaEDGEKUvAwZsskcSMVtUYKqdOELkKdQsZVNbsFfiGeYrqiNrrqaVhMlLVjQCxZlqYSpFlZHcvfjMjFWAXypQCUOknKUwdPqWhdkDzEtEVWIoyRTyEqjHBasZC'
    },
    'project_districts': [
        1
    ],
    'project_districts_detail': [
        {
            'code': 'OTHlKFnQVD',
            'country_iso': 'rO',
            'country_name': 'IZNXBKUOdHmxDjpjVRWtBAueOnArsPkqRMpzphjmbpZtDFJBBPcmkribqYZrQJlPcUFYbdfuMteAxQQfzUiphKVGhHQLXHqFfpMh',
            'id': 1,
            'is_deprecated': False,
            'is_enclave': False,
            'name': 'thvkbIucDQBKGArbSELbuyKyuKgZFgSRnvFGZWQvkNtxBmFOYeInsqdtKzZoNVfTLgLvreKZHEBnwYePtGZtBQIumAzqNGDQWJlb'
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
        'name': 'cfXtuxyeWBJesEihSrvHAHnSnNdgKUOHfEUSMYTsBMuqHKNwiNKFHUOFFZlNoTsmahbDOYhVnZNAAcvwJZOnaOmSsqYettGJuXah'
    },
    'reporting_ns': 3,
    'reporting_ns_detail': {
        'id': 3,
        'independent': None,
        'is_deprecated': False,
        'iso': 'HR',
        'iso3': 'inU',
        'name': 'UKNblmvvREEZcPiEjODIvDYAVdHtKURuJIbnKRvZYwejrbvyOIkKMylMhYWtTuTcrAfFpxCtnHtlhxYcXmfCGbZEGjmvEUHtXujX',
        'record_type': 1,
        'region': 3,
        'society_name': 'cDyTHhatcRMfvDcgHXQVtbKWtOnummsrIuXCQhrjkrhaNJGgnIwJurjTZsKpketNvICdibERdgydfBzlTMLOSSCNwtvmTWQZIfWWDKifZSDgDtRPTXDEoojNqxzlSQvYuDFbeEhwEDksXwMKiGgzTYguJPeYtIDzLApNpJkEyevnSLBYBKYvISplQQeVTKFhLMDuJgCltzeMgRMXyuFPQdfniLWOZaWjQjCIsyNKCmnRutKYRtBTwfLaNGzisdxJdaTJwhsbpBSLzOuTyzyBInQlEimJyxAjsQiiaePbjUFQBifiPZADYSMBNlDGBJCywolBMaKFUpTGrAIKxccKETxhLESfjUUHWXrDHfHNfpEOVQQeROIZLtNdvIXaEDGEKUvAwZsskcSMVtUYKqdOELkKdQsZVNbsFfiGeYrqiNrrqaVhMlLVjQCxZlqYSpFlZHcvfjMjFWAXypQCUOknKUwdPqWhdkDzEtEVWIoyRTyEqjHBasZC'
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
