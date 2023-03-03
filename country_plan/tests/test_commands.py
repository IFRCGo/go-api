from unittest import mock
from django.core.management import call_command

from main.test_case import APITestCase
from api.factories.country import CountryFactory
from country_plan.factories import CountryPlanFactory
from country_plan.models import CountryPlan
from country_plan.management.commands.ingest_country_plan_file import PUBLIC_SOURCE, INTERNAL_SOURCE

# NOTE: Only defined used fields
FILE_BASE_DIRECTORY = 'https://example.org/Download.aspx?FileId='
PUBLIC_APPEAL_COUNTRY_PLAN_MOCK_RESPONSE = [
    {
        'BaseDirectory': FILE_BASE_DIRECTORY,
        'BaseFileName': '000000',
        'Inserted': '2022-11-29T11:24:00',
        'LocationCountryCode': 'SY',
        'LocationCountryName': 'Syrian Arab Republic'
    },
    {
        'BaseDirectory': FILE_BASE_DIRECTORY,
        'BaseFileName': '000001',
        'Inserted': '2022-11-29T11:24:00',
        'LocationCountryCode': 'CD',
        'LocationCountryName': 'Congo, The Democratic Republic Of The'
    },
    # Not included in INTERNAL
    {
        'BaseDirectory': FILE_BASE_DIRECTORY,
        'BaseFileName': '000002',
        'Inserted': '2022-11-29T11:24:00',
        'LocationCountryCode': 'MM',
        'LocationCountryName': 'Myanmar'
    },
    {
        'BaseDirectory': FILE_BASE_DIRECTORY,
        'BaseFileName': '000003',
        'Inserted': '2022-11-29T11:24:00',
        'LocationCountryCode': 'TM',
        'LocationCountryName': 'Turkmenistan'
    },
    {
        'BaseDirectory': FILE_BASE_DIRECTORY,
        'BaseFileName': '000004',
        'Inserted': '2022-11-29T11:24:00',
        'LocationCountryCode': 'GR',
        'LocationCountryName': 'Greece'
    },
    {
        'BaseDirectory': FILE_BASE_DIRECTORY,
        'BaseFileName': 'NOOP',
        'Inserted': '2022-11-29T11:24:00',
        'LocationCountryCode': 'XY',
        'LocationCountryName': 'Myanmar'
    },
]

INTERNAL_APPEAL_COUNTRY_PLAN_MOCK_RESPONSE = [
    {
        'BaseDirectory': FILE_BASE_DIRECTORY,
        'BaseFileName': '000000',
        'Inserted': '2022-11-29T11:24:00',
        'LocationCountryCode': 'SY',
        'LocationCountryName': 'Syrian Arab Republic'
    },
    {
        'BaseDirectory': FILE_BASE_DIRECTORY,
        'BaseFileName': '000001',
        'Inserted': '2022-11-29T11:24:00',
        'LocationCountryCode': 'CD',
        'LocationCountryName': 'Congo, The Democratic Republic Of The'
    },
    # Not included in PUBLIC
    {
        'BaseDirectory': FILE_BASE_DIRECTORY,
        'BaseFileName': '000001',
        'Inserted': '2022-11-29T11:24:00',
        'LocationCountryCode': 'NP',
        'LocationCountryName': 'Nepal'
    },
]


class MockResponse():
    class FileStream():
        def __init__(self, stream):
            self.stream = stream

        def raise_for_status(self):
            pass

        def iter_content(self, **_):
            return self.stream

    def __init__(self, json=None, stream=None, headers=None):
        self._headers = headers
        self._json = json
        self.stream = stream

    def json(self):
        return self._json

    @property
    def headers(self):
        return self._headers

    def __enter__(self):
        return MockResponse.FileStream(self.stream)

    def __exit__(self, *_):
        pass


class CountryPlanIngestTest(APITestCase):
    def mock_request(url, *_, **kwargs):
        if url == PUBLIC_SOURCE:
            return MockResponse(json=PUBLIC_APPEAL_COUNTRY_PLAN_MOCK_RESPONSE)
        if url == INTERNAL_SOURCE:
            return MockResponse(json=INTERNAL_APPEAL_COUNTRY_PLAN_MOCK_RESPONSE)
        if url.startswith(FILE_BASE_DIRECTORY):
            return MockResponse(stream=[b''])

    def mock_request_head(url, *_, **kwargs):
        headers = {
            'Content-Type': 'application/pdf',
            'Content-Disposition': 'attachment;filename=Sample_document_2023.pdf',
        }
        if url.endswith('NOOP'):
            headers['Content-Type'] = 'html/text'
        elif url.endswith('000004'):
            headers['Content-Disposition'] = ''
        return MockResponse(headers=headers)

    @mock.patch('country_plan.management.commands.ingest_country_plan_file.requests.head', side_effect=mock_request_head)
    @mock.patch('country_plan.management.commands.ingest_country_plan_file.requests.get', side_effect=mock_request)
    @mock.patch('main.utils.requests.get', side_effect=mock_request)
    def test_country_plan_ingest(self, *_):
        CountryPlanFactory.create(
            country=CountryFactory.create(
                name='Random Country',
                iso='RC',
            ),
        )
        EXISTING_CP = 1
        for country_iso in set([
                item['LocationCountryCode']
                for item in [
                    *PUBLIC_APPEAL_COUNTRY_PLAN_MOCK_RESPONSE,
                    *INTERNAL_APPEAL_COUNTRY_PLAN_MOCK_RESPONSE,
                ]
        ]):
            if country_iso == 'CD':
                # Not create country for this
                continue
            CountryFactory.create(iso=country_iso)
        # Before
        assert CountryPlan.objects.count() == EXISTING_CP
        assert CountryPlan.objects.filter(is_publish=True).count() == 0
        assert CountryPlan.objects.exclude(public_plan_file='').count() == 0
        call_command('ingest_country_plan_file')
        # After
        assert CountryPlan.objects.count() == EXISTING_CP + 5
        assert CountryPlan.objects.filter(is_publish=True).count() == 5
        assert CountryPlan.objects.exclude(public_plan_file='').count() == 4
        assert CountryPlan.objects.exclude(internal_plan_file='').count() == 2
        # First downloaded document. Others will have Sample_document_2023{random-chars}.pdf
        assert CountryPlan.objects.filter(country__iso='SY').first().public_plan_file.name.endswith('Sample_document_2023.pdf')
        # Without attachment filename
        assert CountryPlan.objects.filter(country__iso='GR').first().public_plan_file.name.endswith('document.pdf')
