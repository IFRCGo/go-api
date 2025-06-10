import os
from datetime import datetime, timedelta
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core import management

from api.models import Country, DisasterType, District, Region, RegionName
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
            "status": Dref.Status.IN_PROGRESS.value,
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
            "needs_identified": [{"title": "shelter_housing_and_settlements", "description": "hey"}],
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
                {
                    "id": 2,
                    "title": "health",
                    "description": "matrix reloaded",
                    "budget": 451111111,
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

    def test_event_date_in_dref(self):
        """
        Test for the event date based on type_of_onset
        """
        national_society = Country.objects.create(name="xzz")
        data = {
            "title": "Dref test title",
            "type_of_onset": Dref.OnsetType.SLOW.value,
            "disaster_category": Dref.DisasterCategory.YELLOW.value,
            "status": Dref.Status.IN_PROGRESS.value,
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
        dref = DrefFactory.create(created_by=self.user)
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
        DrefFactory.create(title="test", status=Dref.Status.COMPLETED, date_of_approval="2020-10-10", created_by=self.user)
        DrefFactory.create(status=Dref.Status.COMPLETED, date_of_approval="2020-10-10", created_by=self.user)
        DrefFactory.create(status=Dref.Status.COMPLETED, date_of_approval="2020-10-10", created_by=self.user)
        DrefFactory.create(status=Dref.Status.IN_PROGRESS, created_by=self.user)
        DrefFactory.create(status=Dref.Status.IN_PROGRESS, created_by=self.user)

        # filter by `In Progress`
        url = f"/api/v2/dref/?status={Dref.Status.IN_PROGRESS.value}"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 5)

    def test_dref_country_filter(self):
        country1 = Country.objects.create(name="country1")
        country2 = Country.objects.create(name="country2")
        DrefFactory.create(title="test", status=Dref.Status.COMPLETED, created_by=self.user, country=country1)
        DrefFactory.create(status=Dref.Status.COMPLETED, created_by=self.user)
        DrefFactory.create(status=Dref.Status.COMPLETED, created_by=self.user, country=country2)
        DrefFactory.create(status=Dref.Status.IN_PROGRESS, created_by=self.user, country=country1)
        DrefFactory.create(status=Dref.Status.IN_PROGRESS, created_by=self.user)
        url = f"/api/v2/dref/?country={country1.id}"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    @mock.patch("django.utils.timezone.now")
    def test_dref_is_published(self, mock_now):
        """
        Test for dref if is_published = True
        """

        initial_now = datetime.now()
        mock_now.return_value = initial_now

        region = Region.objects.create(name=RegionName.AFRICA)
        country = Country.objects.create(name="country1", region=region)
        dref = DrefFactory.create(
            title="test",
            created_by=self.user,
            is_published=False,
            type_of_dref=Dref.DrefType.IMMINENT,
        )
        url = f"/api/v2/dref/{dref.id}/"
        data = {
            "title": "New Update Title",
            "modified_at": initial_now + timedelta(days=1),
        }
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, data)
        self.assert_200(response)

        # create new dref with is_published = False
        not_published_dref = DrefFactory.create(
            title="test",
            created_by=self.user,
            country=country,
        )
        url = f"/api/v2/dref/{not_published_dref.id}/"
        self.client.force_authenticate(self.user)
        data["modified_at"] = initial_now + timedelta(days=10)
        response = self.client.patch(url, data)
        self.assert_200(response)

        data["modified_at"] = initial_now - timedelta(seconds=10)
        response = self.client.patch(url, data)
        self.assert_400(response)

        # test dref published endpoint
        url = f"/api/v2/dref/{not_published_dref.id}/publish/"
        data = {}
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data)
        self.assert_403(response)

        # add permission to request user
        self.dref_permission = Permission.objects.create(
            codename="dref_region_admin_0",
            content_type=ContentType.objects.get_for_model(Region),
            name="Dref Admin for 0",
        )
        self.user.user_permissions.add(self.dref_permission)
        response = self.client.post(url, data)
        self.assert_200(response)
        self.assertEqual(response.data["is_published"], True)

    def test_dref_operation_update_create(self):
        """
        Test create dref operation update
        """
        user1, _ = UserFactory.create_batch(2)
        dref = DrefFactory.create(
            title="Test Title",
            created_by=self.user,
            is_published=True,
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
            is_published=False,
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
            is_published=True,
        )
        dref.users.add(user1)
        DrefOperationalUpdateFactory.create(dref=dref, is_published=True, operational_update_number=1)
        data = {
            "dref": dref.id,
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
            is_published=True,
        )
        dref.users.add(user1)
        DrefOperationalUpdateFactory.create(dref=dref, is_published=False, operational_update_number=1)
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
            is_published=True,
        )
        dref.users.add(user1)
        DrefOperationalUpdateFactory.create(dref=dref, is_published=True, operational_update_number=1)
        url = "/api/v2/dref-op-update/"
        data = {
            "dref": dref.id,
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
            is_published=True,
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
            is_published=True,
            type_of_dref=Dref.DrefType.ASSESSMENT,
        )
        dref.users.add(user1)
        old_count = DrefFinalReport.objects.count()
        url = "/api/v2/dref-final-report/"
        data = {
            "dref": dref.id,
        }
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
            is_published=True,
            type_of_dref=Dref.DrefType.ASSESSMENT,
        )
        dref.users.add(user1)
        operational_update = DrefOperationalUpdateFactory.create(
            dref=dref, title="Operational Update Title", is_published=False, operational_update_number=1
        )
        old_count = DrefFinalReport.objects.count()
        url = "/api/v2/dref-final-report/"
        data = {
            "dref": dref.id,
        }
        self.authenticate(self.user)
        response = self.client.post(url, data=data)
        self.assert_400(response)
        # update the operational_update
        operational_update.is_published = True
        operational_update.save(update_fields=["is_published"])
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
            title="Test Title",
            created_by=user1,
            is_published=True,
            type_of_dref=Dref.DrefType.ASSESSMENT,
        )
        url = "/api/v2/dref-final-report/"
        data = {"dref": dref.id}
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
            created_by=user1,
            is_published=True,
            country=country,
        )
        final_report = DrefFinalReportFactory(
            title="Test title",
            dref=dref,
            country=country,
        )
        final_report.users.set([user1])
        # try to publish this report
        url = f"/api/v2/dref-final-report/{final_report.id}/publish/"
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
        self.assertEqual(response.data["is_published"], True)

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
            "status": Dref.Status.IN_PROGRESS.value,
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
        dref = DrefFactory.create(title="Test Title", created_by=self.user, modified_at=datetime(2022, 4, 18, 2, 29, 39, 793615))
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

    def test_dref_op_update_locking(self):
        user1, _ = UserFactory.create_batch(2)
        dref = DrefFactory.create(
            title="Test Title",
            created_by=user1,
            is_published=True,
        )
        dref.users.add(user1)
        DrefOperationalUpdateFactory.create(dref=dref, is_published=True, operational_update_number=1, modified_at=datetime.now())
        url = "/api/v2/dref-op-update/"
        data = {
            "dref": dref.id,
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
        }
        url = f"/api/v2/dref-op-update/{response_id}/"
        self.authenticate(user=user1)
        response = self.client.patch(url, data)
        self.assert_400(response)

        # with `modified_at` less than instance `modified_at`
        data["modified_at"] = datetime.now() - timedelta(days=2)
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_optimistic_lock_in_final_report(self):
        user1 = UserFactory.create()
        dref = DrefFactory.create(
            title="Test Title",
            created_by=user1,
            is_published=True,
        )
        final_report = DrefFinalReportFactory(
            title="Test title",
            created_by=user1,
            dref=dref,
        )
        url = f"/api/v2/dref-final-report/{final_report.id}/"

        # update data without `modified_at`
        data = {"title": "New Updated Title"}
        self.authenticate(user1)
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
        dref1 = DrefFactory.create(
            title="Test Title",
            created_by=user1,
        )
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
            is_published=True,
        )
        self.country1 = Country.objects.create(name="abc")
        self.district1 = District.objects.create(name="test district1", country=self.country1)
        url = "/api/v2/dref-op-update/"
        data = {
            "dref": dref.id,
            "country": self.country1.id,
            "district": [self.district1.id],
        }
        # authenticate with superuser
        self.authenticate(super_user)
        response = self.client.post(url, data=data)
        self.assert_201(response)

    def test_operational_update_view_permission(self):
        Dref.objects.all().delete()
        user1, user2, user3 = UserFactory.create_batch(3)
        dref = DrefFactory.create(title="Test Title", is_published=True, created_by=user1)
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
        dref = DrefFactory.create(title="Test Title", is_published=True, created_by=user1)
        operational_update = DrefOperationalUpdateFactory.create(dref=dref, operational_update_number=1, created_by=user3)
        operational_update.users.set([user3, user2])
        self.country1 = Country.objects.create(name="abc")
        self.district1 = District.objects.create(name="test district1", country=self.country1)

        # Here user1 is able to see the operational_update
        url = "/api/v2/dref-op-update/"
        self.authenticate(user1)
        response = self.client.get(url)
        self.assert_200(response)

        # create another operational update from corresponding dref
        operation_update2 = DrefOperationalUpdateFactory.create(dref=dref, operational_update_number=2)
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
        dref = DrefFactory.create(title="Test Title", created_by=self.user, is_published=True, type_of_dref=Dref.DrefType.LOAN)
        dref.users.add(user1)
        old_count = DrefFinalReport.objects.count()
        url = "/api/v2/dref-final-report/"
        data = {
            "dref": dref.id,
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
        DrefFinalReportFactory.create(is_published=True, country=country_1, type_of_dref=Dref.DrefType.ASSESSMENT)
        DrefFinalReportFactory.create(is_published=True, country=country_3, type_of_dref=Dref.DrefType.ASSESSMENT)
        final_report_1, final_report_2 = DrefFinalReportFactory.create_batch(
            2, is_published=True, country=country_2, type_of_dref=Dref.DrefType.LOAN
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
            is_published=False, country=country_1, type_of_dref=Dref.DrefType.ASSESSMENT, dref=dref_1, created_by=self.root_user
        )
        DrefFinalReportFactory.create(
            is_published=False, country=country_2, type_of_dref=Dref.DrefType.LOAN, dref=dref_2, created_by=self.root_user
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
            "status": Dref.Status.IN_PROGRESS.value,
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
            is_published=True,
            sub_total_cost=75000,
            indirect_cost=5000,
            total_cost=80000,
        )
        dref1.proposed_action.set([proposed_action_1, proposed_action_2])

        # Create Dref Operational Update
        url = "/api/v2/dref-op-update/"
        data = {
            "dref": dref1.id,
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
                Dref.DrefType.RESPONSE,
                dref1.total_cost,
                dref1.total_cost,
            },
        )
        # For Old final Report from Dref imminent
        dref2 = DrefFactory.create(
            title="Test Title",
            type_of_dref=Dref.DrefType.IMMINENT,
            created_by=self.user,
            is_published=True,
            sub_total_cost=75000,
            indirect_cost=5000,
            total_cost=80000,
        )
        dref2.proposed_action.set([proposed_action_1, proposed_action_2])
        url = "/api/v2/dref-final-report/"
        data = {
            "dref": dref2.id,
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
            is_published=True,
        )
        self.country1 = Country.objects.create(name="abc")
        self.district1 = District.objects.create(name="test district1", country=self.country1)
        old_count = DrefOperationalUpdate.objects.count()
        url = "/api/v2/dref-op-update/"
        data = {
            "dref": dref.id,
            "country": self.country1.id,
            "district": [self.district1.id],
        }
        self.authenticate(self.user)
        response = self.client.post(url, data=data)
        self.assert_201(response)
        self.assertEqual(DrefOperationalUpdate.objects.count(), old_count + 1)
        # DrefOperational
        # Check if the type of dref on DrefOperationalUpdate is RESPONSE
        self.assertEqual(response.data["type_of_dref"], Dref.DrefType.RESPONSE)

    def test_dref_imminent_v2_final_report(self):
        dref1 = DrefFactory.create(
            title="Test Title",
            type_of_dref=Dref.DrefType.IMMINENT,
            created_by=self.user,
            is_published=True,
            is_dref_imminent_v2=True,
        )
        url = "/api/v2/dref-final-report/"
        data = {
            "dref": dref1.id,
        }
        self.authenticate(self.user)
        response = self.client.post(url, data=data)
        self.assert_400(response)

        # Create Operational Update for Newly created Dref of type IMMINENT
        DrefOperationalUpdateFactory.create(
            dref=dref1,
            type_of_dref=Dref.DrefType.RESPONSE,
            created_by=self.user,
            is_published=True,
            operational_update_number=1,
        )
        # Now create Final Report for the same Dref
        response = self.client.post(url, data=data)
        self.assert_201(response)
        self.assertEqual(DrefFinalReport.objects.count(), 1)
        self.assertEqual(response.data["type_of_dref"], Dref.DrefType.RESPONSE)

        # Check for existing Dref of type IMMINENT
        dref2 = DrefFactory.create(
            title="Test Title 2",
            type_of_dref=Dref.DrefType.IMMINENT,
            created_by=self.user,
            is_published=True,
        )
        response = self.client.post(url, data={"dref": dref2.id})
        self.assert_201(response)

        # Check for existing Dref of type IMMINENT with Operational Update
        dref3 = DrefFactory.create(
            title="Test Title 3",
            type_of_dref=Dref.DrefType.IMMINENT,
            created_by=self.user,
            is_published=True,
        )
        DrefOperationalUpdateFactory.create(
            dref=dref3,
            type_of_dref=Dref.DrefType.IMMINENT,
            created_by=self.user,
            is_published=True,
            operational_update_number=1,
        )
        response = self.client.post(url, data={"dref": dref3.id})
        self.assert_201(response)
        self.assertEqual(response.data["type_of_dref"], Dref.DrefType.IMMINENT)
