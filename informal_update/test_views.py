import os

from django.conf import settings
from django.contrib.auth.models import User

from main.test_case import APITestCase
import api.models as models
from informal_update.models import InformalUpdate
from informal_update.factories.informal_update import (
    InformalUpdateFactory,
    ReferenceUrlsFactory,
    InformalGraphicMapFactory
)


class InformalUpdateTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create(username='jo')
        self.country1 = models.Country.objects.create(name='abc')
        self.country2 = models.Country.objects.create(name='xyz')
        self.district1 = models.District.objects.create(name='test district1', country=self.country1)
        self.district2 = models.District.objects.create(name='test district12', country=self.country2)
        self.refrence_urls = ReferenceUrlsFactory.create_batch(3)
        self.informal_map = InformalGraphicMapFactory()
        self.informal_graphics = InformalGraphicMapFactory()
        self.hazard_type = models.DisasterType.objects.create(name="test earthquake")
        self.hazard_type_updated = models.DisasterType.objects.create(name="test flood")

        path = os.path.join(settings.TEST_DIR, 'informal_files')
        self.file = os.path.join(path, 'ifrc.png')

        self.body = {
            "country_district": [
                {
                    'country': str(self.country1.id),
                    'district': str(self.district1.id)
                },
                {
                    'country': str(self.country2.id),
                    'district': str(self.district2.id)
                },
            ],
            "references": [
                {
                    'date': '2021-02-02 00:00:00',
                    'source_description': 'A source',
                    'url': [
                        {"url": str(self.refrence_urls[0].url)},
                        {"url": str(self.refrence_urls[1].url)}
                    ]
                }
            ],
            'actions_taken': [
                {
                    'organization': 'NTLS',
                    'summary': 'actions taken',
                    'actions': [
                        {"id": '37', "name": "First Aid"},
                        {"id": '30', "name": "Relief/Supply distribution"}
                    ]
                },
            ],
            "title": "test",
            "situational_overview": "test situational overview",
            "originator_name": "test originator_name",
            "originator_title": "test originator_title",
            "originator_email": " test originator_email",
            "originator_phone": "9856858585",
            "ifrc_name": " test ifrc_name",
            "ifrc_title": "test ",
            "ifrc_email": "test_ifrc@ifrc.com",
            "ifrc_phone": "9858585858",
            "share_with": InformalUpdate.InformalShareWith.IFRC_SECRETARIAT,
            "created_by": str(self.user.id),
            "hazard_type": str(self.hazard_type.id),
            "map": str(self.informal_map.id),
            "graphics": str(self.informal_graphics.id)
        }
        super().setUp()

    def test_create_and_update(self):
        self.client.force_authenticate(user=self.user)
        with self.capture_on_commit_callbacks(execute=True):
            response = self.client.post('/api/v2/informal-update/', self.body, format='json').json()
        created = InformalUpdate.objects.get(pk=response['id'])
        self.assertEqual(created.created_by.id, self.user.id)
        self.assertEqual(created.hazard_type, self.hazard_type)
        self.assertEqual(created.map, self.informal_map)
        self.assertEqual(response['references'][0]['url'][0]['url'], self.refrence_urls[0].url)
        self.assertEqual(response['country_district'][0]['country'], self.country1.id)
        self.assertEqual(created.share_with, InformalUpdate.InformalShareWith.IFRC_SECRETARIAT)
        self.assertEqual(created.actions_taken_informal.count(), 1)

        # update
        data = self.body
        data['country_district'] = [
            {
                'country': str(self.country1.id),
                'district': str(self.district1.id)
            }
        ]
        data['references'] = [
            {
                'date': '2021-01-01 00:00:00',
                'source_description': 'A source',
                'url': [
                    {"url": str(self.refrence_urls[0].url)},
                    {"url": str(self.refrence_urls[2].url)}
                ]
            }
        ]
        data['actions_taken'] = [
            {
                'organization': 'NTLS',
                'summary': 'actions taken updated',
                'actions': [
                    {"id": '37', "name": "First Aid"},
                ]
            },
            {
                'organization': 'FDRN',
                'summary': 'actions taken updated',
                'actions': [
                    {"id": '30', "name": "Relief/Supply distribution"}
                ]
            }
        ]

        data['hazard_type'] = str(self.hazard_type_updated.id)
        data['share_with'] = InformalUpdate.InformalShareWith.RCRC_NETWORK

        response = self.client.put(f'/api/v2/informal-update/{created.id}/', data, format='json').json()
        updated = InformalUpdate.objects.get(pk=response['id'])
        self.assertEqual(updated.id, created.id)
        self.assertEqual(updated.modified_by, self.user)
        self.assertEqual(updated.share_with, InformalUpdate.InformalShareWith.RCRC_NETWORK)
        self.assertEqual(updated.hazard_type, self.hazard_type_updated)
        self.assertNotEqual(response['hazard_type'], created.hazard_type)
        self.assertEqual(updated.actions_taken_informal.count(), 2)

    def test_patch(self):
        user = User.objects.create(username='test_abc')
        self.client.force_authenticate(user=user)
        with self.capture_on_commit_callbacks(execute=True):
            response1 = self.client.post('/api/v2/informal-update/', self.body, format='json').json()
        created = InformalUpdate.objects.get(pk=response1['id'])
        data = {'title': 'test title patched'}
        response2 = self.client.patch(f'/api/v2/informal-update/{created.id}/', data=data, format='json').json()
        informal_id = InformalUpdate.objects.get(pk=response2['id'])
        self.assertEqual(informal_id.modified_by, user)
        self.assertNotEqual(response1['title'], response2['title'])
        self.assertEqual(response1['id'], response2['id'])
        self.assertEqual(informal_id.share_with, InformalUpdate.InformalShareWith.IFRC_SECRETARIAT)

    def test_get_informal_update(self):
        user1 = User.objects.create(username='abc')
        informal_update1, informal_update2, informal_update3 = InformalUpdateFactory.create_batch(3, created_by=user1)
        self.client.force_authenticate(user=user1)
        response1 = self.client.get('/api/v2/informal-update/').json()
        self.assertEqual(response1['count'], 3)
        self.assertEqual(response1['results'][0]['created_by'], user1.id)
        self.assertEqual(
            sorted([informal_update1.id, informal_update2.id, informal_update3.id]),
            sorted([data['id'] for data in response1['results']])
        )

        #  query single informal update
        response = self.client.get(f'/api/v2/informal-update/{informal_update1.id}/').json()
        self.assertEqual(response['created_by'], user1.id)
        self.assertEqual(response['id'], informal_update1.id)

        #  try with another user
        user2 = User.objects.create(username='xyz')
        self.client.force_authenticate(user=user2)
        informal_update4, informal_update5 = InformalUpdateFactory.create_batch(2, created_by=user2)
        response2 = self.client.get('/api/v2/informal-update/').json()
        self.assertEqual(response2['count'], 2)
        self.assertEqual(response2['results'][0]['created_by'], user2.id)
        self.assertIn(informal_update4.id, [data['id'] for data in response2['results']])
        self.assertNotIn([data['id'] for data in response2['results']], [data['id'] for data in response1['results']])

        # try with users who has no any informal update created
        user3 = User.objects.create(username='ram')
        self.client.force_authenticate(user=user3)
        response3 = self.client.get('/api/v2/informal-update/').json()
        self.assertEqual(response3['count'], 0)

    def test_filter(self):
        user = User.objects.create(username='xyz')
        self.client.force_authenticate(user=user)
        hazard_type1 = models.DisasterType.objects.create(name="disaster_type1")
        hazard_type2 = models.DisasterType.objects.create(name="disaster_type2")
        hazard_type3 = models.DisasterType.objects.create(name="disaster_type3")
        hazard_type4 = models.DisasterType.objects.create(name="disaster_type4")

        InformalUpdateFactory(hazard_type=hazard_type1, created_by=user)
        InformalUpdateFactory.create_batch(3, hazard_type=hazard_type2, created_by=user)
        InformalUpdateFactory.create_batch(2, hazard_type=hazard_type3, created_by=user)
        InformalUpdateFactory(hazard_type=hazard_type4, created_by=user)

        response1 = self.client.get(f'/api/v2/informal-update/?hazard_type={hazard_type1.id}').json()
        response2 = self.client.get(f'/api/v2/informal-update/?hazard_type={hazard_type2.id}').json()
        response3 = self.client.get(f'/api/v2/informal-update/?hazard_type={hazard_type3.id}').json()
        response4 = self.client.get(f'/api/v2/informal-update/?hazard_type={hazard_type4.id}').json()

        self.assertNotIn([data['id'] for data in response2['results']], [data['id'] for data in response1['results']])
        self.assertNotIn([data['id'] for data in response4['results']], [data['id'] for data in response3['results']])
        self.assertNotIn([data['id'] for data in response2['results']], [data['id'] for data in response4['results']])

    def test_validations(self):
        # validate if district passed belongs to respective country
        self.body["country_district"] = [
                {
                    'country': str(self.country1.id),
                    'district': str(self.district2.id)
                }
            ]
        self.client.force_authenticate(user=self.user)
        with self.capture_on_commit_callbacks(execute=True):
            response = self.client.post('/api/v2/informal-update/', self.body, format='json').json()
        self.assert_400(response)

    def test_upload_informal_file(self):
        user = User.objects.create(username='informal_user')
        url = '/api/v2/informal-file/'
        data = {
            'file': open(self.file, 'rb'),
            "caption": "test file"
        }
        self.client.force_authenticate(user=user)
        response = self.client.post(url, data=data, format='multipart')
        self.assert_201(response)
        response = response.json()
        self.assertEqual(response['created_by'], user.id)
