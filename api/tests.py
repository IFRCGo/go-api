from django.test import TestCase

import api.models as models


class DiasterTest(TestCase):
    def setUp(self):
        models.Disaster.create(name='disaster1', description='test disaster')
        models.Disaster.create(name='disaster2', description='another test disaster')

    def test_disaster_create(self):
        obj1 = models.Disaster.objects.get(name='disaster1')
        obj2 = models.Disaster.objects.get(name='disaster2')
        self.assertEqual(obj1.description, 'test disaster')
        self.assertEqual(obj2.description, 'another test disaster')


class CountryTest(TestCase):
    def setUp(self):
        models.Country.create(name='country1')

    def test_country_create(self):
        obj = models.Country.objects.get(name='country1')
        self.assertEqual(obj.name, 'country1')


class DocumentTest(TestCase):
    def setUp(self):
        models.Document.create(name='document1', uri='/path/to/file')

    def test_document_create(self):
        obj = models.Document.objects.get(name='document1')
        self.assertEqual(obj.uri, '/path/to/file')


class AppealTest(TestCase):
    def setUp(self):
        disaster = models.Disaster.create(name='disaster1', description='test disaster')
        models.Appeal.create(name='test1', disaster=disaster)

    def test_appeal_create(self):
        disaster = models.Disaster.objects.get(name='disaster1')
        country = models.Country.objects.get(name='country')
        obj = models.Appeal.objects.get(name='test1')
        self.assertRqual(obj.description, 'test disaster')
        self.assertEqual(obj.country, country)
        self.assertEqual(obj.disaster, disaster)


class FieldReportTest(TestCase):
    def setUp(self):
        disaster = models.Disaster.create(name='disaster1', description='test disaster')
        country = models.Country.create(name='country')
        models.FieldReport.create(name='test1', disaster=disaster, country=country)

    def test_field_report_create(self):
        disaster = models.Disaster.objects.get(name='disaster1')
        country = models.Country.objects.get(name='country')
        obj = models.FieldReport.objects.get(name='test1')
        self.assertRqual(obj.description, 'test disaster')
        self.assertEqual(obj.country, country)
        self.assertEqual(obj.disaster, disaster)


class ServiceTest(TestCase):
    def setUp(self):
        models.Service.create(name='test1', location='earth')
        models.Service.create(name='test2', deployed=True, location='iceland')

    def test_service_create(self):
        obj1 = models.Service.objects.get(name='test1')
        self.assertFalse(obj1.deployed)
        self.assertEqual(obj1.location, 'earth')
        obj1 = models.Service.objects.get(name='test2')
        self.assertTrue(obj1.deployed)
        self.assertEqual(obj1.location, 'iceland')

