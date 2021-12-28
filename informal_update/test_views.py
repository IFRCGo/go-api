from django.contrib.auth.models import User

from main.test_case import APITestCase
import api.models as models
from informal_update.models import InformalUpdate

from factories.informal_refrences import ReferenceUrlsFactory
from factories.informal_graphic_map import InformalGraphicMapFactory
from factories.informal_update import InformalUpdateFactory


class InformalUpdateTest(APITestCase):

    def test_create_and_update(self):
        user = User.objects.create(username='jo')
        country1 = models.Country.objects.create(name='abc')
        country2 = models.Country.objects.create(name='xyz')
        district1 = models.District.objects.create(name='test district1', country=country1)
        district2 = models.District.objects.create(name='test district12', country=country2)
        refrence_urls = ReferenceUrlsFactory.create_batch(3)
        informal_map = InformalGraphicMapFactory()
        informal_graphics = InformalGraphicMapFactory()
        hazard_type = models.DisasterType.objects.create(name="test earthquake")
        hazard_type_updated = models.DisasterType.objects.create(name="test flood")
        body = {
            "country_district": [
                {
                    'country': str(country1.id),
                    'district': str(district1.id)
                },
                {
                    'country': str(country2.id),
                    'district': str(district2.id)
                }
            ],
            "references": [
                {
                    'date': '2021-02-02 00:00:00',
                    'source_description': 'A source',
                    'url': [
                        {"url": str(refrence_urls[0].url)},
                        {"url": str(refrence_urls[1].url)}
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
            "created_by": str(user.id),
            "hazard_type": str(hazard_type.id),
            "map": str(informal_map.id),
            "graphics": str(informal_graphics.id)
        }

        self.client.force_authenticate(user=user)
        with self.capture_on_commit_callbacks(execute=True):
            response = self.client.post('/api/v2/informal-update/', body, format='json').json()
        created = InformalUpdate.objects.get(pk=response['id'])
        self.assertEqual(created.created_by.id, user.id)
        self.assertEqual(created.hazard_type, hazard_type)
        self.assertEqual(created.map, informal_map)
        self.assertEqual(response['references'][0]['url'][0]['url'], refrence_urls[0].url)
        self.assertEqual(response['country_district'][0]['country'], country1.id)
        self.assertEqual(created.share_with, InformalUpdate.InformalShareWith.IFRC_SECRETARIAT)
        self.assertEqual(created.actions_taken_informal.count(), 1)

        # update
        body['country_district'] = [
            {
                'country': str(country1.id),
                'district': str(district1.id)
            }
        ]
        body['references'] = [
            {
                'date': '2021-01-01 00:00:00',
                'source_description': 'A source',
                'url': [
                    {"url": str(refrence_urls[0].url)},
                ]
            }
        ]
        body['actions_taken'] = [
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
        body['hazard_type'] = str(hazard_type_updated.id)
        body['share_with'] = InformalUpdate.InformalShareWith.RCRC_NETWORK

        response = self.client.put(f'/api/v2/informal-update/{created.id}/', body, format='json').json()
        updated = InformalUpdate.objects.get(pk=response['id'])
        self.assertEqual(updated.modified_by, user)
        self.assertEqual(updated.share_with, InformalUpdate.InformalShareWith.RCRC_NETWORK)
        self.assertEqual(updated.hazard_type, hazard_type_updated)
        self.assertEqual(updated.actions_taken_informal.count(), 2)

        #  patch check
        body['share_with'] = InformalUpdate.InformalShareWith.RCRC_NETWORK_AND_DONORS
        response = self.client.patch(f'/api/v2/informal-update/{created.id}/', body, format='json').json()
        updated = InformalUpdate.objects.get(pk=response['id'])
        self.assertEqual(updated.modified_by, user)
        self.assertEqual(updated.share_with, InformalUpdate.InformalShareWith.RCRC_NETWORK_AND_DONORS)
        self.assertEqual(updated.hazard_type, hazard_type_updated)
        self.assertEqual(updated.actions_taken_informal.count(), 2)

    def test_query(self):
        user1 = User.objects.create(username='abc')
        informal_update1, informal_update2, informal_update3 = InformalUpdateFactory.create_batch(3, created_by=user1)
        self.client.force_authenticate(user=user1)
        response1 = self.client.get('/api/v2/informal-update/').json()
        self.assertEqual(response1['count'], 3)
        self.assertEqual(response1['results'][0]['created_by'], user1.id)
        self.assertIn(informal_update1.id, [data['id'] for data in response1['results']])

        #  try with another user
        user2 = User.objects.create(username='xyz')
        self.client.force_authenticate(user=user2)
        informal_update1, informal_update2 = InformalUpdateFactory.create_batch(2, created_by=user2)
        response2 = self.client.get('/api/v2/informal-update/').json()
        self.assertEqual(response2['count'], 2)
        self.assertEqual(response2['results'][0]['created_by'], user2.id)
        self.assertIn(informal_update1.id, [data['id'] for data in response2['results']])
        self.assertNotIn([data['id'] for data in response2['results']], [data['id'] for data in response1['results']])

        #  query single informal update
        response = self.client.get(f'/api/v2/informal-update/{informal_update1.id}/').json()
        self.assertEqual(response['created_by'], user1.id)
        self.assertEqual(response['id'], informal_update1.id)

    def test_filter(self):
        user = User.objects.create(username='xyz')
        self.client.force_authenticate(user=user)
        hazard_type1 = models.DisasterType.objects.create(name="disaster_type1")
        InformalUpdateFactory(hazard_type=hazard_type1, created_by=user)
        response1 = self.client.get(f'/api/v2/informal-update/?hazard_type={hazard_type1.id}').json()

        hazard_type2 = models.DisasterType.objects.create(name="disaster_type2")
        InformalUpdateFactory(hazard_type=hazard_type2, created_by=user)
        response2 = self.client.get(f'/api/v2/informal-update/?hazard_type={hazard_type2.id}').json()

        self.assertNotIn([data['id'] for data in response2['results']], [data['id'] for data in response1['results']])






