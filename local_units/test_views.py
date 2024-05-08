import factory
import datetime

from django.contrib.gis.geos import Point

from .models import LocalUnit, LocalUnitType, DelegationOffice, DelegationOfficeType
from api.models import Country, Region
from main.test_case import APITestCase


class LocalUnitFactory(factory.django.DjangoModelFactory):
    location = Point(12, 38)
    date_of_data = factory.fuzzy.FuzzyDate(datetime.date(2024, 1, 2))

    class Meta:
        model = LocalUnit


class TestLocalUnitsListView(APITestCase):
    def setUp(self):
        super().setUp()
        region = Region.objects.create(name=2)
        country = Country.objects.create(
            name='Nepal',
            iso3='NLP',
            iso='NP',
            region=region
        )
        country_1 = Country.objects.create(
            name='Philippines',
            iso3='PHL',
            iso='PH',
            region=region
        )
        type = LocalUnitType.objects.create(code=0, name='Code 0')
        type_1 = LocalUnitType.objects.create(code=1, name='Code 1')
        LocalUnitFactory.create_batch(
            5,
            country=country,
            type=type,
            draft=True,
            validated=False,
            date_of_data='2023-09-09'
        )
        LocalUnitFactory.create_batch(
            5,
            country=country_1,
            type=type_1,
            draft=False,
            validated=True,
            date_of_data='2023-08-08'
        )

    def test_list(self):
        self.authenticate()
        response = self.client.get('/api/v2/local-units/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 10)
        # TODO: fix these asaywltdi
        # self.assertEqual(response.data['results'][0]['location_details']['coordinates'], [12, 38])
        # self.assertEqual(response.data['results'][0]['country_details']['name'], 'Nepal')
        # self.assertEqual(response.data['results'][0]['country_details']['iso3'], 'NLP')
        # self.assertEqual(response.data['results'][0]['type_details']['name'], 'Code 0')
        # self.assertEqual(response.data['results'][0]['type_details']['code'], 0)

    def test_filter(self):
        self.authenticate()
        response = self.client.get('/api/v2/local-units/?country__name=Nepal')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 5)

        response = self.client.get('/api/v2/local-units/?country__name=Philippines')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 5)

        response = self.client.get('/api/v2/local-units/?country__name=Belgium')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        response = self.client.get('/api/v2/local-units/?country__iso=BE')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        response = self.client.get('/api/v2/local-units/?country__iso3=BEL')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        response = self.client.get('/api/v2/local-units/?country__iso=BE')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        response = self.client.get('/api/v2/local-units/?country__iso3=PHL')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 5)

        response = self.client.get('/api/v2/local-units/?country__iso=NP')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 5)

        response = self.client.get('/api/v2/local-units/?type__code=0')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 5)

        response = self.client.get('/api/v2/local-units/?type__code=4')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        response = self.client.get('/api/v2/local-units/?draft=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 5)

        response = self.client.get('/api/v2/local-units/?draft=false')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 5)

        response = self.client.get('/api/v2/local-units/?validated=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 5)

        response = self.client.get('/api/v2/local-units/?validated=false')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 5)


class TestLocalUnitsDetailView(APITestCase):
    def setUp(self):
        super().setUp()
        region = Region.objects.create(name=2)
        country = Country.objects.create(name='Nepal', iso3='NLP', region=region)
        type = LocalUnitType.objects.create(code=0, name='Code 0')
        LocalUnitFactory.create_batch(2, country=country, type=type)

    def test_detail(self):
        local_unit = LocalUnit.objects.all().first()
        self.authenticate()
        response = self.client.get(f'/api/v2/local-units/{local_unit.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['location_details']['coordinates'], [12, 38])
        self.assertEqual(response.data['country_details']['name'], 'Nepal')
        self.assertEqual(response.data['country_details']['iso3'], 'NLP')
        self.assertEqual(response.data['type_details']['name'], 'Code 0')
        self.assertEqual(response.data['type_details']['code'], 0)

    def test_validate_local_units(self):
        local_unit = LocalUnit.objects.all().first()
        self.authenticate()
        url = f'/api/v2/local-units/{local_unit.id}/validate/'
        data = {}
        response = self.client.post(url, data=data)
        self.assert_403(response)

        # authenticate with super user
        self.client.force_authenticate(self.root_user)
        response = self.client.post(url, data=data)
        self.assert_200(response)


class DelegationOfficeFactory(factory.django.DjangoModelFactory):
    location = Point(2.2, 3.3)

    class Meta:
        model = DelegationOffice


class TestDelegationOfficesListView(APITestCase):
    def setUp(self):
        region = Region.objects.create(name=2)
        country = Country.objects.create(name='Nepal', iso3='NLP', iso='NP', region=region)
        country_1 = Country.objects.create(name='Philippines', iso3='PHL', iso='PH', region=region)
        type = DelegationOfficeType.objects.create(code=0, name='Code 0')
        type_1 = DelegationOfficeType.objects.create(code=1, name='Code 1')
        DelegationOfficeFactory.create_batch(5, country=country, dotype=type)
        DelegationOfficeFactory.create_batch(5, country=country_1, dotype=type_1)

    def test_list(self):
        response = self.client.get('/api/v2/delegation-office/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 10)
        self.assertEqual(response.data['results'][0]['location']['coordinates'], [2.2, 3.3])
        self.assertEqual(response.data['results'][0]['country']['name'], 'Nepal')
        self.assertEqual(response.data['results'][0]['country']['iso3'], 'NLP')
        self.assertEqual(response.data['results'][0]['dotype']['name'], 'Code 0')
        self.assertEqual(response.data['results'][0]['dotype']['code'], 0)

    def test_filter(self):
        response = self.client.get('/api/v2/delegation-office/?country__name=Nepal')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 5)

        response = self.client.get('/api/v2/delegation-office/?country__name=Philippines')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 5)

        response = self.client.get('/api/v2/delegation-office/?country__name=Belgium')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        response = self.client.get('/api/v2/delegation-office/?country__iso=BE')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        response = self.client.get('/api/v2/delegation-office/?country__iso3=BEL')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        response = self.client.get('/api/v2/delegation-office/?country__iso=BE')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        response = self.client.get('/api/v2/delegation-office/?country__iso3=PHL')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 5)

        response = self.client.get('/api/v2/delegation-office/?country__iso=NP')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 5)

        response = self.client.get('/api/v2/delegation-office/?dotype__code=0')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 5)

        response = self.client.get('/api/v2/delegation-office/?dotype__code=4')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)


class TestDelegationOfficesDetailView(APITestCase):
    def setUp(self):
        region = Region.objects.create(name=2)
        country = Country.objects.create(name='Nepal', iso3='NLP', region=region)
        type = DelegationOfficeType.objects.create(code=0, name='Code 0')
        DelegationOfficeFactory.create_batch(2, country=country, dotype=type)

    def test_detail(self):
        local_unit = DelegationOffice.objects.all().first()
        self.authenticate()
        response = self.client.get(f'/api/v2/delegation-office/{local_unit.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['location']['coordinates'], [2.2, 3.3])
        self.assertEqual(response.data['country']['name'], 'Nepal')
        self.assertEqual(response.data['country']['iso3'], 'NLP')
        self.assertEqual(response.data['dotype']['name'], 'Code 0')
        self.assertEqual(response.data['dotype']['code'], 0)
