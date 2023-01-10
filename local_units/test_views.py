import factory
from django.test import TestCase
from django.contrib.gis.geos import Point

from .models import LocalUnit, LocalUnitType
from api.models import Country, Region


class LocalUnitFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LocalUnit
    
    location = Point(12, 38)


class TestLocalUnitsListView(TestCase):
    def setUp(self):
        region = Region.objects.create(name=2)
        country = Country.objects.create(name='Nepal', iso3='NLP', region=region)
        country_1 = Country.objects.create(name='Philippines', iso3='PHL', region=region)
        type = LocalUnitType.objects.create(level=0, name='Level 0')
        type_1 = LocalUnitType.objects.create(level=1, name='Level 1')
        LocalUnitFactory.create_batch(5, country=country, type=type)
        LocalUnitFactory.create_batch(5, country=country_1, type=type_1)

    def test_list(self):
        response = self.client.get('/api/v2/local-unit/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 10)
        self.assertEqual(response.data['results'][0]['location']['coordinates'], [12, 38])
        self.assertEqual(response.data['results'][0]['country']['name'], 'Nepal')
        self.assertEqual(response.data['results'][0]['country']['iso3'], 'NLP')
        self.assertEqual(response.data['results'][0]['type']['name'], 'Level 0')
        self.assertEqual(response.data['results'][0]['type']['level'], 0)

    def test_filter(self):
        response = self.client.get('/api/v2/local-unit/?country__name=Nepal')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 5)

        response = self.client.get('/api/v2/local-unit/?country__name=Philippines')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 5)

        response = self.client.get('/api/v2/local-unit/?country__name=Belgium')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)


class TestLocalUnitsDetailView(TestCase):
    def setUp(self):
        region = Region.objects.create(name=2)
        country = Country.objects.create(name='Nepal', iso3='NLP', region=region)
        type = LocalUnitType.objects.create(level=0, name='Level 0')
        LocalUnitFactory.create_batch(2, country=country, type=type)

    def test_detail(self):
        response = self.client.get('/api/v2/local-unit/1/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['location']['coordinates'], [12, 38])
        self.assertEqual(response.data['country']['name'], 'Nepal')
        self.assertEqual(response.data['country']['iso3'], 'NLP')
        self.assertEqual(response.data['type']['name'], 'Level 0')
        self.assertEqual(response.data['type']['level'], 0)
