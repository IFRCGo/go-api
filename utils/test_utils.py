import erp
from django.test import TestCase
from api.models import Event, FieldReport, Region, Country, DisasterType, ERPGUID
from main.mock import erp_request_side_effect_mock
from unittest.mock import patch

class ERPTest(TestCase):

    @patch('requests.post', side_effect=erp_request_side_effect_mock)
    def test_not_successful(self, erp_request_side_effect_mock):
        region = Region.objects.create(name=1)
        dtype = DisasterType.objects.create(name='d1', summary='foo')
        event = Event.objects.create(name='disaster1', summary='test disaster', dtype=dtype)
        report = FieldReport.objects.create(
            rid='test',
            dtype=dtype,
            event=event
        )
        result = erp.push_fr_data(report)
        self.assertEqual(erp_request_side_effect_mock.called, False)

    @patch('requests.post', side_effect=erp_request_side_effect_mock)
    def test_successful(self, erp_request_side_effect_mock):
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
        self.assertEqual(erp_request_side_effect_mock.called, True)
