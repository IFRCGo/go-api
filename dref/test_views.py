import os
from datetime import datetime, timedelta
from unittest import mock
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core import management
from rest_framework import status

from api.models import Country, DisasterType, District, Region, RegionName
from api.utils import get_model_name
from deployments.factories.project import SectorFactory
from deployments.factories.user import UserFactory
from dref.factories.dref import (
    DrefFactory,
    DrefFileFactory,
    DrefFinalReportFactory,
    DrefOperationalUpdateFactory,
    ProposedActionActivitiesFactory,
    ProposedActionFactory,
)
from dref.models import (
    Dref,
    DrefFile,
    DrefFinalReport,
    DrefOperationalUpdate,
    ProposedAction,
)
from dref.tasks import send_dref_email
from main.test_case import APITestCase


class DrefTestCase(APITestCase):
    def setUp(self):
        super().setUp()

        path = os.path.join(settings.TEST_DIR, "documents")
        self.file = os.path.join(path, "go.png")

    def test_upload_file(self):
        file_count = DrefFile.objects.count()
        url = "/api/v2/dref-files/"
        data = {
            "file": open(self.file, "rb"),
        }
        self.authenticate()
        response = self.client.post(url, data, format="multipart")
        self.assert_201(response)
        self.assertEqual(DrefFile.objects.count(), file_count + 1)

    def test_upload_multiple_file(self):
        file_count = DrefFile.objects.count()
        url = "/api/v2/dref-files/multiple/"
        data = {"file": [open(self.file, "rb")]}

        self.authenticate()
        response = self.client.post(url, data, format="multipart")
        self.assert_201(response)
        self.assertEqual(DrefFile.objects.count(), file_count + 1)

    def test_upload_invalid_files(self):
        file_count = DrefFile.objects.count()
        url = "/api/v2/dref-files/multiple/"
        data = {"file": [open(self.file, "rb"), open(self.file, "rb"), open(self.file, "rb"), "test_string"]}

        self.authenticate()
        response = self.client.post(url, data, format="multipart")
        self.assert_400(response)
        self.assertEqual(DrefFile.objects.count(), file_count)  # no new files to be created

    def test_dref_file(self):
        file1, file2, file3, file5 = DrefFileFactory.create_batch(4, created_by=self.user)
        file4 = DrefFileFactory.create(created_by=self.ifrc_user)
        url = "/api/v2/dref-files/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(len(response.data["results"]), 4)
        self.assertEqual(set(file["id"] for file in response.data["results"]), set([file1.id, file2.id, file3.id, file5.id]))

        # authenticate with another user
        self.client.force_authenticate(self.ifrc_user)
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(set(file["id"] for file in response.data["results"]), set([file4.id]))

    def test_get_dref(self):
        """
        This test includes  dref to be viewed by user who create is or shared with other user
        """
        # create a dref
        dref_1 = DrefFactory.create(created_by=self.user)
        dref_1.users.add(self.ifrc_user)
        url = "/api/v2/dref/"
        self.client.force_authenticate(self.user)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 1)

        # authenticate with another user and try to view the dref
        self.client.force_authenticate(self.ifrc_user)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 1)

        # try to get the dref by user who neither created nor has access to dref
        user = UserFactory.create()
        self.client.force_authenticate(user)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 0)

    @mock.patch("notifications.notification.send_notification")
    def test_post_dref_creation(self, send_notification):
        old_count = Dref.objects.count()
        national_society = Country.objects.create(name="xzz")
        disaster_type = DisasterType.objects.create(name="abc")
        data = {
            "title": "Dref test title",
            "type_of_onset": Dref.OnsetType.SLOW.value,
            "disaster_category": Dref.DisasterCategory.YELLOW.value,
            "status": Dref.Status.DRAFT.value,
            "num_assisted": 5666,
            "num_affected": 23,
            "amount_requested": 127771111,
            "emergency_appeal_planned": False,
            "event_date": "2021-08-01",
            "ns_respond_date": "2021-08-01",
            "event_text": "Test text for respond",
            "did_ns_request_fund": False,
            "lessons_learned": "Test text for lessons learned",
            "complete_child_safeguarding_risk": True,
            "child_safeguarding_risk_level": "Very high",
            "event_description": "Test text for event description",
            "anticipatory_actions": "Test text for anticipatory actions",
            "event_scope": "Test text for event scope",
            "government_requested_assistance": False,
            "government_requested_assistance_date": "2021-08-01",
            "national_authorities": "Test text for national authorities",
            "icrc": "Test text for lessons learned",
            "un_or_other_actor": "Test text for lessons learned",
            "major_coordination_mechanism": "Test text for lessons learned",
            "identified_gaps": "Test text for lessons learned",
            "people_assisted": "Test text for lessons learned",
            "selection_criteria": "Test text for lessons learned",
            "entity_affected": "Test text for lessons learned",
            "community_involved": "Test text for lessons learned",
            "women": 344444,
            "men": 5666,
            "girls": 22,
            "boys": 344,
            "disability_people_per": "12.45",
            "people_per": "10.35",
            "displaced_people": 234243,
            "operation_objective": "Test script",
            "response_strategy": "Test script",
            "secretariat_service": "Test script",
            "national_society_strengthening": "",
            "ns_request_date": "2021-07-01",
            "submission_to_geneva": "2021-07-01",
            "date_of_approval": "2021-07-01",
            "end_date": "2021-07-05",
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
            "originator_name": "Test Name",
            "originator_email": "test@gmail.com",
            "national_society": national_society.id,
            "disaster_type": disaster_type.id,
            # NOTE: Test Many to Many fields
            "risk_security": [
                {"risk": "Test Risk 1", "mitigation_measure": "Test Mitigation Measure"},
                {"risk": "Test Risk 2", "mitigation_measure": "Test Mitigation Measure 1"},
            ],
            "source_information": [
                {"source_name": "Test Source 1", "link": "http://test.com"},
                {"source_name": "Test Source 2", "link": "http://test.com"},
            ],
            "needs_identified": [
                {"title": "shelter_housing_and_settlements", "description": "Shelter"},
                {"title": "health", "description": "Health"},
            ],
            "national_society_actions": [
                {"title": "coordination", "description": "Coordination"},
                {"title": "shelter_housing_and_settlements", "description": "Shelter"},
            ],
            "planned_interventions": [
                {
                    "title": "shelter_housing_and_settlements",
                    "description": "matrix",
                    "budget": 23444,
                    "male": 12222,
                    "female": 2255,
                    "indicators": [
                        {
                            "title": "test_title_1",
                            "actual": 21232,
                            "target": 44444,
                        },
                        {
                            "title": "test_title_2",
                            "actual": 21232,
                            "target": 44444,
                        },
                    ],
                },
                {
                    "title": "health",
                    "description": "matrix reloaded",
                    "budget": 451111111,
                    "male": 12222,
                    "female": 2255,
                    "indicators": [
                        {
                            "title": "test_title_2",
                            "actual": 21232,
                            "target": 44444,
                        },
                        {
                            "title": "test_title_2",
                            "actual": 21232,
                            "target": 44444,
                        },
                    ],
                },
            ],
            # "users": ,
        }
        url = "/api/v2/dref/"
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Dref.objects.count(), old_count + 1)
        instance = Dref.objects.get(id=response.data["id"])
        instance.users.add(self.user.id)
        instance_user_email = [user.email for user in instance.users.all()]

        # call email send task
        email_data = send_dref_email(instance.id, instance_user_email)
        self.assertTrue(send_notification.assert_called)
        self.assertEqual(email_data["title"], instance.title)

        # Testing Nested objects creation and update
        # Update the created dref
        data = {
            "modified_at": datetime.now(),
            **data,
            "risk_security": [
                {"id": response.data["risk_security"][0]["id"], "risk": "Updated Test Risk 1", "mitigation_measure": "Test"},
                {
                    "id": response.data["risk_security"][1]["id"],
                    "risk": "Updated Test Risk 2",
                    "mitigation_measure": "Test Mitigation Measure 2",
                },
                # New item to be added
                {"risk": "New Test Risk", "mitigation_measure": "New Test Mitigation Measure"},
            ],
            "source_information": [
                {
                    "id": response.data["source_information"][0]["id"],
                    "source_name": "Updated Test Source 1",
                    "link": "http://updated.com",
                },
                {
                    "id": response.data["source_information"][1]["id"],
                    "source_name": "Updated Test Source 2",
                    "link": "http://updated.com",
                },
                # New item to be added
                {"source_name": "New Test Source", "link": "http://new.com"},
            ],
            "needs_identified": [
                {
                    "id": response.data["needs_identified"][0]["id"],
                    "title": "shelter_housing_and_settlements",
                    "description": "Updated Shelter",
                },
                {"id": response.data["needs_identified"][1]["id"], "title": "health", "description": "Updated Health"},
                # New item to be added
                {"title": "water_sanitation_and_hygiene", "description": "WASH"},
            ],
            "national_society_actions": [
                {
                    "id": response.data["national_society_actions"][0]["id"],
                    "title": "coordination",
                    "description": "Updated Coordination",
                },
                {
                    "id": response.data["national_society_actions"][1]["id"],
                    "title": "shelter_housing_and_settlements",
                    "description": "Updated Shelter",
                },
                # New item to be added
                {"title": "health", "description": "Health"},
            ],
            "planned_interventions": [
                {
                    "id": response.data["planned_interventions"][0]["id"],
                    "title": "shelter_housing_and_settlements",
                    "description": "Updated matrix",
                    "budget": 99999,
                    "male": 12222,
                    "female": 2255,
                    "indicators": [
                        {
                            "id": response.data["planned_interventions"][0]["indicators"][0]["id"],
                            "title": "updated_test_title_1",
                            "actual": 11111,
                            "target": 22222,
                        },
                        {
                            "id": response.data["planned_interventions"][0]["indicators"][1]["id"],
                            "title": "updated_test_title_2",
                            "actual": 33333,
                            "target": 44444,
                        },
                        # New item to be added
                        {
                            "title": "new_test_title_3",
                            "actual": 55555,
                            "target": 66666,
                        },
                    ],
                },
                {
                    "id": response.data["planned_interventions"][1]["id"],
                    "title": "health",
                    "description": "Updated matrix reloaded",
                    "budget": 88888,
                    "male": 12222,
                    "female": 2255,
                    "indicators": [
                        {
                            "id": response.data["planned_interventions"][1]["indicators"][0]["id"],
                            "title": "updated_test_title_1",
                            "actual": 11111,
                            "target": 22222,
                        },
                        {
                            "id": response.data["planned_interventions"][1]["indicators"][1]["id"],
                            "title": "updated_test_title_2",
                            "actual": 33333,
                            "target": 44444,
                        },
                        # New item to be added
                        {
                            "title": "new_test_title_3",
                            "actual": 55555,
                            "target": 66666,
                        },
                    ],
                },
            ],
        }

        # Update the created dref
        url = f"/api/v2/dref/{instance.id}/"
        response = self.client.patch(url, data, format="json")
        self.assert_200(response)

        # Risk Security should have 3 items now
        self.assertEqual(len(response.data["risk_security"]), 3)
        self.assertEqual(
            {
                response.data["risk_security"][0]["id"],
                response.data["risk_security"][1]["id"],
                response.data["risk_security"][2]["risk"],
            },
            {
                data["risk_security"][0].get("id"),
                data["risk_security"][1].get("id"),
                data["risk_security"][2].get("risk"),
            },
        )

        # Source of Information should have 3 items now
        self.assertEqual(len(response.data["source_information"]), 3)
        self.assertEqual(
            {
                response.data["source_information"][0]["id"],
                response.data["source_information"][0]["source_name"],
                response.data["source_information"][1]["id"],
                response.data["source_information"][1]["source_name"],
                response.data["source_information"][2]["source_name"],
            },
            {
                data["source_information"][0].get("id"),
                data["source_information"][0].get("source_name"),
                data["source_information"][1].get("id"),
                data["source_information"][1].get("source_name"),
                data["source_information"][2].get("source_name"),
            },
        )

        # Needs Identified should have 3 items mock_now
        self.assertEqual(len(response.data["needs_identified"]), 3)
        self.assertEqual(
            {
                response.data["needs_identified"][0]["id"],
                response.data["needs_identified"][0]["title"],
                response.data["needs_identified"][1]["id"],
                response.data["needs_identified"][1]["title"],
                response.data["needs_identified"][2]["title"],
            },
            {
                data["needs_identified"][0].get("id"),
                data["needs_identified"][0].get("title"),
                data["needs_identified"][1].get("id"),
                data["needs_identified"][1].get("title"),
                data["needs_identified"][2].get("title"),
            },
        )

        # National Society Actions should have 3 items mock_now
        self.assertEqual(len(response.data["national_society_actions"]), 3)
        self.assertEqual(
            {
                response.data["national_society_actions"][0]["id"],
                response.data["national_society_actions"][0]["title"],
                response.data["national_society_actions"][1]["id"],
                response.data["national_society_actions"][1]["title"],
                response.data["national_society_actions"][2]["title"],
            },
            {
                data["national_society_actions"][0].get("id"),
                data["national_society_actions"][0].get("title"),
                data["national_society_actions"][1].get("id"),
                data["national_society_actions"][1].get("title"),
                data["national_society_actions"][2].get("title"),
            },
        )

        # Planned Interventions should have 2 items
        self.assertEqual(len(response.data["planned_interventions"]), 2)
        self.assertEqual(
            {
                response.data["planned_interventions"][0]["id"],
                response.data["planned_interventions"][0]["title"],
                response.data["planned_interventions"][1]["id"],
                response.data["planned_interventions"][1]["title"],
            },
            {
                data["planned_interventions"][0].get("id"),
                data["planned_interventions"][0].get("title"),
                data["planned_interventions"][1].get("id"),
                data["planned_interventions"][1].get("title"),
            },
        )

        # Planned Intervention - Indicators should have 3 items now
        self.assertEqual(
            {
                response.data["planned_interventions"][0]["indicators"][0]["id"],
                response.data["planned_interventions"][0]["indicators"][0]["title"],
                response.data["planned_interventions"][0]["indicators"][1]["id"],
                response.data["planned_interventions"][0]["indicators"][1]["title"],
                response.data["planned_interventions"][0]["indicators"][2]["title"],
            },
            {
                data["planned_interventions"][0]["indicators"][0].get("id"),
                data["planned_interventions"][0]["indicators"][0].get("title"),
                data["planned_interventions"][0]["indicators"][1].get("id"),
                data["planned_interventions"][0]["indicators"][1].get("title"),
                data["planned_interventions"][0]["indicators"][2].get("title"),
            },
        )

    def test_event_date_in_dref(self):
        """
        Test for the event date based on type_of_onset
        """
        national_society = Country.objects.create(name="xzz")
        data = {
            "title": "Dref test title",
            "type_of_onset": Dref.OnsetType.SLOW.value,
            "disaster_category": Dref.DisasterCategory.YELLOW.value,
            "status": Dref.Status.DRAFT.value,
            "national_society": national_society.id,
            "num_assisted": 5666,
            "num_affected": 23,
            "estimated_number_of_affected_male": 12,
            "estimated_number_of_affected_female": 12,
            "estimated_number_of_affected_girls_under_18": 12,
            "estimated_number_of_affected_boys_under_18": 12,
            "amount_requested": 127771111,
            "emergency_appeal_planned": False,
            "event_date": "2021-08-01",
            "ns_respond_date": "2021-08-01",
            "event_text": "Test text for respond",
            "did_ns_request_fund": False,
            "lessons_learned": "Test text for lessons learned",
            "complete_child_safeguarding_risk": False,
            "child_safeguarding_risk_level": "Random things",
            "event_description": "Test text for event description",
            "anticipatory_actions": "Test text for anticipatory actions",
            "event_scope": "Test text for event scope",
            "government_requested_assistance": False,
            "government_requested_assistance_date": "2021-08-01",
            "national_authorities": "Test text for national authorities",
            "icrc": "Test text for lessons learned",
            "un_or_other_actor": "Test text for lessons learned",
            "major_coordination_mechanism": "Test text for lessons learned",
            "identified_gaps": "Test text for lessons learned",
            "people_assisted": "Test text for lessons learned",
            "selection_criteria": "Test text for lessons learned",
            "entity_affected": "Test text for lessons learned",
            "community_involved": "Test text for lessons learned",
            "women": 344444,
            "men": 5666,
            "girls": 22,
            "boys": 344,
            "disability_people_per": "12.45",
            "people_per": "10.35",
            "displaced_people": 234243,
            "operation_objective": "Test script",
            "response_strategy": "Test script",
            "secretariat_service": "Test script",
            "national_society_strengthening": "",
            "ns_request_date": "2021-07-01",
            "submission_to_geneva": "2021-07-01",
            "date_of_approval": "2021-07-01",
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
            "originator_name": "Test Name",
            "originator_email": "test@gmail.com",
            "needs_identified": [{"title": "shelter_housing_and_settlements", "description": "hey"}],
            "planned_interventions": [
                {
                    "title": "shelter_housing_and_settlements",
                    "description": "matrix",
                    "budget": 23444,
                    "person_targeted": 12222,
                },
                {"id": 2, "title": "health", "description": "matrix reloaded", "budget": 451111111, "person_targeted": 345},
            ],
            "images_file": [],
            "cover_image_file": None,
        }
        url = "/api/v2/dref/"
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_update_dref_image(self):
        file1, file2, file3, file5 = DrefFileFactory.create_batch(4, created_by=self.user)
        file4 = DrefFileFactory.create(created_by=self.ifrc_user)
        dref = DrefFactory.create(created_by=self.user, status=Dref.Status.DRAFT)
        dref.users.add(self.ifrc_user)
        url = f"/api/v2/dref/{dref.id}/"
        data = {
            "images_file": [{"file": file1.id, "caption": "Test Caption"}, {"file": file2.id, "caption": "Test Caption"}],
            "modified_at": datetime.now(),
        }
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data=data, format="json")
        self.assert_400(response)

        # now remove one file and add one file by `self.ifrc_user`
        data = {
            "images_file": [{"file": file1.id, "caption": "Test Caption"}, {"file": file4.id, "caption": "Test Caption"}],
            "modified_at": datetime.now(),
        }
        self.client.force_authenticate(self.ifrc_user)
        response = self.client.patch(url, data, format="multipart")
        self.assert_200(response)

        # add from another user
        data = {"images_file": [{"file": file4.id, "caption": "Test Caption"}], "modified_at": datetime.now()}
        self.client.force_authenticate(self.ifrc_user)
        response = self.client.patch(url, data)
        self.assert_200(response)

        # add file created_by another user
        data = {"images_file": [{"file": file5.id, "caption": "Test Caption"}], "modified_at": datetime.now()}
        self.client.force_authenticate(self.ifrc_user)
        response = self.client.patch(url, data)
        # self.assert_400(response)

    def test_filter_dref_status(self):
        """
        Test to filter dref status
        """
        DrefFactory.create(title="test", status=Dref.Status.APPROVED, date_of_approval="2020-10-10", created_by=self.user)
        DrefFactory.create(status=Dref.Status.APPROVED, date_of_approval="2020-10-10", created_by=self.user)
        DrefFactory.create(status=Dref.Status.APPROVED, date_of_approval="2020-10-10", created_by=self.user)
        DrefFactory.create(status=Dref.Status.DRAFT, created_by=self.user)
        DrefFactory.create(status=Dref.Status.DRAFT, created_by=self.user)

        # filter by `In Progress`
        url = f"/api/v2/dref/?status={Dref.Status.DRAFT.value}"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_dref_country_filter(self):
        country1 = Country.objects.create(name="Test country1")
        country2 = Country.objects.create(name="Test country2")
        DrefFactory.create(title="test", status=Dref.Status.APPROVED, created_by=self.user, country=country1)
        DrefFactory.create(status=Dref.Status.APPROVED, created_by=self.user)
        DrefFactory.create(status=Dref.Status.APPROVED, created_by=self.user, country=country2)
        DrefFactory.create(status=Dref.Status.DRAFT, created_by=self.user, country=country1)
        DrefFactory.create(status=Dref.Status.DRAFT, created_by=self.user)
        url = f"/api/v2/dref/?country={country1.id}"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    @mock.patch("django.utils.timezone.now")
    def test_dref_is_approved(self, mock_now):
        """
        Test DREF publishing flow:
        - Can only approve when status=FINALIZED
        - Approve sets status=APPROVED
        """
        initial_now = datetime.now()
        mock_now.return_value = initial_now

        region = Region.objects.create(name=RegionName.AFRICA)
        country = Country.objects.create(name="country1", region=region)
        dref = DrefFactory.create(
            title="test",
            created_by=self.user,
            country=country,
            status=Dref.Status.DRAFT,
            type_of_dref=Dref.DrefType.IMMINENT,
        )
        # Normal PATCH
        url = f"/api/v2/dref/{dref.id}/"
        data = {
            "title": "New Update Title",
            "modified_at": initial_now + timedelta(days=1),
        }
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data)
        self.assert_200(response)
        # create new dref with status = DRAFT
        not_approved_dref = DrefFactory.create(
            title="test",
            created_by=self.user,
            country=country,
            status=Dref.Status.DRAFT,
        )
        url = f"/api/v2/dref/{not_approved_dref.id}/"
        self.client.force_authenticate(self.user)
        data["modified_at"] = initial_now + timedelta(days=10)
        response = self.client.patch(url, data)
        self.assert_200(response)

        data["modified_at"] = initial_now - timedelta(seconds=10)
        response = self.client.patch(url, data)
        self.assert_400(response)
        # ---- Test publishing ----
        publish_url = f"/api/v2/dref/{dref.id}/approve/"
        data = {}
        response = self.client.post(publish_url, data)
        self.assert_403(response)
        # Add permission to user
        self.dref_permission = Permission.objects.create(
            codename="dref_region_admin_0",
            content_type=ContentType.objects.get_for_model(Region),
            name="Dref Admin for 0",
        )
        self.user.user_permissions.add(self.dref_permission)
        # Try again while DRAFT. Should fail(not finalized yet)
        response = self.client.post(publish_url, data)
        self.assert_400(response)
        # Update status to FINALIZED, then publish should succeed
        dref.status = Dref.Status.FINALIZED
        dref.save(update_fields=["status"])
        dref.refresh_from_db()
        response = self.client.post(publish_url, data)
        dref.refresh_from_db()
        self.assert_200(response)
        self.assertEqual(response.data["status"], Dref.Status.APPROVED)

    def test_dref_operation_update_create(self):
        """
        Test create dref operation update
        """
        user1, _ = UserFactory.create_batch(2)
        dref = DrefFactory.create(
            title="Test Title",
            created_by=self.user,
            status=Dref.Status.APPROVED,
        )
        dref.users.add(user1)
        self.country1 = Country.objects.create(name="abc")
        self.district1 = District.objects.create(name="test district1", country=self.country1)
        old_count = DrefOperationalUpdate.objects.count()
        url = "/api/v2/dref-op-update/"
        data = {
            "dref": dref.id,
            "country": self.country1.id,
            "district": [self.district1.id],
            "starting_language": "en",
        }
        self.authenticate(self.user)
        response = self.client.post(url, data=data)
        self.assert_201(response)
        self.assertEqual(DrefOperationalUpdate.objects.count(), old_count + 1)

    def test_dref_operation_update_for_published_dref(self):
        # NOTE: If DREF is not published can't create Operational Update
        user1, _ = UserFactory.create_batch(2)
        dref = DrefFactory.create(
            title="Test Title",
            created_by=self.user,
            status=Dref.Status.DRAFT,
        )
        dref.users.add(user1)
        url = "/api/v2/dref-op-update/"
        data = {"dref": dref.id}
        self.client.force_authenticate(user1)
        response = self.client.post(url, data=data)
        self.assert_400(response)

    def test_dref_operational_create_for_parent(self):
        user1, _ = UserFactory.create_batch(2)
        dref = DrefFactory.create(
            title="Test Title",
            created_by=self.user,
            status=Dref.Status.APPROVED,
        )
        dref.users.add(user1)
        DrefOperationalUpdateFactory.create(
            dref=dref,
            status=Dref.Status.APPROVED,
            operational_update_number=1,
        )
        data = {
            "dref": dref.id,
            "starting_language": "en",
        }
        url = "/api/v2/dref-op-update/"
        self.authenticate(user1)
        response = self.client.post(url, data)
        self.assert_201(response)
        self.assertEqual(response.data["operational_update_number"], 2)

    def test_operational_update_create_for_not_published_parent(self):
        user1, _ = UserFactory.create_batch(2)
        dref = DrefFactory.create(
            title="Test Title",
            created_by=self.user,
            status=Dref.Status.APPROVED,
        )
        dref.users.add(user1)
        DrefOperationalUpdateFactory.create(
            dref=dref,
            status=Dref.Status.DRAFT,
            operational_update_number=1,
        )
        data = {
            "dref": dref.id,
        }
        url = "/api/v2/dref-op-update/"
        self.client.force_authenticate(user1)
        response = self.client.post(url, data)
        self.assert_400(response)

    def test_dref_operational_update_patch(self):
        user1, _ = UserFactory.create_batch(2)
        dref = DrefFactory.create(
            title="Test Title",
            created_by=user1,
            status=Dref.Status.APPROVED,
        )
        dref.users.add(user1)
        DrefOperationalUpdateFactory.create(
            dref=dref,
            status=Dref.Status.APPROVED,
            operational_update_number=1,
        )
        url = "/api/v2/dref-op-update/"
        data = {
            "dref": dref.id,
            "starting_language": "en",
        }
        self.authenticate(user=user1)
        response = self.client.post(url, data=data)
        self.assert_201(response)
        response_id = response.data["id"]
        data = {
            "title": "New Operation title",
            "new_operational_end_date": "2022-10-10",
            "reporting_timeframe": "2022-10-16",
            "is_timeframe_extension_required": True,
            "modified_at": datetime.now() + timedelta(days=12),
        }
        url = f"/api/v2/dref-op-update/{response_id}/"
        self.authenticate(user=user1)
        response = self.client.patch(url, data)
        self.assert_200(response)

    def test_dref_change_on_final_report_create(self):
        user1 = UserFactory.create()
        dref = DrefFactory.create(
            title="Test Title",
            created_by=user1,
            is_final_report_created=True,
        )
        DrefFinalReportFactory.create(
            dref=dref,
            status=Dref.Status.APPROVED,
        )
        # try to patch to dref
        data = {
            "title": "hey title",
            "new_operational_end_date": "2022-10-10",
            "reporting_timeframe": "2022-10-16",
            "is_timeframe_extension_required": True,
        }
        url = f"/api/v2/dref/{dref.id}/"
        self.authenticate(user=user1)
        response = self.client.patch(url, data)
        self.assert_400(response)

    def test_dref_fields_copied_to_final_report(self):
        user1, _ = UserFactory.create_batch(2)
        dref = DrefFactory.create(
            title="Test Title",
            created_by=self.user,
            status=Dref.Status.APPROVED,
            type_of_dref=Dref.DrefType.ASSESSMENT,
        )
        dref.users.add(user1)
        old_count = DrefFinalReport.objects.count()
        url = "/api/v2/dref-final-report/"
        data = {"dref": dref.id, "starting_language": "en"}
        self.authenticate(self.user)
        response = self.client.post(url, data=data)
        self.assert_201(response)
        self.assertEqual(DrefFinalReport.objects.count(), old_count + 1)
        self.assertEqual(response.data["title"], dref.title)

    def test_dref_operational_update_copied_to_final_report(self):
        """
        Here fields in final report should be copied from operational update if dref have
        operational update created for it
        """
        user1, _ = UserFactory.create_batch(2)
        dref = DrefFactory.create(
            title="Test Title",
            created_by=user1,
            status=Dref.Status.APPROVED,
            type_of_dref=Dref.DrefType.ASSESSMENT,
        )
        dref.users.add(user1)
        operational_update = DrefOperationalUpdateFactory.create(
            dref=dref,
            title="Operational Update Title",
            status=Dref.Status.DRAFT,
            operational_update_number=1,
        )
        old_count = DrefFinalReport.objects.count()
        url = "/api/v2/dref-final-report/"
        data = {"dref": dref.id, "starting_language": "en"}
        self.authenticate(self.user)
        response = self.client.post(url, data=data)
        self.assert_400(response)
        # update the operational_update
        operational_update.status = Dref.Status.APPROVED
        operational_update.save(update_fields=["status"])
        response = self.client.post(url, data=data)
        self.assert_201(response)
        self.assertEqual(DrefFinalReport.objects.count(), old_count + 1)
        self.assertEqual(response.data["title"], operational_update.title)

    def test_final_report_for_dref(self):
        # here a final report is already created for dref
        # no multiple final report allowed for a dref
        user1 = UserFactory.create()
        dref = DrefFactory.create(
            title="Test Title",
            created_by=user1,
            type_of_dref=Dref.DrefType.ASSESSMENT,
        )
        DrefFinalReportFactory.create(
            dref=dref,
        )
        url = "/api/v2/dref-final-report/"
        data = {"dref": dref.id}
        self.authenticate(self.user)
        response = self.client.post(url, data)
        self.assert_400(response)

    def test_update_dref_for_final_report_created(self):
        user1 = UserFactory.create()
        dref = DrefFactory.create(
            title="Test Title1",
            created_by=user1,
            status=Dref.Status.APPROVED,
            type_of_dref=Dref.DrefType.IMMINENT,
        )
        url = "/api/v2/dref-final-report/"
        data = {"dref": dref.id, "starting_language": "en"}
        self.authenticate(self.user)
        response = self.client.post(url, data)
        self.assert_201(response)
        dref_response = Dref.objects.get(id=dref.id)
        self.assertEqual(dref_response.is_final_report_created, True)

    def test_final_report_update_once_published(self):
        user1 = UserFactory.create()
        region = Region.objects.create(name=RegionName.AFRICA)
        country = Country.objects.create(name="country1", region=region)
        dref = DrefFactory.create(
            title="Test Title",
            type_of_dref=Dref.DrefType.ASSESSMENT,
            created_by=user1,
            country=country,
            status=Dref.Status.APPROVED,
        )
        final_report = DrefFinalReportFactory(
            title="Test title",
            dref=dref,
            country=country,
            type_of_dref=Dref.DrefType.RESPONSE,
            status=Dref.Status.FINALIZED,
        )
        final_report.users.set([user1])
        url = f"/api/v2/dref-final-report/{final_report.id}/approve/"
        data = {}
        self.client.force_authenticate(user1)
        response = self.client.post(url, data)
        self.assert_403(response)
        # add permission to request user
        self.dref_permission = Permission.objects.create(
            codename="dref_region_admin_0",
            content_type=ContentType.objects.get_for_model(Region),
            name="Dref Admin for 0",
        )
        user1.user_permissions.add(self.dref_permission)
        self.client.force_authenticate(user1)
        response = self.client.post(url, data)
        self.assert_200(response)
        self.assertEqual(response.data["status"], Dref.Status.APPROVED)
        # now try to patch to the final report
        url = f"/api/v2/dref-final-report/{final_report.id}/"
        data = {
            "title": "New Field Report Title",
        }
        response = self.client.patch(url, data)
        self.assert_400(response)

    def test_dref_for_assessment_report(self):
        old_count = Dref.objects.count()
        national_society = Country.objects.create(name="xzz")
        disaster_type = DisasterType.objects.create(name="abc")
        data = {
            "title": "Dref test title",
            "type_of_onset": Dref.OnsetType.SLOW.value,
            "type_of_dref": Dref.DrefType.ASSESSMENT,
            "disaster_category": Dref.DisasterCategory.YELLOW.value,
            "status": Dref.Status.DRAFT.value,
            "num_assisted": 5666,
            "num_affected": 23,
            "amount_requested": 127771111,
            "emergency_appeal_planned": False,
            "event_date": "2021-08-01",
            "ns_respond_date": "2021-08-01",
            "event_text": "Test text for respond",
            "did_ns_request_fund": False,
            "lessons_learned": "Test text for lessons learned",
            "complete_child_safeguarding_risk": False,
            "child_safeguarding_risk_level": "Random Things",
            "event_description": "Test text for event description",
            "anticipatory_actions": "Test text for anticipatory actions",
            "event_scope": "Test text for event scope",
            "government_requested_assistance": False,
            "government_requested_assistance_date": "2021-08-01",
            "national_authorities": "Test text for national authorities",
            "icrc": "Test text for lessons learned",
            "un_or_other_actor": "Test text for lessons learned",
            "major_coordination_mechanism": "Test text for lessons learned",
            "identified_gaps": "Test text for lessons learned",
            "people_assisted": "Test text for lessons learned",
            "selection_criteria": "Test text for lessons learned",
            "entity_affected": "Test text for lessons learned",
            "community_involved": "Test text for lessons learned",
            "women": 344444,
            "men": 5666,
            "girls": 22,
            "boys": 344,
            "disability_people_per": "12.45",
            "people_per": "10.35",
            "displaced_people": 234243,
            "operation_objective": "Test script",
            "response_strategy": "Test script",
            "secretariat_service": "Test script",
            "national_society_strengthening": "",
            "ns_request_date": "2021-07-01",
            "submission_to_geneva": "2021-07-01",
            "date_of_approval": "2021-07-01",
            "end_date": "2021-07-05",
            "publishing_date": "2021-08-01",
            "operation_timeframe": 1,
            "appeal_code": "J7876",
            "glide_code": "ER878",
            "appeal_manager_name": "Test Name",
            "appeal_manager_email": "test@gmail.com",
            "project_manager_name": "Test Name",
            "project_manager_email": "test@gmail.com",
            "national_society_contact_name": "Test Name",
            "national_society_contact_email": "test@gmail.com",
            "national_society_integrity_contact_name": "Test Name",
            "national_society_integrity_contact_email": "test@test.com",
            "national_society_integrity_contact_phone_number": "8191719",
            "national_society_hotline_phone_number": "8191719",
            "media_contact_name": "Test Name",
            "media_contact_email": "test@gmail.com",
            "ifrc_emergency_name": "Test Name",
            "ifrc_emergency_email": "test@gmail.com",
            "originator_name": "Test Name",
            "originator_email": "test@gmail.com",
            "national_society": national_society.id,
            "disaster_type": disaster_type.id,
            "needs_identified": [{"title": "environment_sustainability ", "description": "hey"}],
        }
        url = "/api/v2/dref/"
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Dref.objects.count(), old_count + 1)

    def test_dref_for_super_user(self):
        user1 = UserFactory.create(
            username="user1@test.com",
            first_name="Test",
            last_name="User1",
            password="admin123",
            email="user1@test.com",
            is_superuser=True,
        )
        user2 = UserFactory.create(
            username="user2@test.com",
            first_name="Test",
            last_name="User2",
            password="admin123",
            email="user2@test.com",
        )
        user3 = UserFactory.create(
            username="user3@test.com",
            first_name="Test",
            last_name="User3",
            password="admin123",
            email="user3@test.com",
        )
        dref1 = DrefFactory.create(
            title="Test Title",
            created_by=user2,
        )
        DrefFactory.create(
            title="Test Title New",
        )

        # authenticate with user1(superuser)
        # user1 should be able to view all dref
        url = "/api/v2/dref/"
        self.client.force_authenticate(user1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

        # authenticate with User2
        self.client.force_authenticate(user2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], dref1.id)

        # authenticate with User3
        self.client.force_authenticate(user3)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 0)

    def test_dref_latest_update(self):
        dref = DrefFactory.create(
            title="Test Title",
            created_by=self.user,
            status=Dref.Status.DRAFT,
            modified_at=datetime(2022, 4, 18, 2, 29, 39, 793615),
        )
        url = f"/api/v2/dref/{dref.id}/"
        data = {
            "title": "New title",
        }

        # without `modified_at`
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 400)

        # with `modified_at` less than instance `modified_at`
        data["modified_at"] = datetime(2022, 2, 18, 2, 29, 39, 793615)
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 400)

        data["modified_at"] = datetime.now()
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 200)
        # Title should be latest since modified_at is greater than modified_at in database
        self.assertEqual(response.data["title"], "New title")

    def test_dref_create_and_update_in_local_language(
        self,
    ):
        national_society = Country.objects.create(name="Test country xzz")
        disaster_type = DisasterType.objects.create(name="Test country abc")

        data = {
            "title": "Prueba de título Dref",
            "type_of_onset": Dref.OnsetType.SLOW.value,
            "disaster_category": Dref.DisasterCategory.YELLOW.value,
            "status": Dref.Status.DRAFT.value,
            "num_assisted": 5666,
            "num_affected": 23,
            "amount_requested": 127771111,
            "emergency_appeal_planned": False,
            "event_date": "2021-08-01",
            "ns_respond_date": "2021-08-01",
            "event_text": "Texto de prueba para la respuesta",
            "did_ns_request_fund": False,
            "lessons_learned": "Texto de prueba para lecciones aprendidas",
            "complete_child_safeguarding_risk": True,
            "child_safeguarding_risk_level": "Muy alto",
            "event_description": "Texto de prueba para descripción del evento",
            "anticipatory_actions": "Texto de prueba para acciones anticipatorias",
            "event_scope": "Texto de prueba para alcance del evento",
            "government_requested_assistance": False,
            "government_requested_assistance_date": "2021-08-01",
            "national_authorities": "Texto de prueba para autoridades nacionales",
            "icrc": "Texto de prueba para lecciones aprendidas",
            "un_or_other_actor": "Texto de prueba para lecciones aprendidas",
            "major_coordination_mechanism": "Texto de prueba para lecciones aprendidas",
            "identified_gaps": "Texto de prueba para lecciones aprendidas",
            "people_assisted": "Texto de prueba para lecciones aprendidas",
            "selection_criteria": "Texto de prueba para lecciones aprendidas",
            "entity_affected": "Texto de prueba para lecciones aprendidas",
            "community_involved": "Texto de prueba para lecciones aprendidas",
            "women": 344444,
            "men": 5666,
            "girls": 22,
            "boys": 344,
            "disability_people_per": "12.45",
            "people_per": "10.35",
            "displaced_people": 234243,
            "operation_objective": "Texto de prueba para objetivo de operación",
            "response_strategy": "Texto de prueba para estrategia de respuesta",
            "secretariat_service": "Texto de prueba para servicio de secretaría",
            "national_society_strengthening": "",
            "ns_request_date": "2021-07-01",
            "submission_to_geneva": "2021-07-01",
            "date_of_approval": "2021-07-01",
            "end_date": "2021-07-05",
            "publishing_date": "2021-08-01",
            "operation_timeframe": 4,
            "appeal_code": "J7876",
            "glide_code": "ER878",
            "appeal_manager_name": "Nombre de prueba",
            "appeal_manager_email": "test@gmail.com",
            "project_manager_name": "Nombre de prueba",
            "project_manager_email": "test@gmail.com",
            "national_society_contact_name": "Nombre de prueba",
            "national_society_contact_email": "test@gmail.com",
            "media_contact_name": "Nombre de prueba",
            "media_contact_email": "test@gmail.com",
            "ifrc_emergency_name": "Nombre de prueba",
            "ifrc_emergency_email": "test@gmail.com",
            "originator_name": "Nombre de prueba",
            "originator_email": "test@gmail.com",
            "national_society": national_society.id,
            "disaster_type": disaster_type.id,
            "needs_identified": [{"title": "shelter_housing_and_settlements", "description": "hola"}],
            "starting_language": "es",
            "planned_interventions": [
                {
                    "title": "shelter_housing_and_settlements",
                    "description": "matriz",
                    "budget": 23444,
                    "male": 12222,
                    "female": 2255,
                    "indicators": [
                        {
                            "title": "título de prueba",
                            "actual": 21232,
                            "target": 44444,
                        }
                    ],
                }
            ],
        }

        url = "/api/v2/dref/"

        self.client.force_authenticate(self.user)
        response = self.client.post(url, data, format="json", HTTP_ACCEPT_LANGUAGE="es")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["starting_language"], "es")
        self.assertEqual(response.data["translation_module_original_language"], "es")
        self.assertEqual(response.data["title"], "Prueba de título Dref")
        # Test update
        dref_id = response.data["id"]
        url = f"/api/v2/dref/{dref_id}/"
        #  update in French
        data_fr = {"title": "Titre en français", "modified_at": datetime.now()}
        response = self.client.patch(url, data=data_fr, format="json", HTTP_ACCEPT_LANGUAGE="fr")
        self.assert_400(response)

        #  update in Arabic
        data_ar = {"title": "العنوان بالعربية", "modified_at": datetime.now()}
        response = self.client.patch(url, data=data_ar, format="json", HTTP_ACCEPT_LANGUAGE="ar")
        self.assert_400(response)

        #  update in English
        data_en = {"title": "Updated title in English", "modified_at": datetime.now()}
        response = self.client.patch(url, data=data_en, format="json", HTTP_ACCEPT_LANGUAGE="en")
        self.assert_400(response)
        # Test update when status is Finalizing
        dref1 = DrefFactory.create(
            title="Title in English",
            type_of_dref=Dref.DrefType.IMMINENT,
            created_by=self.user,
            status=Dref.Status.FINALIZING,
        )
        url = f"/api/v2/dref/{dref1.id}/"
        response = self.client.patch(url, data=data_en, format="json", HTTP_ACCEPT_LANGUAGE="es")
        self.assert_400(response)

    @patch("dref.views.transaction.on_commit", lambda func: func())
    @patch("dref.views.process_dref_translation")
    def test_update_and_finalize_dref(self, mock_translation):
        dref = DrefFactory.create(
            title="Título original en español",
            type_of_dref=Dref.DrefType.IMMINENT,
            created_by=self.user,
            status=Dref.Status.DRAFT,
            translation_module_original_language="es",
        )
        dref2 = DrefFactory.create(
            title="title123",
            type_of_dref=Dref.DrefType.ASSESSMENT,
            created_by=self.user,
            status=Dref.Status.DRAFT,
            translation_module_original_language="en",
        )
        url = f"/api/v2/dref/{dref.id}/"
        self.client.force_authenticate(self.user)
        # update in Spanish
        data_es = {"title": "en español", "modified_at": datetime.now()}
        response = self.client.patch(url, data=data_es, HTTP_ACCEPT_LANGUAGE="es")
        self.assert_200(response)
        self.assertEqual(response.data["title"], "en español")

        # Update in French
        data_fr = {"title": "Titre en français", "modified_at": datetime.now()}
        response = self.client.patch(url, data=data_fr, format="json", HTTP_ACCEPT_LANGUAGE="fr")
        self.assert_400(response)

        # Update in Arabic
        data_ar = {"title": "العنوان بالعربية", "modified_at": datetime.now()}
        response = self.client.patch(url, data=data_ar, format="json", HTTP_ACCEPT_LANGUAGE="ar")
        self.assert_400(response)
        # Update in English before translation complete
        data_en = {"title": "Updated title in English", "modified_at": datetime.now()}
        response = self.client.patch(url, data=data_en, HTTP_ACCEPT_LANGUAGE="en")
        self.assert_400(response)

        finalize_url = f"/api/v2/dref/{dref2.id}/finalize/"
        response = self.client.post(finalize_url)
        self.assert_200(response)
        self.assertEqual(response.data["status"], Dref.Status.FINALIZED)

        # Finalize with original language
        finalize_url = f"/api/v2/dref/{dref.id}/finalize/"
        response = self.client.post(finalize_url)
        model_name = get_model_name(type(dref))
        mock_translation.delay.assert_called_once_with(model_name, dref.pk)
        dref.refresh_from_db()
        self.assert_202(response)

    def test_dref_op_update_locking(self):
        user1, _ = UserFactory.create_batch(2)
        dref = DrefFactory.create(
            title="Test Title",
            created_by=user1,
            status=Dref.Status.APPROVED,
        )
        dref.users.add(user1)
        DrefOperationalUpdateFactory.create(
            dref=dref,
            status=Dref.Status.APPROVED,
            operational_update_number=1,
            modified_at=datetime.now(),
        )
        url = "/api/v2/dref-op-update/"
        data = {
            "dref": dref.id,
            "starting_language": "en",
        }
        self.authenticate(user=user1)
        response = self.client.post(url, data=data)
        self.assert_201(response)
        response_id = response.data["id"]

        # without `modified_at`
        data = {
            "title": "New Operation title",
            "new_operational_end_date": "2022-10-10",
            "reporting_timeframe": "2022-10-16",
            "is_timeframe_extension_required": True,
            "starting_language": "en",
        }
        url = f"/api/v2/dref-op-update/{response_id}/"
        self.authenticate(user=user1)
        response = self.client.patch(url, data)
        self.assert_400(response)

        # with `modified_at` less than instance `modified_at`
        data["modified_at"] = datetime.now() - timedelta(days=2)
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_create_and_update_operational_update(self):
        self.country = Country.objects.create(name="test ops country")
        self.district = District.objects.create(name="test ops dis", country=self.country)

        user1, user2 = UserFactory.create_batch(2)
        dref = DrefFactory.create(
            title="Test Title",
            created_by=user1,
            status=Dref.Status.DRAFT,
            starting_language="en",
        )
        dref2 = DrefFactory.create(
            title="Título en español",
            created_by=user1,
            status=Dref.Status.APPROVED,
            starting_language="fr",
        )
        dref3 = DrefFactory.create(
            title="Titre en français",
            created_by=user1,
            status=Dref.Status.APPROVED,
            starting_language="fr",
        )
        dref4 = DrefFactory.create(
            title="Titre en français",
            created_by=user1,
            status=Dref.Status.APPROVED,
            starting_language="fr",
        )
        ops_update_data = {
            "dref": dref.id,
            "country": self.country.id,
            "district": [self.district.id],
        }
        ops_update_data2 = {
            "dref": dref2.id,
            "country": self.country.id,
            "district": [self.district.id],
            "starting_language": "es",
        }
        ops_update_data3 = {
            "dref": dref3.id,
            "country": self.country.id,
            "district": [self.district.id],
            "starting_language": "fr",
        }
        ops_update_data4 = DrefOperationalUpdateFactory.create(
            dref=dref4,
            country=self.country,
            starting_language="fr",
            status=Dref.Status.FINALIZING,
        )
        self.authenticate(user1)
        # Test create ops update for DRAFT dref
        self.authenticate(user2)
        url = "/api/v2/dref-op-update/"
        response = self.client.post(url, data=ops_update_data)
        self.assert_400(response)

        # Test create ops-update with original language other than dref original language
        response = self.client.post(url, data=ops_update_data2)
        self.assert_400(response)

        # Test create ops-update with approved dref status and matching language with dref
        response = self.client.post(url, data=ops_update_data3, HTTP_ACCEPT_LANGUAGE="fr")
        self.assert_201(response)
        self.assertEqual(response.data["translation_module_original_language"], "fr")
        ops_update_id = response.data["id"]
        # Test Update
        update_url = f"/api/v2/dref-op-update/{ops_update_id}/"
        data_ar = {
            "title": "العنوان بالعربية",
            "modified_at": datetime.now(),
            "starting_language": "ar",
        }
        response = self.client.patch(update_url, data=data_ar, HTTP_ACCEPT_LANGUAGE="ar")
        self.assert_400(response)
        # Update in Spanish
        data_es = {
            "title": "Título en español",
            "modified_at": datetime.now(),
            "starting_language": "es",
        }
        response = self.client.patch(update_url, data=data_es, HTTP_ACCEPT_LANGUAGE="es")
        self.assert_400(response)

        # Update in English
        data_en = {
            "title": "Updated title in English",
            "modified_at": datetime.now(),
            "starting_language": "en",
        }
        response = self.client.patch(update_url, data=data_en, HTTP_ACCEPT_LANGUAGE="en")
        self.assert_400(response)

        # Update in French
        data_fr = {
            "title": "Titre en français",
            "modified_at": datetime.now(),
            "starting_language": "fr",
        }
        response = self.client.patch(update_url, data=data_fr, HTTP_ACCEPT_LANGUAGE="fr")
        self.assert_200(response)
        self.assertEqual(response.data["title"], "Titre en français")
        # Test Finalizing ops-update
        data = {
            "title": "Titre en français",
        }
        self.authenticate(user1)
        url = f"/api/v2/dref-op-update/{ops_update_data4.id}/"
        response = self.client.patch(url, data=data, HTTP_ACCEPT_LANGUAGE="fr")
        self.assert_400(response)

    @patch("dref.views.transaction.on_commit", lambda func: func())
    @patch("dref.views.process_dref_translation")
    def test_dref_operational_update_finalize(self, mock_translation):
        # Create users
        user1, user2 = UserFactory.create_batch(2)
        dref = DrefFactory.create(
            title="Test Title",
            created_by=user1,
            status=Dref.Status.APPROVED,
            translation_module_original_language="en",
        )
        dref2 = DrefFactory.create(
            title="Test Title",
            created_by=user1,
            status=Dref.Status.APPROVED,
            translation_module_original_language="en",
        )
        dref.users.add(user1)
        op_update = DrefOperationalUpdateFactory.create(
            dref=dref,
            status=Dref.Status.DRAFT,
            operational_update_number=1,
            modified_at=datetime.now(),
            translation_module_original_language="ar",
        )

        op_update2 = DrefOperationalUpdateFactory.create(
            dref=dref2,
            status=Dref.Status.DRAFT,
            operational_update_number=1,
            modified_at=datetime.now(),
            translation_module_original_language="en",
        )

        url = f"/api/v2/dref-op-update/{op_update.id}/"
        self.client.force_authenticate(user1)

        # Update in Arabic (original language)
        data_ar = {"title": "العنوان بالعربية", "modified_at": datetime.now()}
        response = self.client.patch(url, data=data_ar, HTTP_ACCEPT_LANGUAGE="ar")
        self.assert_200(response)
        self.assertEqual(response.data["title"], "العنوان بالعربية")

        # Update in English
        data_en = {"title": "Updated title in English", "modified_at": datetime.now()}
        response = self.client.patch(url, data=data_en, HTTP_ACCEPT_LANGUAGE="en")
        self.assert_400(response)

        # Finalize with original language
        finalize_url = f"/api/v2/dref-op-update/{op_update.id}/finalize/"
        response = self.client.post(finalize_url)
        model_name = get_model_name(type(op_update))
        mock_translation.delay.assert_called_once_with(model_name, op_update.pk)
        dref.refresh_from_db()
        self.assert_202(response)

        # Finalize English-language report (no translation)
        finalize_url = f"/api/v2/dref-op-update/{op_update2.id}/finalize/"
        response = self.client.post(finalize_url)
        self.assert_200(response)
        self.assertEqual(response.data["status"], Dref.Status.FINALIZED)

    def test_optimistic_lock_in_final_report(self):
        user1 = UserFactory.create()
        dref = DrefFactory.create(
            title="Test Title",
            created_by=user1,
            status=Dref.Status.APPROVED,
        )
        final_report = DrefFinalReportFactory(
            title="Test title",
            created_by=user1,
            dref=dref,
        )
        url = f"/api/v2/dref-final-report/{final_report.id}/"

        # update data without `modified_at`
        data = {"title": "New Updated Title"}
        self.client.force_authenticate(user1)
        response = self.client.patch(url, data)
        self.assert_400(response)

        # with `modified_at` less than instance `modified_at`
        data["modified_at"] = datetime.now() - timedelta(days=2)
        response = self.client.patch(url, data=data)
        self.assert_400(response)

        # with `modified_at` greater than instance `modified_at`
        data["modified_at"] = datetime.now() + timedelta(days=2)
        response = self.client.patch(url, data=data)
        self.assert_200(response)

    def test_dref_permission(self):
        user1 = UserFactory.create(
            username="user1@test.com",
            first_name="Test",
            last_name="User1",
            password="admin123",
            email="user1@test.com",
            is_superuser=True,
        )
        user2 = UserFactory.create(
            username="user2@test.com",
            first_name="Test",
            last_name="User2",
            password="admin123",
            email="user2@test.com",
        )
        user3 = UserFactory.create(
            username="user4@test.com",
            first_name="Test",
            last_name="User3",
            password="admin123",
            email="user4@test.com",
        )
        user4 = UserFactory.create(
            username="user3@test.com",
            first_name="Test",
            last_name="User4",
            password="admin123",
            email="user3@test.com",
        )
        dref1 = DrefFactory.create(title="Test Title", created_by=user1, status=Dref.Status.DRAFT)
        dref1.users.add(user2)
        DrefFactory.create(title="Test Title New", created_by=user3)
        get_url = "/api/v2/dref/"
        # authenticate with superuser
        # should be able to view all drefs
        self.client.force_authenticate(user1)
        response = self.client.get(get_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

        # # let superuser patch the dref
        patch_url = f"/api/v2/dref/{dref1.id}/"
        data = {"title": "New test title", "modified_at": datetime.now()}
        response = self.client.patch(patch_url, data=data)
        self.assertEqual(response.status_code, 200)

        # # lets authenticate with user for whom dref is shared with
        self.client.force_authenticate(user2)
        response = self.client.get(get_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

        # # try to patch by user
        self.client.force_authenticate(user2)
        data = {
            "title": "New test title",
            "modified_at": datetime.now() + timedelta(days=1),
        }
        response = self.client.patch(patch_url, data=data)
        self.assertEqual(response.status_code, 200)

        # # try to authenticate with user who is neither assigned nor created_by
        self.client.force_authenticate(user4)
        response = self.client.get(get_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 0)

    def test_superuser_permission_operational_update(self):
        super_user = UserFactory.create(
            username="user1@test.com",
            first_name="Test",
            last_name="User1",
            password="admin123",
            email="user1@test.com",
            is_superuser=True,
        )
        dref = DrefFactory.create(
            title="Test Title",
            status=Dref.Status.APPROVED,
        )
        self.country1 = Country.objects.create(name="abc")
        self.district1 = District.objects.create(name="test district1", country=self.country1)
        url = "/api/v2/dref-op-update/"
        data = {
            "dref": dref.id,
            "country": self.country1.id,
            "district": [self.district1.id],
            "starting_language": "en",
        }
        # authenticate with superuser
        self.authenticate(super_user)
        response = self.client.post(url, data=data)
        self.assert_201(response)

    def test_operational_update_view_permission(self):
        Dref.objects.all().delete()
        user1, user2, user3 = UserFactory.create_batch(3)
        dref = DrefFactory.create(
            title="Test Title",
            status=Dref.Status.APPROVED,
            created_by=user1,
        )
        operational_update = DrefOperationalUpdateFactory.create(
            dref=dref,
        )
        operational_update.users.set([user3])
        self.country1 = Country.objects.create(name="abc")
        self.district1 = District.objects.create(name="test district1", country=self.country1)

        # Here user1 is able to see the operational_update
        url = "/api/v2/dref-op-update/"
        self.authenticate(user1)
        response = self.client.get(url)
        self.assert_200(response)

        # authenticate with the user3
        # here user3 should be able to view dref
        # since user3 is assigned to op-update created from dref
        dref_url = "/api/v2/dref/"
        self.authenticate(user3)
        response = self.client.get(dref_url)
        self.assert_200(response)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], dref.id)

        # authenticate with user2
        # here user2 is not able to view dref
        self.authenticate(user2)
        response = self.client.get(dref_url)
        self.assert_200(response)
        self.assertEqual(len(response.data["results"]), 0)

    def test_concurrent_dref_operational_update(self):
        user1, user2, user3 = UserFactory.create_batch(3)
        dref = DrefFactory.create(
            title="Test Title",
            status=Dref.Status.APPROVED,
            created_by=user1,
        )
        operational_update = DrefOperationalUpdateFactory.create(
            dref=dref, status=Dref.Status.DRAFT, operational_update_number=1, created_by=user3
        )
        operational_update.users.set([user3, user2])
        self.country1 = Country.objects.create(name="abc")
        self.district1 = District.objects.create(name="test district1", country=self.country1)

        # Here user1 is able to see the operational_update
        url = "/api/v2/dref-op-update/"
        self.authenticate(user1)
        response = self.client.get(url)
        self.assert_200(response)

        # create another operational update from corresponding dref
        operation_update2 = DrefOperationalUpdateFactory.create(dref=dref, status=Dref.Status.DRAFT, operational_update_number=2)
        operation_update2.users.set([user2])

        # authenticate with user2
        url = "/api/v2/dref-op-update/"
        self.authenticate(user2)
        response = self.client.get(url)
        self.assert_200(response)

        # user2 should also be able to view dref
        dref_url = "/api/v2/dref/"
        self.authenticate(user2)
        response = self.client.get(dref_url)
        self.assert_200(response)
        self.assertEqual(len(response.data["results"]), 1)

        # authenticate with user1
        self.authenticate(user1)
        response = self.client.get(dref_url)
        self.assert_200(response)

    def test_dref_type_loan(self):
        user1, _ = UserFactory.create_batch(2)
        dref = DrefFactory.create(
            title="Test Title",
            created_by=self.user,
            status=Dref.Status.APPROVED,
            type_of_dref=Dref.DrefType.LOAN,
        )
        dref.users.add(user1)
        old_count = DrefFinalReport.objects.count()
        url = "/api/v2/dref-final-report/"
        data = {
            "dref": dref.id,
            "starting_language": "en",
        }
        self.authenticate(self.user)
        response = self.client.post(url, data=data)
        self.assert_400(response)

        # update the dref type to other
        dref.type_of_dref = Dref.DrefType.ASSESSMENT
        dref.save(update_fields=["type_of_dref"])

        self.authenticate(self.user)
        response = self.client.post(url, data=data)
        self.assert_201(response)
        self.assertEqual(DrefFinalReport.objects.count(), old_count + 1)

    @mock.patch("dref.tasks.send_dref_email")
    def test_dref_share(self, send_dref_email):
        user1 = UserFactory.create(
            username="user1@test.com",
            first_name="Test",
            last_name="User1",
            password="admin123",
            email="user1@test.com",
            is_superuser=True,
        )
        user2 = UserFactory.create(
            username="user2@test.com",
            first_name="Test",
            last_name="User2",
            password="admin123",
            email="user2@test.com",
        )
        user3 = UserFactory.create(
            username="user4@test.com",
            first_name="Test",
            last_name="User3",
            password="admin123",
            email="user4@test.com",
        )
        user4 = UserFactory.create(
            username="user3@test.com",
            first_name="Test",
            last_name="User4",
            password="admin123",
            email="user3@test.com",
        )
        dref1 = DrefFactory.create(
            title="Test Title",
            created_by=user1,
        )
        op_update = DrefOperationalUpdateFactory.create(
            dref=dref1,
            created_by=user1,
        )
        final_report = DrefFinalReportFactory.create(
            dref=dref1,
            created_by=user1,
        )
        self.client.force_authenticate(user1)
        data = {"users": [user2.id, user3.id, user4.id], "dref": dref1.id}

        # share url
        url = "/api/v2/dref-share/"
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(list(DrefFinalReport.objects.filter(id=final_report.id).values_list("users", flat=True))),
            set([user2.id, user3.id, user4.id]),
        )
        self.assertEqual(
            set(list(Dref.objects.filter(id=dref1.id).values_list("users", flat=True))), set([user2.id, user3.id, user4.id])
        )
        self.assertEqual(
            set(list(DrefOperationalUpdate.objects.filter(id=op_update.id).values_list("users", flat=True))),
            set([user2.id, user3.id, user4.id]),
        )
        # check if the notification is called
        self.assertTrue(send_dref_email.is_called())

    def test_completed_dref_operations(self):
        country_1 = Country.objects.create(name="country1")
        country_2 = Country.objects.create(name="country2")
        country_3 = Country.objects.create(name="country3")

        # create some dref final report
        DrefFinalReport.objects.all().delete()
        DrefFinalReportFactory.create(
            status=Dref.Status.APPROVED,
            country=country_1,
            type_of_dref=Dref.DrefType.ASSESSMENT,
        )
        DrefFinalReportFactory.create(
            status=Dref.Status.APPROVED,
            country=country_3,
            type_of_dref=Dref.DrefType.ASSESSMENT,
        )
        final_report_1, final_report_2 = DrefFinalReportFactory.create_batch(
            2,
            status=Dref.Status.APPROVED,
            country=country_2,
            type_of_dref=Dref.DrefType.LOAN,
        )
        DrefFinalReportFactory.create(country=country_2)

        url = "/api/v2/completed-dref/"
        self.client.force_authenticate(self.root_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 4)

        # filter by national society
        url = f"/api/v2/completed-dref/?country={country_2.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(set([item["id"] for item in response.data["results"]]), set([final_report_1.id, final_report_2.id]))
        url = "/api/v2/completed-dref/?type_of_dref=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_filter_active_dref(self):
        country_1 = Country.objects.create(name="country1")
        country_2 = Country.objects.create(name="country2")

        # create some dref
        dref_1 = DrefFactory.create(
            is_active=True, type_of_dref=Dref.DrefType.ASSESSMENT, country=country_1, created_by=self.root_user
        )
        dref_2 = DrefFactory.create(is_active=True, type_of_dref=Dref.DrefType.LOAN, country=country_2, created_by=self.root_user)
        # some dref final report
        dref_final_report = DrefFinalReportFactory.create(
            status=Dref.Status.DRAFT,
            country=country_1,
            type_of_dref=Dref.DrefType.ASSESSMENT,
            dref=dref_1,
            created_by=self.root_user,
        )
        DrefFinalReportFactory.create(
            status=Dref.Status.DRAFT,
            country=country_2,
            type_of_dref=Dref.DrefType.LOAN,
            dref=dref_2,
            created_by=self.root_user,
        )

        url = "/api/v2/active-dref/"
        self.client.force_authenticate(self.root_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

        # filter by national society
        url = f"/api/v2/active-dref/?country={country_1.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

        url = f"/api/v2/active-dref/?type_of_dref={Dref.DrefType.ASSESSMENT}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["final_report_details"]["id"], dref_final_report.id)

    def test_dref_share_users(self):
        user1 = UserFactory.create(
            username="user1@test.com",
            first_name="Test",
            last_name="User1",
            password="admin123",
            email="user1@test.com",
            is_superuser=True,
        )
        user2 = UserFactory.create(
            username="user2@test.com",
            first_name="Test",
            last_name="User2",
            password="admin123",
            email="user2@test.com",
        )
        user3 = UserFactory.create(
            username="user4@test.com",
            first_name="Test",
            last_name="User3",
            password="admin123",
            email="user4@test.com",
        )
        user4 = UserFactory.create(
            username="user3@test.com",
            first_name="Test",
            last_name="User4",
            password="admin123",
            email="user3@test.com",
        )
        dref = DrefFactory.create(
            title="Test Title",
            created_by=user1,
        )
        dref.users.set([user2, user3, user4])
        url = "/api/v2/dref-share-user/"
        self.client.force_authenticate(user1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(set(response.data["results"][0]["users"]), set([user2.id, user3.id, user4.id]))

    def test_dref_imminent(self):
        old_count = Dref.objects.count()
        sct_1 = SectorFactory(
            title="shelter_housing_and_settlements",
        )
        sct_2 = SectorFactory(
            title="health",
        )
        national_society = Country.objects.create(name="abc")
        disaster_type = DisasterType.objects.create(name="disaster 1")
        data = {
            "title": "Dref test title",
            "type_of_onset": Dref.OnsetType.SUDDEN.value,
            "type_of_dref": Dref.DrefType.IMMINENT,
            "disaster_category": Dref.DisasterCategory.YELLOW.value,
            "status": Dref.Status.DRAFT.value,
            "num_assisted": 5666,
            "num_affected": 23,
            "amount_requested": 127771111,
            "women": 344444,
            "men": 5666,
            "girls": 22,
            "boys": 344,
            "appeal_manager_name": "Test Name",
            "ifrc_emergency_email": "test@gmail.com",
            "is_surge_personnel_deployed": False,
            "originator_email": "test@gmail.com",
            "national_society": national_society.id,
            "disaster_type": disaster_type.id,
            "planned_interventions": [
                {
                    "title": "shelter_housing_and_settlements",
                    "description": "matrix",
                    "budget": 23444,
                    "male": 12222,
                    "female": 2255,
                    "indicators": [
                        {
                            "title": "test_title",
                            "actual": 21232,
                            "target": 44444,
                        }
                    ],
                },
            ],
            "proposed_action": [
                {
                    "proposed_type": ProposedAction.Action.EARLY_ACTION.value,
                    "activities": [
                        {
                            "sector": sct_1.id,
                            "activity": "test activity 1",
                        },
                        {
                            "sector": sct_2.id,
                            "activity": "test activity 2",
                        },
                        {
                            "sector": sct_2.id,
                            "activity": "Test activity 3",
                        },
                    ],
                    "total_budget": 70000,
                },
                {
                    "proposed_type": ProposedAction.Action.EARLY_RESPONSE.value,
                    "activities": [
                        {
                            "sector": sct_1.id,
                            "activity": "test activity 1",
                        },
                        {
                            "sector": sct_2.id,
                            "activity": "test activity 2",
                        },
                    ],
                    "total_budget": 5000,
                },
            ],
            "sub_total_cost": 75000,
            "indirect_cost": 5000,
            "total_cost": 80000,
        }
        url = "/api/v2/dref/"
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data, format="json")
        self.assert_201(response)
        self.assertEqual(Dref.objects.count(), old_count + 1)

        # Checking for surge personnel deployed
        data["is_surge_personnel_deployed"] = True
        data["surge_deployment_cost"] = 10000
        data["indirect_cost"] = 5800
        data["total_cost"] = 90800
        response = self.client.post(url, data, format="json")
        self.assert_201(response)
        self.assertEqual(Dref.objects.count(), old_count + 2)
        response_id = response.data["id"]

        # update the dref with proposed action
        url = f"/api/v2/dref/{response_id}/"
        data = {
            "modified_at": datetime.now(),
            **data,
            "proposed_action": [
                {
                    "id": response.data["proposed_action"][0]["id"],
                    "proposed_type": ProposedAction.Action.EARLY_ACTION.value,
                    "activities": [
                        {
                            "id": response.data["proposed_action"][0]["activities"][0]["id"],
                            "sector": sct_1.id,
                            "activity": "1 changed",
                        },
                        {
                            "id": response.data["proposed_action"][0]["activities"][1]["id"],
                            "sector": sct_1.id,
                            "activity": "Sector changed",
                        },
                    ],
                    "total_budget": 70000,
                },
                {
                    "id": response.data["proposed_action"][1]["id"],
                    "proposed_type": ProposedAction.Action.EARLY_RESPONSE.value,
                    "activities": [
                        {
                            "id": response.data["proposed_action"][1]["activities"][0]["id"],
                            "sector": sct_2.id,
                            "activity": "Seconda activity changed Sector",
                        },
                        {
                            "id": response.data["proposed_action"][1]["activities"][1]["id"],
                            "sector": sct_2.id,
                            "activity": "test activity 2",
                        },
                    ],
                    "total_budget": 5000,
                },
            ],
        }
        response = self.client.patch(url, data, format="json")
        self.assert_200(response)

        self.assertEqual(
            {
                response.data["proposed_action"][0]["id"],
                response.data["proposed_action"][1]["id"],
            },
            {
                data["proposed_action"][0]["id"],
                data["proposed_action"][1]["id"],
            },
        )

        # Check for activity update id should be same
        self.assertEqual(
            {
                response.data["proposed_action"][0]["activities"][0]["id"],
                response.data["proposed_action"][0]["activities"][1]["id"],
            },
            {
                data["proposed_action"][0]["activities"][0]["id"],
                data["proposed_action"][0]["activities"][1]["id"],
            },
        )

    def test_migrate_operation_timeframe_imminent(self):
        dref_1 = DrefFactory.create(
            title="Test Title 1",
            type_of_dref=Dref.DrefType.IMMINENT,
            date_of_approval="2021-10-10",
            operation_timeframe=1,
            end_date="2021-11-20",
            created_by=self.user,
        )
        dref_2 = DrefFactory.create(
            title="Test Title 2",
            type_of_dref=Dref.DrefType.IMMINENT,
            date_of_approval="2021-10-10",
            operation_timeframe=2,
            end_date="2021-12-30",
            created_by=self.user,
        )
        dref_3 = DrefFactory.create(
            title="Test Title 3",
            type_of_dref=Dref.DrefType.IMMINENT,
            date_of_approval="2021-10-10",
            operation_timeframe=3,
            end_date="2022-01-30",
            created_by=self.user,
        )

        # migrate operation timeframe for dref imminent
        management.call_command("migrate_operation_timeframe_imminent")

        dref_1.refresh_from_db()
        dref_2.refresh_from_db()
        dref_3.refresh_from_db()

        self.assertIsNotNone(dref_1.operation_timeframe_imminent)
        self.assertIsNotNone(dref_2.operation_timeframe_imminent)
        self.assertIsNotNone(dref_3.operation_timeframe_imminent)

        self.assertEqual(
            {
                dref_1.operation_timeframe_imminent,
                dref_2.operation_timeframe_imminent,
                dref_3.operation_timeframe_imminent,
            },
            {
                (dref_1.end_date - dref_1.date_of_approval).days,
                (dref_2.end_date - dref_2.date_of_approval).days,
                (dref_3.end_date - dref_3.date_of_approval).days,
            },
        )

    def test_dref_total_allocation_for_imminent(self):
        sector = SectorFactory.create(title="test sector")
        activity1 = ProposedActionActivitiesFactory.create(
            sector=sector,
            activity="Test activity 1",
        )
        activity2 = ProposedActionActivitiesFactory.create(
            sector=sector,
            activity="Test activity 2",
        )
        proposed_action_1 = ProposedActionFactory.create(
            proposed_type=ProposedAction.Action.EARLY_ACTION,
            total_budget=70000,
        )
        proposed_action_1.activities.set([activity1])
        proposed_action_2 = ProposedActionFactory.create(
            proposed_type=ProposedAction.Action.EARLY_RESPONSE,
            total_budget=5000,
        )
        proposed_action_2.activities.set([activity2])
        dref1 = DrefFactory.create(
            title="Test Title",
            type_of_dref=Dref.DrefType.IMMINENT,
            created_by=self.user,
            status=Dref.Status.APPROVED,
            sub_total_cost=75000,
            indirect_cost=5000,
            total_cost=80000,
        )
        dref1.proposed_action.set([proposed_action_1, proposed_action_2])

        # Create Dref Operational Update
        url = "/api/v2/dref-op-update/"
        data = {
            "dref": dref1.id,
            "starting_language": "en",
        }
        self.authenticate(self.user)
        response = self.client.post(url, data=data)
        self.assert_201(response)
        self.assertEqual(
            {
                response.data["type_of_dref"],
                response.data["dref_allocated_so_far"],
                response.data["total_dref_allocation"],
            },
            {
                Dref.DrefType.IMMINENT,
                dref1.total_cost,
                dref1.total_cost,
            },
        )
        # For Old final Report from Dref imminent
        dref2 = DrefFactory.create(
            title="Test Title",
            type_of_dref=Dref.DrefType.IMMINENT,
            created_by=self.user,
            status=Dref.Status.APPROVED,
            sub_total_cost=75000,
            indirect_cost=5000,
            total_cost=80000,
        )
        dref2.proposed_action.set([proposed_action_1, proposed_action_2])
        url = "/api/v2/dref-final-report/"
        data = {
            "dref": dref2.id,
            "starting_language": "en",
        }
        response = self.client.post(url, data=data)
        self.assert_201(response)
        self.assertEqual(
            response.data["total_dref_allocation"],
            dref2.total_cost,
        )

    def test_dref_operation_imminent_create(self):
        dref = DrefFactory.create(
            title="Test Title",
            type_of_dref=Dref.DrefType.IMMINENT,
            created_by=self.user,
            status=Dref.Status.APPROVED,
        )
        self.country1 = Country.objects.create(name="abc")
        self.district1 = District.objects.create(name="test district1", country=self.country1)
        old_count = DrefOperationalUpdate.objects.count()
        url = "/api/v2/dref-op-update/"
        data = {
            "dref": dref.id,
            "country": self.country1.id,
            "district": [self.district1.id],
            "starting_language": "en",
        }
        self.authenticate(self.user)
        response = self.client.post(url, data=data)
        self.assert_201(response)
        self.assertEqual(DrefOperationalUpdate.objects.count(), old_count + 1)
        # NOTE: Should be same type for existing drefs
        self.assertEqual(response.data["type_of_dref"], Dref.DrefType.IMMINENT)

        # NOTE: New Dref of type IMMINENT with is_dref_imminent_v2
        dref1 = DrefFactory.create(
            title="Test Title",
            type_of_dref=Dref.DrefType.IMMINENT,
            created_by=self.user,
            status=Dref.Status.APPROVED,
            is_dref_imminent_v2=True,
        )
        data = {
            "dref": dref1.id,
            "country": self.country1.id,
            "district": [self.district1.id],
            "starting_language": "en",
        }
        response = self.client.post(url, data=data)
        self.assert_201(response)
        # DrefOperationalUpdate should be of type RESPONSE for new Dref of type IMMINENT with is_dref_imminent_v2
        self.assertEqual(response.data["type_of_dref"], Dref.DrefType.RESPONSE)

    def test_dref_imminent_v2_final_report(self):
        sector = SectorFactory.create(title="test sector")
        activity1 = ProposedActionActivitiesFactory.create(
            sector=sector,
            activity="Test activity 1",
        )
        activity2 = ProposedActionActivitiesFactory.create(
            sector=sector,
            activity="Test activity 2",
        )
        proposed_action_1 = ProposedActionFactory.create(
            proposed_type=ProposedAction.Action.EARLY_ACTION,
            total_budget=70000,
        )
        proposed_action_1.activities.set([activity1])
        proposed_action_2 = ProposedActionFactory.create(
            proposed_type=ProposedAction.Action.EARLY_RESPONSE,
            total_budget=5000,
        )
        proposed_action_2.activities.set([activity2])
        dref1 = DrefFactory.create(
            title="Test Title",
            type_of_dref=Dref.DrefType.IMMINENT,
            created_by=self.user,
            status=Dref.Status.APPROVED,
            is_dref_imminent_v2=True,
            sub_total_cost=75000,
            indirect_cost=5800,
            is_surge_personnel_deployed=True,
            surge_deployment_cost=10000,
            total_cost=90800,
            starting_language="en",
        )
        dref1.proposed_action.set([proposed_action_1, proposed_action_2])
        url = "/api/v2/dref-final-report/"
        data = {
            "dref": dref1.id,
            "starting_language": "en",
        }
        self.authenticate(self.user)
        response = self.client.post(url, data=data)
        self.assert_201(response)
        self.assertTrue(response.data["is_dref_imminent_v2"])

        # Check for the proposed_action
        self.assertEqual(
            dref1.proposed_action.count(),
            len(response.data["proposed_action"]),
        )
        self.assertEqual(
            {
                response.data["sub_total_cost"],
                response.data["indirect_cost"],
                response.data["total_cost"],
                response.data["surge_deployment_expenditure_cost"],
                response.data["indirect_expenditure_cost"],
            },
            {
                dref1.sub_total_cost,
                dref1.indirect_cost,
                dref1.total_cost,
                dref1.surge_deployment_cost,
                dref1.indirect_cost,
            },
        )

        # Update dref final report
        data = {
            "title": "Updated Title",
            "starting_language": "en",
            "modified_at": datetime.now(),
            # Add total_expenditure on the existing proposed_action
            "proposed_action": [
                {
                    "id": response.data["proposed_action"][0]["id"],
                    "total_expenditure": 50000,
                },
                {
                    "id": response.data["proposed_action"][1]["id"],
                    "total_expenditure": 5000,
                },
            ],
            "sub_total_expenditure_cost": 55000,
            "surge_deployment_expenditure_cost": 10000,
            "indirect_expenditure_cost": 5800,
            "total_expenditure_cost": 70800,
        }
        url = f"/api/v2/dref-final-report/{response.data['id']}/"
        response = self.client.patch(url, data=data)
        self.assert_200(response)
        self.assertEqual(
            {
                response.data["title"],
                response.data["sub_total_expenditure_cost"],
                response.data["indirect_expenditure_cost"],
                response.data["total_expenditure_cost"],
            },
            {
                data["title"],
                data["sub_total_expenditure_cost"],
                data["indirect_expenditure_cost"],
                data["total_expenditure_cost"],
            },
        )

        dref2 = DrefFactory.create(
            title="Test Title",
            type_of_dref=Dref.DrefType.IMMINENT,
            created_by=self.user,
            status=Dref.Status.APPROVED,
            is_dref_imminent_v2=True,
            starting_language="en",
        )
        # Create Operational Update for Newly created Dref of type IMMINENT
        DrefOperationalUpdateFactory.create(
            dref=dref2,
            type_of_dref=Dref.DrefType.RESPONSE,
            created_by=self.user,
            status=Dref.Status.APPROVED,
            operational_update_number=1,
        )
        data = {
            "dref": dref2.id,
            "starting_language": "en",
        }
        url = "/api/v2/dref-final-report/"
        response = self.client.post(url, data=data)
        self.assert_201(response)
        self.assertEqual(DrefFinalReport.objects.count(), 2)
        self.assertEqual(response.data["type_of_dref"], Dref.DrefType.RESPONSE)

        # Check for existing Dref of type IMMINENT
        dref3 = DrefFactory.create(
            title="Test Title 2",
            type_of_dref=Dref.DrefType.IMMINENT,
            created_by=self.user,
            status=Dref.Status.APPROVED,
        )
        response = self.client.post(url, data={"dref": dref3.id, "starting_language": "en"})
        self.assert_201(response)

        # Check for existing Dref of type IMMINENT with Operational Update
        dref4 = DrefFactory.create(
            title="Test Title 3",
            type_of_dref=Dref.DrefType.IMMINENT,
            created_by=self.user,
            status=Dref.Status.APPROVED,
        )
        DrefOperationalUpdateFactory.create(
            dref=dref4,
            type_of_dref=Dref.DrefType.IMMINENT,
            created_by=self.user,
            status=Dref.Status.APPROVED,
            operational_update_number=1,
        )
        response = self.client.post(url, data={"dref": dref4.id, "starting_language": "en"})
        self.assert_201(response)
        self.assertEqual(response.data["type_of_dref"], Dref.DrefType.IMMINENT)

        # Update existing dref final report
        url = f"/api/v2/dref-final-report/{response.data['id']}/"
        data = {
            "title": "Old Title",
            "modified_at": datetime.now(),
            "starting_language": "en",
        }
        response = self.client.patch(url, data=data)
        self.assert_200(response)
        self.assertEqual(
            {
                response.data["title"],
                response.data["type_of_dref"],
                response.data["is_dref_imminent_v2"],
            },
            {
                data["title"],
                Dref.DrefType.IMMINENT,
                False,  # is_dref_imminent_v2 should be False for existing Dref of type IMMINENT
            },
        )

    def test_create_and_update_final_report(self):
        user1, user2 = UserFactory.create_batch(2)
        dref = DrefFactory.create(
            title="Test Title",
            created_by=self.user,
            status=Dref.Status.DRAFT,
            type_of_dref=Dref.DrefType.ASSESSMENT,
            starting_language="en",
        )
        dref2 = DrefFactory.create(
            title="لعنوان بالعربية",
            created_by=self.user,
            status=Dref.Status.APPROVED,
            type_of_dref=Dref.DrefType.IMMINENT,
            starting_language="ar",
        )
        dref3 = DrefFactory.create(
            title="Título en español",
            created_by=self.user,
            status=Dref.Status.APPROVED,
            type_of_dref=Dref.DrefType.IMMINENT,
            starting_language="es",
        )
        dref.users.add(user1)
        url = "/api/v2/dref-final-report/"
        data2 = {
            "dref": dref2.id,
            "starting_language": "fr",
        }

        self.authenticate(self.user)
        response = self.client.post(url, data=data2)
        self.assert_400(response)

        url = "/api/v2/dref-final-report/"
        # Test create final report for draft dref status
        data1 = {"dref": dref.id, "starting_language": "en"}
        response = self.client.post(url, data=data1)
        self.assert_400(response)

        # Test create final report with original language other than dref original language
        data2 = {"dref": dref2.id, "starting_language": "es"}
        response = self.client.post(url, data=data2)
        self.assert_400(response)

        # Test create final report with approved dref status and matching with dref original language
        data3 = {"dref": dref3.id, "starting_language": "es"}
        response = self.client.post(url, data=data3, HTTP_ACCEPT_LANGUAGE="es")
        self.assert_201(response)
        self.assertEqual(response.data["translation_module_original_language"], "es")
        final_report_id = response.data["id"]

        # Test Update
        update_url = f"/api/v2/dref-final-report/{final_report_id}/"
        data_ar = {"title": "العنوان بالعربية", "modified_at": datetime.now(), "starting_language": "ar"}
        response = self.client.patch(update_url, data=data_ar, HTTP_ACCEPT_LANGUAGE="ar")
        self.assert_400(response)

        # Update in English
        data_en = {"title": "Updated title in English", "modified_at": datetime.now(), "starting_language": "en"}
        response = self.client.patch(update_url, data=data_en, HTTP_ACCEPT_LANGUAGE="en")
        self.assert_400(response)

        # Update in French
        data_fr = {"title": "Titre en français", "modified_at": datetime.now(), "starting_language": "ar"}
        response = self.client.patch(update_url, data=data_fr, HTTP_ACCEPT_LANGUAGE="ar")
        self.assert_400(response)

        # Update in Spanish (original language)
        data_es = {"title": "Título en español", "modified_at": datetime.now(), "starting_language": "es"}
        response = self.client.patch(update_url, data=data_es, HTTP_ACCEPT_LANGUAGE="es")
        self.assert_200(response)
        self.assertEqual(response.data["translation_module_original_language"], "es")
        self.assertEqual(response.data["title"], "Título en español")

    @patch("dref.views.transaction.on_commit", lambda func: func())
    @patch("dref.views.process_dref_translation")
    def test_dref_final_report_finalize(self, mock_translation):
        region = Region.objects.create(name=RegionName.EUROPE)
        country = Country.objects.create(name="Test country12", region=region)
        user1, user2 = UserFactory.create_batch(2)
        dref = DrefFactory.create(
            title="Test Title",
            created_by=user1,
            status=Dref.Status.APPROVED,
            translation_module_original_language="en",
        )
        dref2 = DrefFactory.create(
            title="Test Title2",
            created_by=user1,
            status=Dref.Status.APPROVED,
            translation_module_original_language="en",
        )
        dref.users.add(user1)

        final_report = DrefFinalReportFactory(
            title="Título en español",
            dref=dref,
            country=country,
            type_of_dref=Dref.DrefType.RESPONSE,
            status=Dref.Status.DRAFT,
            translation_module_original_language="es",
        )
        final_report2 = DrefFinalReportFactory(
            title="Título en inglés",
            dref=dref2,
            country=country,
            type_of_dref=Dref.DrefType.RESPONSE,
            status=Dref.Status.DRAFT,
            translation_module_original_language="en",
        )

        self.client.force_authenticate(user1)
        url = f"/api/v2/dref-final-report/{final_report.id}/"

        # Update in Spanish (original language)
        data_es = {"title": "Título en español", "modified_at": datetime.now()}
        response = self.client.patch(url, data=data_es, HTTP_ACCEPT_LANGUAGE="es")
        self.assert_200(response)
        self.assertEqual(response.data["title"], "Título en español")
        self.assertEqual(response.data["translation_module_original_language"], "es")

        # Finalize final report
        finalize_url = f"/api/v2/dref-final-report/{final_report.id}/finalize/"
        response = self.client.post(finalize_url)

        model_name = get_model_name(type(final_report))
        mock_translation.delay.assert_called_once_with(model_name, final_report.pk)

        final_report.refresh_from_db()
        self.assert_202(response)

        # Finalize English-language report (no translation)
        finalize_url = f"/api/v2/dref-final-report/{final_report2.id}/finalize/"
        response = self.client.post(finalize_url)
        self.assert_200(response)
        self.assertEqual(response.data["status"], Dref.Status.FINALIZED)


User = get_user_model()


class Dref3ViewSetTests(APITestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser("admin", "admin@example.com", "password")
        self.user = User.objects.create_user("user", "user@example.com", "password")
        self.url = "/api/v2/dref3/"

    def test_superuser_can_access_list(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_normal_user_can_access_list_also(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        # self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # New decision: normal users can access but see fewer records
        self.assertEqual(response.status_code, status.HTTP_200_OK)
