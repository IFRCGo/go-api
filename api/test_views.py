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

    def setUp(self):
        type1 = models.DocumentType.objects.create(type='Lyric')
        type2 = models.DocumentType.objects.create(type='Epic')
        dtype1 = models.DisasterType.objects.get(pk=1)
        #dtype2 = models.DisasterType.objects.get(pk=2)
        #dtype3 = models.DisasterType.objects.get(pk=4)
        event1 = models.Event.objects.create(name='disaster1', summary='test disaster1', dtype=dtype1)
        #event2 = models.Event.objects.create(name='disaster2', summary='test disaster2', dtype=dtype2)
        #event3 = models.Event.objects.create(name='disaster3', summary='test disaster3', dtype=dtype3)
        report1 = models.SituationReport.objects.create(name='test1', event=event1, type=type1)
        report2 = models.SituationReport.objects.create(name='test2', event=event1, type=type2)
        report3 = models.SituationReport.objects.create(name='test3', event=event1, type=type2)

    def test_sit_rep_types(self):
        type1 = models.DocumentType.objects.get(type='Lyric')
        type2 = models.DocumentType.objects.get(type='Epic')
        event1 = models.Event.objects.get(name='disaster1')
        report1 = models.SituationReport.objects.get(name='test1')
        report2 = models.SituationReport.objects.get(name='test2')
        report3 = models.SituationReport.objects.get(name='test3')
        self.assertIsNotNone(report1)
        self.assertIsNotNone(report2)
        self.assertIsNotNone(report3)
        response = self.client.get('/api/v2/situation_report/?limit=100&event=' + str(event1.id))
        #r..content: {"count":3,"next":null,"previous":null,"results":[{"created_at":"...","name":"test3","document":null,"document_url":"","event":540,"id":185,"type":237 ...  ...
        self.assertEqual(response.status_code, 200)
        cnt = json.loads(response.content)['count']
        self.assertEqual(cnt, 3)
        response = self.client.get('/api/v2/situation_report/?limit=100&event=' + str(event1.id) + '&type=' + str(type2.id))
        #r..content: {"count":2,"next":null,"previous":null,"results":[{"created_at":"...","name":"test3","document":null,"document_url":"","event":540,"id":185   ...
        self.assertEqual(response.status_code, 200)
        cnt = json.loads(response.content)['count']
        self.assertEqual(cnt, 2)
