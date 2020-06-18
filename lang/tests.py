from django.conf import settings
from main.test_case import APITestCase

from .models import String


class ProjectGetTest(APITestCase):

    def setUp(self):
        super().setUp()

    def test_list_languages(self, **kwargs):
        self.authenticate(self.user)
        resp = self.client.get('/api/v2/language/')
        j_resp = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(j_resp['results']), len(settings.LANGUAGES))
        self.assertEqual(j_resp['count'], len(settings.LANGUAGES))

    def test_list_strings(self, **kwargs):
        language = settings.LANGUAGES[0]
        self.authenticate(self.user)
        resp = self.client.get('/api/v2/language/en/')
        j_resp = resp.json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(j_resp['strings']), len(settings.LANGUAGES))
        self.assertEqual(j_resp['count'], len(settings.LANGUAGES))
