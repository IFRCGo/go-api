from unittest import mock
from django.core.management import call_command

from main.test_case import APITestCase
from api.factories.country import CountryFactory
from country_plan.factories import CountryPlanFactory
from country_plan.models import CountryPlan
from country_plan.management.commands.ingest_country_plan_file import SOURCE

# NOTE: Only defined used fields
FILE_BASE_DIRECTORY = 'https://example.org/Download.aspx?FileId='
APPEAL_COUNTRY_PLAN_MOCK_RESPONSE = [
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
    }
]


class MockResponse():
    class FileStream():
        def __init__(self, stream):
            self.stream = stream

        def raise_for_status(self):
            pass

        def iter_content(self, **_):
            return self.stream

    def __init__(self, json=None, stream=None):
        self._json = json
        self.stream = stream

    def json(self):
        return self._json

    def __enter__(self):
        return MockResponse.FileStream(self.stream)

    def __exit__(self, *_):
        pass


class CountryPlanIngestTest(APITestCase):
    def mock_request(url, *_, **kwargs):
        if url == SOURCE:
            return MockResponse(json=APPEAL_COUNTRY_PLAN_MOCK_RESPONSE)
        if url.startswith(FILE_BASE_DIRECTORY):
            return MockResponse(stream=[b''])

    @mock.patch('country_plan.management.commands.ingest_country_plan_file.requests.get', side_effect=mock_request)
    @mock.patch('main.utils.requests.get', side_effect=mock_request)
    def test_country_plan_ingest(self, *_):
        CountryPlanFactory.create(
            country=CountryFactory.create(
                name='Random Country',
                iso='RC',
            ),
        )
        for country_plan_data in APPEAL_COUNTRY_PLAN_MOCK_RESPONSE[:3]:
            CountryPlanFactory.create(
                country=CountryFactory.create(
                    name=country_plan_data['LocationCountryName'],
                    iso=country_plan_data['LocationCountryCode'],
                ),
            )
        assert CountryPlan.objects.count() == 4
        assert CountryPlan.objects.filter(is_publish=True).count() == 0
        assert CountryPlan.objects.exclude(public_plan_file='').count() == 0
        call_command('ingest_country_plan_file')
        assert CountryPlan.objects.count() == 4
        assert CountryPlan.objects.filter(is_publish=True).count() == 3
        assert CountryPlan.objects.exclude(public_plan_file='').count() == 3
