from django.conf import settings
from modeltranslation.utils import build_localized_fieldname

from main.test_case import APITestCase
from api.models import Country
from .models import Language, Form


# TODO: Add test for Draft, Form and FormData API
class PerTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.country = Country.objects.create(name='Country 1')

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

    def test_sendperform(self):
        body = {
            'code': 'A1',
            'name': 'Form Name',
            'language': Language.ENGLISH,
            'user_id': self.user.pk,
            'country_id': self.country.pk,
            'comment': 'test comment',
        }
        resp = self.client.post('/sendperform', body, format='json')
        self.assert_200(resp)

    def test_editperform(self):
        body = {
            'code': 'A1',
            'name': 'Form Name',
            'language': Language.ENGLISH,
            'user_id': self.user.pk,
            'country_id': self.country.pk,
            'comment': 'test comment',
        }
        form = Form.objects.create(**body)
        body['id'] = form.pk
        body['comment'] += ' [updated]'

        self.authenticate(self.user)
        resp = self.client.post('/editperform', body, format='json')
        self.assert_200(resp)
