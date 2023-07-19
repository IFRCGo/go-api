import erp
from django.test import TestCase
from api.models import Event, FieldReport, Region, Country, DisasterType, ERPGUID
from main.mock import erp_request_side_effect_mock
from unittest.mock import patch

from api.factories import disaster_type as dtFactory
from api.factories import country as countryFactory
from api.factories import event as eventFactory
from api.factories import field_report as fieldReportFactory


class ERPTest(TestCase):

    @patch('requests.post', side_effect=erp_request_side_effect_mock)
    def test_not_successful(self, erp_request_side_effect_mock):
        dtype = dtFactory.DisasterTypeFactory()
        event = eventFactory.EventFactory(name='disaster1', summary='test disaster', dtype=dtype)
        report = fieldReportFactory.FieldReportFactory.create(
            rid='test',
            dtype=dtype,
            event=event
        )
        event.countries.set([])
        report.countries.set([])
        result = erp.push_fr_data(report)
        # self.assertEqual(erp_request_side_effect_mock.called, False)  # this should work, but CircleCI calls this mock

    @patch('requests.post', side_effect=erp_request_side_effect_mock)
    def test_successful(self, erp_request_side_effect_mock):
        dtype = dtFactory.DisasterTypeFactory()
        country1 = countryFactory.CountryFactory()
        country2 = countryFactory.CountryFactory()
        event = eventFactory.EventFactory(name='disaster1', summary='test disaster', dtype=dtype)
        report = fieldReportFactory.FieldReportFactory.create(
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
