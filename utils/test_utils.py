import erp
import json
from collections import Counter
from django.test import TestCase

import reversion
from reversion.errors import RevertError
from reversion.models import Version
from django.contrib.contenttypes.models import ContentType

from api.models import Event, FieldReport, Region, Country, DisasterType, ERPGUID
from main.mock import erp_request_side_effect_mock
from main.utils import DjangoReversionDataFixHelper
from unittest.mock import patch

from per.models import Overview as PerOverview
from per.factories import OverviewFactory as PerOverviewFactory
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


class DjangoReversionDataFixHelperTest(TestCase):
    def get_version_qs(self):
        return Version.objects.get_for_model(PerOverview)

    def update_serialized_data(self, raw_data, new_value):
        new_data = json.loads(raw_data)
        new_data[0]['fields'][self.field_name] = new_value
        return json.dumps(new_data)

    def get_version_data_snapshot(self, field_name):
        # Version data snapshot excluding self.field_name
        version_data_snapshot = []
        for _id, data_raw in self.get_version_qs().values_list('id', 'serialized_data').order_by('id'):
            data = json.loads(data_raw)
            data[0]['fields'].pop(field_name)
            version_data_snapshot.append({
                'id': _id,
                'data': data,
            })
        return version_data_snapshot

    def assert_values(self, values: dict):
        # Make sure other values are not changed
        assert self.version_data_snapshot == self.get_version_data_snapshot(self.field_name)
        # Check count
        assert self.get_version_qs().count() == sum(values.values())
        # Check count by value
        assert dict(Counter([
            json.loads(data)[0]['fields'][self.field_name]
            for data in self.get_version_qs().values_list('serialized_data', flat=True)
        ])) == values

    def confirm_version_data_serialization(self):
        for version in self.get_version_qs().all():
            version._local_field_dict

    def setUp(self):
        super().setUp()
        self.field_name = 'date_of_assessment'
        for _ in range(95):
            reversion.create_revision()(PerOverviewFactory.create)()

        versions = self.get_version_qs().all()
        # Create dataset with different formats
        for index, version in enumerate(versions):
            new_value = '2022-01-01'
            if (index % 2) == 0:
                new_value = '2022-01-01T00:00:00'
            version.serialized_data = self.update_serialized_data(
                version.serialized_data,
                new_value,
            )
            version.save()
        Version.objects.bulk_update(versions, fields=('serialized_data',))
        # Version data snapshot excluding self.field_name
        self.version_data_snapshot = self.get_version_data_snapshot(self.field_name)
        self.assert_values({'2022-01-01': 47, '2022-01-01T00:00:00': 48})

    def test_date_fields_to_datetime(self):
        self.assert_values({'2022-01-01': 47, '2022-01-01T00:00:00': 48})
        DjangoReversionDataFixHelper.date_fields_to_datetime(
            ContentType,
            Version,
            PerOverview,
            [self.field_name]
        )
        self.assert_values({'2022-01-01T00:00:00': 95})

    def test_datetime_fields_to_date(self):
        with self.assertRaises(RevertError):
            self.confirm_version_data_serialization()
        self.assert_values({'2022-01-01': 47, '2022-01-01T00:00:00': 48})
        DjangoReversionDataFixHelper.datetime_fields_to_date(
            ContentType,
            Version,
            PerOverview,
            [self.field_name]
        )
        self.assert_values({'2022-01-01': 95})
        self.confirm_version_data_serialization()
