from main.test_case import APITestCase
from dref.models import Dref
from django.contrib.auth.models import User

from dref.factories.dref import DrefFactory

from api.models import Country, DisasterType


class DrefTestCase(APITestCase):

    def test_get_dref(self):
        DrefFactory.create_batch(5)
        url = '/api/v2/dref/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 5)

    def test_post_dref_creation(self):
        old_count = Dref.objects.count()
        national_society = Country.objects.create(name='xzz')
        disaster_type = DisasterType.objects.create(name='abc')
        data = {
            "title": "Dref test title",
            "type_of_onset": Dref.OnsetType.ANTICIPATORY.value,
            "disaster_category_level": Dref.DisasterCategory.YELLOW.value,
            "status": Dref.Status.IN_PROGESS.value,
            "num_assisted": 5666,
            "num_affected": 23,
            "amount_requested": 127771111,
            "emergency_appeal_planned": False,
            "disaster_date": "2021-08-01",
            "ns_respond_date": "2021-08-01",
            "ns_respond_text": "Test text for respond",
            "ns_request": False,
            "lessons_learned": "Test text for lessons learned",
            "event_description": "Test text for event description",
            "anticipatory_actions": "Test text for anticipatory actions",
            "event_scope": "Test text for event scope",
            "government_requested_assistance": False,
            "government_requested_assistance_date": "2021-08-01",
            "national_authorities": "Test text for national authorities",
            "rcrc_partners": "",
            "icrc": "",
            "un_or_other": "",
            "major_coordination_mechanism": "",
            "identified_gaps": "",
            "people_assisted": "",
            "selection_criteria": "",
            "entity_affected": "",
            "community_involved": "",
            "women": 344444,
            "men": 5666,
            "girls": 22,
            "boys": 344,
            "disability_people_per": "12.4",
            "people_per": "10.3",
            "displaced_people": 234243,
            "operation_objective": "",
            "response_strategy": "",
            "secretariat_service": "",
            "national_society_strengthening": "",
            "ns_request_date": "2021-07-01",
            "submission_to_geneva": "2021-07-01",
            "date_of_approval": "2021-07-01",
            "start_date": "2021-07-01",
            "end_date": "2021-07-01",
            "publishing_date": "2021-08-01",
            "operation_timeframe": 4,
            "appeal_code": "J7876",
            "glide_code": "ER878",
            "appeal_manager_name": "Test Name",
            "appeal_manager_email": "test@gmail.com",
            "project_manager_name": "Test Name",
            "project_manager_email": "test@gmail.com",
            "national_society_contact_name": "Test Name",
            "national_society_contact_email": "test@gmail.com",
            "media_contact_name": "Test Name",
            "media_contact_email": "test@gmail.com",
            "ifrc_emergency_name": "Test Name",
            "ifrc_emergency_email": "test@gmail.com",
            "national_society": national_society.id,
            "disaster_type": disaster_type.id,
        }
        url = '/api/v2/dref/'
        user = User.objects.create(username='foo')
        self.client.force_authenticate(user=user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Dref.objects.count(), old_count + 1)

    def test_filter_dref_status(self):
        """
        Test to filter dref status
        """
        DrefFactory.create(title='test', status=Dref.Status.COMPLETED, date_of_approval='2020-10-10')
        DrefFactory.create(status=Dref.Status.COMPLETED, date_of_approval='2020-10-10')
        DrefFactory.create(status=Dref.Status.COMPLETED, date_of_approval='2020-10-10')
        DrefFactory.create(status=Dref.Status.IN_PROGESS)
        DrefFactory.create(status=Dref.Status.IN_PROGESS)

        # filter by `In Progress`
        url = f'/api/v2/dref/?status={Dref.Status.IN_PROGESS.value}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['status'], 0)
        self.assertEqual(response.data['count'], 2)

    def test_create_planned_interventions(self):
        data = {
            'title': 'Test title',
            'description': 'Test for description',
            'budget': 200100100
        }
        url = '/api/v2/planned/'
        user = User.objects.create(username='foo')
        self.client.force_authenticate(user=user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)

    def test_create_national_society_action(self):
        data = {
            'title': 'Test title',
            'description': 'Test for description',
        }
        url = '/api/v2/national-society-action/'
        user = User.objects.create(username='foo')
        self.client.force_authenticate(user=user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)

    def test_create_identified_need(self):
        data = {
            'title': 'Test title',
            'description': 'Test for description',
        }
        url = '/api/v2/identified-need/'
        user = User.objects.create(username='foo')
        self.client.force_authenticate(user=user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
