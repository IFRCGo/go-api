import json
from django.test import TestCase
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
import api.models as models
import api.drf_views as views


class AuthTokenTest(APITestCase):
    def setUp(self):
        user = User.objects.create(username='jo')
        user.set_password('12345678')
        user.save()

    def test_get_auth(self):
        body = {
            'username': 'jo',
            'password': '12345678',
        }
        headers = {'CONTENT_TYPE': 'application/json'}
        response = self.client.post('/get_auth_token', body, format='json', headers=headers).content
        response = json.loads(response)
        self.assertIsNotNone(response.get('token'))
        self.assertIsNotNone(response.get('expires'))


class SituationReportTypeTest(APITestCase):

    fixtures = ['DisasterTypes']

    def test_sit_rep_types(self):
        type1 = models.SituationReportType.objects.create(type='Lyric')
        type2 = models.SituationReportType.objects.create(type='Epic')
        dtype1 = models.DisasterType.objects.get(pk=1)
        event1 = models.Event.objects.create(name='disaster1', summary='test disaster1', dtype=dtype1)
        report1 = models.SituationReport.objects.create(name='test1', event=event1, type=type1)
        report2 = models.SituationReport.objects.create(name='test2', event=event1, type=type2)
        report3 = models.SituationReport.objects.create(name='test3', event=event1, type=type2)

        # Filter by event
        response = self.client.get('/api/v2/situation_report/?limit=100&event=%s' % event1.id)
        self.assertEqual(response.status_code, 200)
        count = json.loads(response.content)['count']
        self.assertEqual(count, 3)

        # Filter by event and type
        response = self.client.get('/api/v2/situation_report/?limit=100&event=%s&type=%s' % (event1.id, type2.id))
        self.assertEqual(response.status_code, 200)
        count = json.loads(response.content)['count']
        self.assertEqual(count, 2)


class FieldReportTest(APITestCase):

    fixtures = ['DisasterTypes', 'Actions']

    def test_create_and_update(self):
        user = User.objects.create(username='jo')
        region = models.Region.objects.create(name=1)
        country1 = models.Country.objects.create(name='abc', region=region)
        country2 = models.Country.objects.create(name='xyz')
        body = {
            'countries': [country1.id, country2.id],
            'dtype': 7,
            'summary': 'test',
            'bulletin': '3',
            'num_assisted': 100,
            'visibility': 1,
            'sources': [
                {'stype': 'Government', 'spec': 'A source'},
                {'stype': 'Other', 'spec': 'Another source'},
            ],
            'actions_taken': [
                {'organization': 'NTLS', 'summary': 'actions taken', 'actions': ['37', '30', '39']},
            ],
            'dref': '2',
            'appeal': '1',
            'contacts': [
                {'ctype': 'Originator', 'name': 'jo', 'title': 'head', 'email': '123'}
            ],
            'user': user.id,
        }
        self.client.force_authenticate(user=user)
        response = self.client.post('/api/v2/create_field_report/', body, format='json')
        response = json.loads(response.content)
        created = models.FieldReport.objects.get(pk=response['id'])

        self.assertEqual(created.countries.count(), 2)
        # one region attached automatically
        self.assertEqual(created.regions.count(), 1)

        self.assertEqual(created.sources.count(), 2)
        source_types = list([source.stype.name for source in created.sources.all()])
        self.assertTrue('Government' in source_types)
        self.assertTrue('Other' in source_types)

        self.assertEqual(created.actions_taken.count(), 1)
        actions = list([action.id for action in created.actions_taken.first().actions.all()])
        self.assertTrue(37 in actions)
        self.assertTrue(30 in actions)
        self.assertTrue(39 in actions)

        self.assertEqual(created.contacts.count(), 1)
        self.assertEqual(created.visibility, 1)
        self.assertEqual(created.dtype.id, 7)
        self.assertEqual(created.summary, 'test')

        # created an emergency automatically
        self.assertEqual(created.event.name, 'test')
        event_pk = created.event.id

        body['countries'] = [country2.id]
        body['sources'] = [
            {'stype': 'Vanilla', 'spec': 'something'},
            {'stype': 'Chocolate', 'spec': 'other'},
        ]
        body['actions_taken'] = []
        body['visibility'] = 2
        response = self.client.put('/api/v2/update_field_report/%s/' % created.id, body, format='json')
        response = json.loads(response.content)
        updated = models.FieldReport.objects.get(pk=response['id'])

        self.assertEqual(updated.countries.count(), 1)
        self.assertEqual(updated.countries.first().name, 'xyz')
        # region automatically removed
        self.assertEqual(updated.regions.count(), 0)

        self.assertEqual(updated.sources.count(), 2)
        source_types = list([source.stype.name for source in updated.sources.all()])
        self.assertTrue('Vanilla' in source_types)
        self.assertTrue('Chocolate' in source_types)

        self.assertEqual(updated.actions_taken.count(), 0)
        self.assertEqual(updated.contacts.count(), 1)
        self.assertEqual(updated.visibility, 2)
        # emergency still attached
        self.assertEqual(updated.event.id, event_pk)
