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
            'unique_id': '1aad9295-ceb9-4ad5-9b10-84cc423e93f4',
            'started_at': '2019-04-11 11:42:22.278796+00',
            'submitted_at': '2019-04-11 09:42:52.278796+00',
            'data': [{'id': '1.1', 'op': 3, 'nt': 'notes here'}, {'id': '1.2', 'op': 0, 'nt': 'notes here also'}]
        }
        headers = {'CONTENT_TYPE': 'application/json'}
        resp = self.client.post('/sendperform', body, format='json', headers=headers)
        self.assertEqual(resp.status_code, 200)
