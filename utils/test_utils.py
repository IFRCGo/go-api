import erp
from django.test import TestCase
from api.models import Event, FieldReport, Region, Country, DisasterType, ERPGUID
from unittest import mock


class ERPTest(TestCase):
    def setUp(self):
        pass
        # Did not succeed to set up FieldReport here

    def mocked_requests_post0(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.text       = 'FindThisGUID'
                self.status_code = status_code

            def json(self):
                return self.json_data

        return MockResponse(None, 400)

    def mocked_requests_post1(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.text       = 'FindThisGUID'
                self.status_code = status_code

            def json(self):
                return self.json_data

        return MockResponse(None, 200)

    @mock.patch('requests.post', side_effect=mocked_requests_post0)
    def test_not_successful(self, mocked_requests_post0):
        region = Region.objects.create(name=1)
        dtype = DisasterType.objects.create(name='d1', summary='foo')
        event = Event.objects.create(name='disaster1', summary='test disaster', dtype=dtype)
        report = FieldReport.objects.create(
            rid='test',
            dtype=dtype,
            event=event
        )
        result = erp.push_fr_data(report)
        self.assertEqual(mocked_requests_post0.call_count, 1)

    @mock.patch('requests.post', side_effect=mocked_requests_post1)
    def test_successful(self, mocked_requests_post1):
        region = Region.objects.create(name=1)
        country1 = Country.objects.create(name='c1', iso='HU', region=region)
        country2 = Country.objects.create(name='c2', iso='CH')
        dtype = DisasterType.objects.create(name='d1', summary='foo')
        event = Event.objects.create(name='disaster1', summary='test disaster', dtype=dtype)
        report = FieldReport.objects.create(
            rid='test',
            dtype=dtype,
            event=event
        )
        report.countries.add(country1)
        report.countries.add(country2)
        result = erp.push_fr_data(report)
        ERP = ERPGUID.objects.get(api_guid='FindThisGUID')
        self.assertEqual(ERP.api_guid, 'FindThisGUID')
        self.assertEqual(ERP.field_report_id, report.id)
