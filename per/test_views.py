from django.test import TestCase
from rest_framework.test import APITestCase
from django.core.exceptions import ObjectDoesNotExist

class SmokeTest(APITestCase):
    def setUp(self):
        a111=1
        
    def test_simple_form(self):
        body = {
            'code': 'A1',
            'name': 'Nemo',
            'language': 1,
        }
        headers = {'CONTENT_TYPE': 'application/json'}
        resp = self.client.post('/sendperform', body, format='json', headers=headers)
        self.assertEqual(resp.status_code, 200)
