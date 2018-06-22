import json
from django.test import TestCase
from rest_framework.test import APITestCase
from django.contrib.auth.models import User

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
