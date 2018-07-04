import json
from django.test import TestCase
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
import api.models as models
import api.drf_views as views


from api.views import (
    GetAuthToken,
)

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
