from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory
from rest_framework.test import APITestCase

import api.models as models
import api.drf_views as views


class DisasterTypeTest(TestCase):

    fixtures = ['DisasterTypes']

    def test_disaster_type_data(self):
        objs = models.DisasterType.objects.all()
        self.assertEqual(len(objs), 24)


class EventTest(TestCase):

    fixtures = ['DisasterTypes']

    def setUp(self):
        dtype = models.DisasterType.objects.get(pk=1)
        models.Event.objects.create(name='disaster1', summary='test disaster', dtype=dtype)
        event = models.Event.objects.create(name='disaster2', summary='another test disaster', dtype=dtype)
        models.KeyFigure.objects.create(event=event, number=7, deck='things', source='website')
        models.Snippet.objects.create(event=event, snippet='this is a snippet')

    def test_disaster_create(self):
        obj1 = models.Event.objects.get(name='disaster1')
        obj2 = models.Event.objects.get(name='disaster2')
        self.assertEqual(obj1.summary, 'test disaster')
        self.assertEqual(obj2.summary, 'another test disaster')
        keyfig = obj2.key_figures.all()
        self.assertEqual(keyfig[0].deck, 'things')
        self.assertEqual(keyfig[0].number, '7')
        snippet = obj2.snippets.all()
        self.assertEqual(snippet[0].snippet, 'this is a snippet')


class CountryTest(TestCase):

    fixtures = ['Regions', 'Countries']

    def test_country_data(self):
        regions = models.Region.objects.all()
        self.assertEqual(regions.count(), 5)
        countries = models.Country.objects.all()
        self.assertEqual(countries.count(), 258)


class ProfileTest(TestCase):
    def setUp(self):
        user = User.objects.create(username='username', first_name='pat', last_name='smith', password='password')
        user.profile.org = 'org'
        user.profile.save()

    def test_profile_create(self):
        profile = models.Profile.objects.get(user__username='username')
        self.assertEqual(profile.org, 'org')


class AppealTest(APITestCase):
    def setUp(self):
        # An appeal with needs_confirmation=True should not return the event in the API response.
        event = models.Event.objects.create(name='associated event', summary='foo')
        country = models.Country.objects.create(name='country')
        models.Appeal.objects.create(aid='test1', name='appeal', atype=1, code='abc', needs_confirmation=True, event=event, country=country)

    def test_unconfirmed_event(self):
        response = self.client.get('/api/v2/appeal/?code=abc')
        response = dict(dict(response.data)['results'][0])
        self.assertIsNone(response['event'])
        self.assertIsNotNone(response['country'])


class FieldReportTest(TestCase):

    fixtures = ['DisasterTypes']

    def setUp(self):
        dtype = models.DisasterType.objects.get(pk=1)
        event = models.Event.objects.create(name='disaster1', summary='test disaster', dtype=dtype)
        country = models.Country.objects.create(name='country')
        report = models.FieldReport.objects.create(rid='test1', event=event, dtype=dtype)
        report.countries.add(country)

    def test_field_report_create(self):
        event = models.Event.objects.get(name='disaster1')
        country = models.Country.objects.get(name='country')
        self.assertEqual(event.field_reports.all()[0].countries.all()[0], country)
        obj = models.FieldReport.objects.get(rid='test1')
        self.assertEqual(obj.rid, 'test1')
        self.assertEqual(obj.countries.all()[0], country)
        self.assertEqual(obj.event, event)
        self.assertIsNotNone(obj.report_date)


class ProfileTestDepartment(TestCase):
    def setUp(self):
        user = User.objects.create(username='test1', password='12345678!')
        user.profile.department = 'testdepartment'
        user.save()

    def test_profile_create(self):
        obj = models.Profile.objects.get(user__username='test1')
        self.assertEqual(obj.department, 'testdepartment')
