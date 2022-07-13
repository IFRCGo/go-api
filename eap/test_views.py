import os

from django.conf import settings
from django.contrib.auth.models import User

from main.test_case import APITestCase
from eap.models import EAP

from api.factories.country import CountryFactory
from api.factories.district import DistrictFactory
from api.factories.disaster_type import DisasterTypeFactory
from deployments.factories.user import UserFactory

from .factories import EAPDocumentFactory, EAPFactory


class EAPTest(APITestCase):

    def setUp(self):
        self.user = UserFactory.create(username='jo')
        self.country1 = CountryFactory.create(name='abc')
        self.country2 = CountryFactory.create(name='xyz')
        self.district1 = DistrictFactory.create(name='test district1', country=self.country1)
        self.district2 = DistrictFactory.create(name='test district2', country=self.country2)
        self.document1 = EAPDocumentFactory.create(created_by=self.user)
        self.disaster_type = DisasterTypeFactory.create(name="test earthquake")
        self.disaster_type_updated = DisasterTypeFactory.create(name="test flood")

        path = os.path.join(settings.TEST_DIR, 'documents')
        self.file = os.path.join(path, 'go.png')

        self.body = {
            "references": [
                {
                    "source": "test",
                    "url": "https://jsonformatter.org/"
                },
                {
                    "source": "test 2",
                    "url": "https://jsonformatter.org/"
                }
            ],
            "partners": [
                {
                    "name": "test name",
                    "url": "https://jsonformatter2.org/"
                },
                {
                    "name": "test name 2",
                    "url": "https://jsonformatter2.org/"
                }
            ],
            "eap_number": "1",
            "approval_date": "2022-11-11",
            "status": "approved",
            "operational_timeframe": 5,
            "lead_time": 5,
            "eap_timeframe": 5,
            "num_of_people": 1000,
            "total_budget": 10000,
            "readiness_budget": 5000,
            "pre_positioning_budget": 3000,
            "early_action_budget": 2000,
            "trigger_statement": "test",
            "overview": "test",
            "document": self.document1.id,
            "originator_name": "eap name",
            "originator_title": "eap title",
            "originator_email": "eap@gmail.com",
            "originator_phone": "1245145241",
            "nsc_name": "eap ns name",
            "nsc_title": "eap ns title",
            "nsc_email": "eap_ns@gmail.com",
            "nsc_phone": "8547458745",
            "ifrc_focal_name": "ifrc name",
            "ifrc_focal_title": "ifrc title",
            "ifrc_focal_email": "eap_ifrc@gmail.com",
            "ifrc_focal_phone": "5685471584",
            "country": self.country1.id,
            "district": self.district1.id,
            "disaster_type": self.disaster_type.id,
            "early_actions": [
                {
                    "sector": "Health",
                    "budget_per_sector": 1000,
                    "prioritized_risk": "test",
                    "targeted_people": 100,
                    "readiness_activities": "test",
                    "prepositioning_activities": "test",
                    "indicators": [
                        {
                            "indicator": "indicator_1",
                            "indicator_value": 1
                        },
                        {
                            "indicator": "indicator_2",
                            "indicator_value": 2
                        }
                    ],
                    "actions": [
                        {
                            "early_act": "test"
                        },
                        {
                            "early_act": "test 2"
                        }
                    ]

                },
                {
                    "sector": "Health",
                    "budget_per_sector": 1000,
                    "prioritized_risk": "prioritized_risk",
                    "targeted_people": 200,
                    "readiness_activities": "test",
                    "prepositioning_activities": "test",
                    "indicators": [
                        {
                            "indicator": "indicator_1",
                            "indicator_value": 1
                        },
                        {
                            "indicator": "indicator_2",
                            "indicator_value": 2
                        }
                    ],
                    "actions": [
                        {
                            "early_act": " early_acttest"
                        },
                        {
                            "early_act": "early_act test 2"
                        }
                    ]

                }
            ]
        }
        super().setUp()

    def test_create_and_update_eap(self):
        self.client.force_authenticate(user=self.user)
        # create eap
        with self.capture_on_commit_callbacks(execute=True):
            response = self.client.post('/api/v2/eap/', self.body, format='json').json()
        created = EAP.objects.get(id=response['id'])
        self.assertEqual(created.created_by.id, self.user.id)
        self.assertEqual(created.country.id, self.country1.id)
        self.assertEqual(created.district.id, self.district1.id)
        self.assertEqual(created.disaster_type, self.disaster_type)
        self.assertEqual(created.document.id, self.document1.id)
        self.assertEqual(response['country'], self.country1.id)
        self.assertEqual(created.status, EAP.Status.APPROVED)
        self.assertEqual(created.early_actions.count(), 2)
        self.assertEqual(len(response['references']), 2)
        self.assertEqual(len(response['partners']), 2)

        # update eap
        data = self.body
        data['country'] = self.country2.id
        data['district'] = self.district2.id
        data['references'] = [
            {
                "source": "test updated",
                "url": "https://jsonformatter.org/"
            }
        ]
        data['partners'] = [
            {
                "name": "test name updated",
                "url": "https://jsonformatter2.org/"
            }
        ]

        data['disaster_type'] = str(self.disaster_type_updated.id)
        data['status'] = EAP.Status.ACTIVATED
        data['reference'] = self.document1.id

        response = self.client.put(f'/api/v2/eap/{created.id}/', data, format='json').json()
        updated = EAP.objects.get(id=response['id'])
        self.assertEqual(updated.id, created.id)
        self.assertEqual(updated.modified_by, self.user)
        self.assertEqual(updated.status, EAP.Status.ACTIVATED)
        self.assertEqual(updated.disaster_type, self.disaster_type_updated)
        self.assertEqual(updated.early_actions.count(), 2)
        self.assertEqual(len(response['references']), 1)
        self.assertEqual(len(response['partners']), 1)

    def test_get_eap(self):
        user1 = UserFactory.create(username='abc')
        eap1, eap2, eap3 = EAPFactory.create_batch(3, created_by=user1)
        self.client.force_authenticate(user=user1)
        response1 = self.client.get('/api/v2/eap/').json()
        self.assertEqual(response1['count'], 3)
        self.assertEqual(response1['results'][0]['created_by'], user1.id)
        self.assertEqual(
            sorted([eap1.id, eap2.id, eap3.id]),
            sorted([data['id'] for data in response1['results']])
        )

        #  query single eap
        response = self.client.get(f'/api/v2/eap/{eap1.id}/').json()
        self.assertEqual(response['created_by'], user1.id)
        self.assertEqual(response['id'], eap1.id)

        #  try with another user
        user2 = User.objects.create(username='xyz')
        self.client.force_authenticate(user=user2)
        eap4, eap5 = EAPFactory.create_batch(2, created_by=user2)
        response2 = self.client.get('/api/v2/eap/').json()
        self.assertEqual(response2['count'], 5)
        self.assertEqual(response2['results'][0]['created_by'], user2.id)
        self.assertIn(eap4.id, [data['id'] for data in response2['results']])
        self.assertNotIn([data['id'] for data in response2['results']], [data['id'] for data in response1['results']])

        # try with users who has no any eap created
        user3 = User.objects.create(username='ram')
        self.client.force_authenticate(user=user3)
        response3 = self.client.get('/api/v2/eap/').json()
        self.assertEqual(response3['count'], 5)
