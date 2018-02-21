from django.test import TestCase
from django.contrib.auth.models import User

import api.models as models


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
        keyfig = obj2.keyfigure_set.all()
        self.assertEqual(keyfig[0].deck, 'things')
        self.assertEqual(keyfig[0].number, 7)
        snippet = obj2.snippet_set.all()
        self.assertEqual(snippet[0].snippet, 'this is a snippet')


class CountryTest(TestCase):

    fixtures = ['Regions', 'Countries']

    def test_country_data(self):
        regions = models.Region.objects.all()
        self.assertEqual(regions.count(), 5)
        countries = models.Country.objects.all()
        self.assertEqual(countries.count(), 260)


class ProfileTest(TestCase):
    def setUp(self):
        user = User.objects.create(username='username', first_name='pat', last_name='smith', password='password')
        user.profile.org = 'org'
        user.profile.save()

    def test_profile_create(self):
        profile = models.Profile.objects.get(user__username='username')
        self.assertEqual(profile.org, 'org')


"""
class AppealTest(TestCase):
    def setUp(self):
        event = models.Event.objects.create(name='disaster1', summary='test disaster')
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
"""

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


class ProfileTest(TestCase):
    def setUp(self):
        user = User.objects.create(username='test1', password='12345678!')
        user.profile.department = 'testdepartment'
        user.save()

    def test_profile_create(self):
        obj = models.Profile.objects.get(user__username='test1')
        self.assertEqual(obj.department, 'testdepartment')
