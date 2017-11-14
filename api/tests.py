from django.test import TestCase

import api.models as models


class DisasterTypeTest(TestCase):

    fixtures = ['DisasterTypes']

    def test_disaster_type_data(self):
        objs = models.DisasterType.objects.all()
        self.assertEqual(len(objs), 46)


class EventTest(TestCase):
    def setUp(self):
        models.Event.objects.create(name='disaster1', description='test disaster')
        models.Event.objects.create(name='disaster2', description='another test disaster')

    def test_disaster_create(self):
        obj1 = models.Event.objects.get(name='disaster1')
        obj2 = models.Event.objects.get(name='disaster2')
        self.assertEqual(obj1.description, 'test disaster')
        self.assertEqual(obj2.description, 'another test disaster')


class CountryTest(TestCase):

    fixtures = ['Countries']

    def test_country_data(self):
        objs = models.Country.objects.all()
        self.assertEqual(objs.count(), 260)


class DocumentTest(TestCase):
    def setUp(self):
        models.Document.objects.create(name='document1', uri='/path/to/file')

    def test_document_create(self):
        obj = models.Document.objects.get(name='document1')
        self.assertEqual(obj.uri, '/path/to/file')


class AppealTest(TestCase):
    def setUp(self):
        event = models.Event.objects.create(name='disaster1', description='test disaster')
        country = models.Country.objects.create(name='country')
        models.Appeal.objects.create(aid='test1', disaster=event, country=country)

    def test_appeal_create(self):
        event = models.Event.objects.get(name='disaster1')
        self.assertEqual(event.countries(), ['country'])
        country = models.Country.objects.get(name='country')
        obj = models.Appeal.objects.get(aid='test1')
        self.assertEqual(obj.aid, 'test1')
        self.assertEqual(obj.country, country)
        self.assertEqual(obj.event, event)


class FieldReportTest(TestCase):
    def setUp(self):
        event = models.Event.objects.create(name='disaster1', description='test disaster')
        country = models.Country.objects.create(name='country')
        models.FieldReport.objects.create(fid='test1', disaster=event, country=country)

    def test_field_report_create(self):
        event = models.Event.objects.get(name='disaster1')
        self.assertEqual(event.countries(), ['country'])
        country = models.Country.objects.get(name='country')
        obj = models.FieldReport.objects.get(fid='test1')
        self.assertEqual(obj.fid, 'test1')
        self.assertEqual(obj.country, country)
        self.assertEqual(obj.event, event)


class ServiceTest(TestCase):
    def setUp(self):
        models.Service.objects.create(name='test1', location='earth')
        models.Service.objects.create(name='test2', deployed=True, location='iceland')

    def test_service_create(self):
        obj1 = models.Service.objects.get(name='test1')
        self.assertFalse(obj1.deployed)
        self.assertEqual(obj1.location, 'earth')
        obj1 = models.Service.objects.get(name='test2')
        self.assertTrue(obj1.deployed)
        self.assertEqual(obj1.location, 'iceland')
