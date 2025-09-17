import re
import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

import api.models as models
from api.factories.event import (
    AppealFactory,
    AppealType,
    EventFactory,
    EventFeaturedDocumentFactory,
    EventLinkFactory,
)
from api.factories.field_report import FieldReportFactory
from api.models import Profile, VisibilityChoices
from deployments.factories.user import UserFactory
from dref.models import DrefFile
from main.test_case import APITestCase


class AuthPowerBITest(APITestCase):
    def setUp(self):
        self.url = reverse("auth_power_bi")

    def test_not_authenticated_returns_401(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 401)
        self.assertIn("error_code", resp.json())

    def test_authenticated_returns_ok(self):
        user = User.objects.create_user(username="alice", password="pass1234")
        # self.client.login(username="alice", password="pass1234")  # session auth, if needed in the future
        # Use token authentication instead of session auth
        self.authenticate(user=user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("detail"), "ok")
        self.assertEqual(data.get("user"), user.username)

    def test_authenticated_returns_mock_values_shape(self):
        user = User.objects.create_user(username="bob", password="pass1234")
        self.assertEqual("bob", user.username)
        # Use token authentication instead of session auth
        self.authenticate(user=user)

        # Force mock path regardless of settings by returning no MI token
        with patch("api.views._pbi_token_via_managed_identity", return_value=None):
            resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # embed_token: 16 hex chars
        self.assertIsInstance(data.get("embed_token"), str)
        self.assertTrue(re.fullmatch(r"[0-9a-f]{16}", data["embed_token"]))
        # embed_url: 10-char random string
        self.assertIsInstance(data.get("embed_url"), str)
        self.assertEqual(len(data["embed_url"]), 10)
        # report_id: positive int
        self.assertIsInstance(data.get("report_id"), int)
        self.assertGreater(data["report_id"], 0)

    def test_authenticated_powerbi_values_when_configured(self):
        user = User.objects.create_user(username="carol", password="pass1234")
        self.assertEqual("carol", user.username)
        # Use token authentication instead of session auth
        self.authenticate(user=user)

        expected = {
            "embed_url": "https://app.powerbi.com/reportEmbed?reportId=rep-123",
            "report_id": "rep-123",
            "embed_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  # dummy string
            "expires_at": "2099-01-01T00:00:00Z",
        }

        with override_settings(POWERBI_WORKSPACE_ID="ws-abc"):
            with (
                patch("api.views._pbi_token_via_managed_identity", return_value="access-token") as p_token,
                patch(
                    "api.views._pbi_get_embed_info",
                    return_value=(expected["embed_url"], expected["report_id"], expected["embed_token"], expected["expires_at"]),
                ) as p_info,
            ):
                # Pass report_id via query parameter per new behavior
                resp = self.client.get(f"{self.url}?report_id={expected['report_id']}")

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("embed_url"), expected["embed_url"])
        self.assertEqual(data.get("report_id"), expected["report_id"])
        self.assertEqual(data.get("embed_token"), expected["embed_token"])
        self.assertEqual(data.get("user"), "carol")
        # helpers were called
        p_token.assert_called_once()
        p_info.assert_called_once_with("access-token", "ws-abc", expected["report_id"])


class SecureFileFieldTest(APITestCase):
    def is_valid_uuid(self, uuid_to_test):
        try:
            # Validate if the directory name is a valid UUID (hex)
            uuid_obj = uuid.UUID(uuid_to_test, version=4)
        except ValueError:
            return False
        return uuid_obj.hex == uuid_to_test

    def test_filefield_uuid_directory_and_filename(self):
        # Mocking a file upload with SimpleUploadedFile
        original_filename = "test_file.txt"
        mock_file = SimpleUploadedFile(original_filename, b"file_content", content_type="text/plain")
        # Create an instance of MyModel and save it with the mocked file
        instance = DrefFile.objects.create(file=mock_file)
        # Check the uploaded file name
        uploaded_file_name = instance.file.name
        # Example output: uploads/5f9d54c8b5a34d3e8fdc4e4f43e2f82a/test_file.txt

        # Extract UUID directory part and filename part
        directory_name, file_name = uploaded_file_name.split("/")[-2:]
        # Check that the directory name is a valid UUID (hexadecimal)
        self.assertTrue(self.is_valid_uuid(directory_name))
        # Check that the file name retains the original name
        self.assertEqual(file_name, original_filename)


class GuestUserPermissionTest(APITestCase):
    def setUp(self):
        # Create guest user
        self.guest_user = User.objects.create(username="guest")
        guest_profile = Profile.objects.get(user=self.guest_user)
        guest_profile.limit_access_to_guest = True
        guest_profile.save()

        # Create go user
        self.go_user = User.objects.create(username="go-user", is_superuser=True, is_staff=True)
        go_user_profile = Profile.objects.get(user=self.go_user)
        go_user_profile.limit_access_to_guest = False
        go_user_profile.save()

        # Create public field reports
        event_pub = EventFactory.create(visibility=VisibilityChoices.PUBLIC, parent_event=None)
        FieldReportFactory.create_batch(4, event=event_pub, visibility=VisibilityChoices.PUBLIC)
        # Create non-public field reports
        event_non_pub = EventFactory.create(visibility=VisibilityChoices.IFRC, parent_event=None)
        FieldReportFactory.create_batch(5, event=event_non_pub, visibility=VisibilityChoices.IFRC)

    def test_guest_user_permission(self):
        body = {}
        id = 1  # NOTE: id is used just to test api that requires id, it doesnot indicate real id. It can be any number.

        guest_apis = [
            "/api/v2/add_subscription/",
            "/api/v2/del_subscription/",
            "/api/v2/external-token/",
        ]
        guest_get_apis = [
            "/api/v2/user/me/",
            "/api/v2/field-report/",
            f"/api/v2/field-report/{id}/",
            "/api/v2/language/",
            f"/api/v2/language/{id}/",
            "/api/v2/event/",
            "/api/v2/ops-learning/",
            f"/api/v2/ops-learning/{id}/",
        ]

        go_post_apis = [
            "/api/v2/dref/",
            "/api/v2/dref-final-report/",
            f"/api/v2/dref-final-report/{id}/approve/",
            "/api/v2/dref-op-update/",
            f"/api/v2/dref-op-update/{id}/approve/",
            "/api/v2/dref-share/",
            f"/api/v2/dref/{id}/approve/",
            "/api/v2/flash-update/",
            "/api/v2/flash-update-file/multiple/",
            "/api/v2/local-units/",
            f"/api/v2/local-units/{id}/validate/",
            "/api/v2/pdf-export/",
            "/api/v2/per-assessment/",
            "/api/v2/per-document-upload/",
            "/api/v2/per-file/multiple/",
            "/api/v2/per-prioritization/",
            "/api/v2/per-work-plan/",
            "/api/v2/ops-learning/",
            "/api/v2/project/",
            "/api/v2/dref-files/",
            "/api/v2/dref-files/multiple/",
            "/api/v2/field-report/",
            "/api/v2/flash-update-file/",
            "/api/v2/per-file/",
            "/api/v2/share-flash-update/",
            "/api/v2/add_cronjob_log/",
            "/api/v2/profile/",
            "/api/v2/subscription/",
            "/api/v2/user/",
        ]

        get_apis = [
            "/api/v2/dref/",
            "/api/v2/dref-files/",
            "/api/v2/dref-final-report/",
            f"/api/v2/dref-final-report/{id}/",
            "/api/v2/dref-op-update/",
            f"/api/v2/dref/{id}/",
            "/api/v2/flash-update/",
            "/api/v2/flash-update-file/",
            f"/api/v2/flash-update/{id}/",
            "/api/v2/local-units/",
            f"/api/v2/local-units/{id}/",
            f"/api/v2/pdf-export/{id}/",
            "/api/v2/per-assessment/",
            f"/api/v2/per-assessment/{id}/",
            "/api/v2/per-document-upload/",
            f"/api/v2/per-document-upload/{id}/",
            "/api/v2/per-file/",
            "/api/v2/per-overview/",
            f"/api/v2/per-overview/{id}/",
            "/api/v2/per-prioritization/",
            f"/api/v2/per-prioritization/{id}/",
            "/api/v2/per-work-plan/",
            f"/api/v2/per-work-plan/{id}/",
            "/api/v2/profile/",
            f"/api/v2/profile/{id}/",
            f"/api/v2/share-flash-update/{id}/",
            "/api/v2/subscription/",
            f"/api/v2/subscription/{id}/",
            "/api/v2/users/",
            f"/api/v2/users/{id}/",
            "/api/v2/per-stats/",
            "/api/v2/per-options/",
            "/api/v2/per-process-status/",
            "/api/v2/aggregated-per-process-status/",
            "/api/v2/completed-dref/",
            "/api/v2/active-dref/",
            "/api/v2/dref-share-user/",
            "/api/v2/personnel_deployment/",
            f"/api/v2/delegation-office/{id}/",
            # Exports
            f"/api/v2/export-flash-update/{1}/",
        ]

        # NOTE: With custom Content Negotiation: Look for main.utils.SpreadSheetContentNegotiation
        get_custom_negotiation_apis = [
            f"/api/v2/export-per/{1}/",
        ]

        go_post_apis_req_additional_perm = [
            "/api/v2/per-overview/",
            f"/api/v2/user/{id}/accepted_license_terms/",
        ]

        def _success_check(response):  # NOTE: Only handles json responses
            self.assertNotIn(response.status_code, [401, 403], response.content)
            self.assertNotIn(response.json().get("error_code"), [401, 403], response.content)

        def _failure_check(response, check_json_error_code=True):
            self.assertIn(response.status_code, [401, 403], response.content)
            if check_json_error_code:
                self.assertIn(response.json()["error_code"], [401, 403], response.content)

        # check for unauthenticated user
        # Unauthenticated user should be able to view public field reports
        field_report_pub_response = self.client.get("/api/v2/field-report/")
        _success_check(field_report_pub_response)
        self.assertEqual(len(field_report_pub_response.json()["results"]), 4)

        # Unauthenticated user should be not be able to do post operations in field reports
        field_report_pub_response = self.client.post("/api/v2/field-report/", json=body)
        _failure_check(field_report_pub_response, check_json_error_code=False)

        # Unauthenticated user should be able to view public events
        event_pub_response = self.client.get("/api/v2/event/")
        _success_check(event_pub_response)
        self.assertEqual(len(event_pub_response.json()["results"]), 1)

        # Unauthenticated user should be able to view operational learning
        ops_learning_response = self.client.get("/api/v2/ops-learning/")
        _success_check(ops_learning_response)

        # Unauthenticated user should not be able to do post operations in operational learning
        ops_learning_response = self.client.post("/api/v2/ops-learning/", json=body)
        _failure_check(ops_learning_response, check_json_error_code=False)

        # authenticate guest user
        self.authenticate(user=self.guest_user)

        for api_url in get_custom_negotiation_apis:
            headers = {
                "Accept": "text/html",
            }
            response = self.client.get(api_url, headers=headers, stream=True)
            _failure_check(response, check_json_error_code=False)

        # # Guest user should not be able to access get apis that requires IsAuthenticated permission
        for api_url in get_apis:
            response = self.client.get(api_url)
            _failure_check(response)

        # # Guest user should not be able to hit post apis.
        for api_url in go_post_apis + go_post_apis_req_additional_perm:
            response = self.client.post(api_url, json=body)
            _failure_check(response)

        # Guest user should be able to access guest post apis
        for api_url in guest_apis:
            response = self.client.post(api_url, json=body)
            _success_check(response)

        # Guest user should be able to access guest get apis
        for api_url in guest_get_apis:
            response = self.client.get(api_url)
            _success_check(response)

        # Guest user should be able to view only public field reports
        field_report_pub_response = self.client.get("/api/v2/field-report/")
        _success_check(field_report_pub_response)
        self.assertEqual(len(field_report_pub_response.json()["results"]), 4)

        # Guest user should be able to view public events
        event_pub_response = self.client.get("/api/v2/event/")
        _success_check(event_pub_response)
        self.assertEqual(len(event_pub_response.json()["results"]), 1)

        # authenticate ifrc go user
        # Go user should be able to access go_post_apis
        self.authenticate(user=self.go_user)
        for api_url in go_post_apis:
            response = self.client.post(api_url, json=body)
            _success_check(response)

        for api_url in get_apis:
            response = self.client.get(api_url)
            _success_check(response)

        # Go user should be able to view both public + non-public field reports
        field_report_response = self.client.get("/api/v2/field-report/")
        _success_check(field_report_response)
        self.assertEqual(len(field_report_response.json()["results"]), 9)

        # Go user should be able to view both public + non-pubic events
        event_response = self.client.get("/api/v2/event/")
        _success_check(event_response)
        self.assertEqual(len(event_response.json()["results"]), 2)


class AuthTokenTest(APITestCase):
    def setUp(self):
        user = User.objects.create(username="jo")
        user.set_password("12345678")
        user.save()

    def test_get_auth(self):
        body = {
            "username": "jo",
            "password": "12345678",
        }
        headers = {"CONTENT_TYPE": "application/json"}
        response = self.client.post("/get_auth_token", body, format="json", headers=headers).json()
        self.assertIsNotNone(response.get("token"))
        self.assertIsNotNone(response.get("expires"))


class EventApiTest(APITestCase):

    def test_event_featured_document_api(self):
        event = EventFactory()
        EventFeaturedDocumentFactory.create_batch(5, event=event)
        resp = self.client.get(f"/api/v2/event/{event.id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["featured_documents"]), 5)

    def test_event_link_api(self):
        event = EventFactory()
        EventLinkFactory.create_batch(5, event=event)
        resp = self.client.get(f"/api/v2/event/{event.id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["links"]), 5)


class SituationReportTypeTest(APITestCase):

    fixtures = ["DisasterTypes"]

    def test_sit_rep_types(self):
        type1 = models.SituationReportType.objects.create(type="Lyric")
        type2 = models.SituationReportType.objects.create(type="Epic")
        dtype1 = models.DisasterType.objects.get(pk=1)
        event1 = models.Event.objects.create(name="disaster1", summary="test disaster1", dtype=dtype1)

        models.SituationReport.objects.create(name="test1", event=event1, type=type1, visibility=3)
        models.SituationReport.objects.create(name="test2", event=event1, type=type2, visibility=3)
        models.SituationReport.objects.create(name="test3", event=event1, type=type2, visibility=3)

        # Filter by event
        response = self.client.get("/api/v2/situation_report/?limit=100&event=%s" % event1.id)
        self.assertEqual(response.status_code, 200)
        count = response.json()["count"]
        self.assertEqual(count, 3)

        # Filter by event and type
        response = self.client.get("/api/v2/situation_report/?limit=100&event=%s&type=%s" % (event1.id, type2.id))
        self.assertEqual(response.status_code, 200)
        count = response.json()["count"]
        self.assertEqual(count, 2)


class FieldReportTest(APITestCase):

    fixtures = ["DisasterTypes", "Actions"]

    def test_create_and_update(self):
        user = UserFactory(username="jo")
        region = models.Region.objects.create(name=1)
        country1 = models.Country.objects.create(name="abc", region=region)
        country2 = models.Country.objects.create(name="xyz")
        source1 = models.SourceType.objects.create(name="source1")
        source2 = models.SourceType.objects.create(name="source2")
        body = {
            "countries": [country1.id, country2.id],
            "dtype": 7,
            "title": "test",
            "description": "this is a test description",
            "bulletin": "3",
            "num_assisted": 100,
            "visibility": models.VisibilityChoices.IFRC,
            "sources": [
                {"stype": source1.id, "spec": "A source"},
                {"stype": source2.id, "spec": "Another source"},
            ],
            "actions_taken": [
                {"organization": "NTLS", "summary": "actions taken", "actions": ["37", "30", "39"]},
            ],
            "dref": "2",
            "appeal": "1",
            "contacts": [{"ctype": "Originator", "name": "jo", "title": "head", "email": "123"}],
            "user": user.id,
        }
        self.client.force_authenticate(user=user)
        response = self.client.post("/api/v2/field-report/", body, format="json").json()
        old_respone_id = response["id"]
        created = models.FieldReport.objects.get(pk=old_respone_id)

        self.assertEqual(created.countries.count(), 2)
        # one region attached automatically
        self.assertEqual(created.regions.count(), 1)

        self.assertEqual(created.sources.count(), 2)
        source_types = list([source.stype.name for source in created.sources.all()])
        self.assertTrue("source1" in source_types)
        self.assertTrue("source2" in source_types)

        self.assertEqual(created.actions_taken.count(), 1)
        actions = list([action.id for action in created.actions_taken.first().actions.all()])
        self.assertTrue(37 in actions)
        self.assertTrue(30 in actions)
        self.assertTrue(39 in actions)

        self.assertEqual(created.contacts.count(), 1)
        self.assertEqual(created.visibility, models.VisibilityChoices.IFRC)
        self.assertEqual(created.dtype.id, 7)
        self.assertEqual(created.title, "test")
        # Translated field test
        self.assertEqual(created.title_en, "test")

        # created an emergency automatically
        self.assertEqual(created.event.name, response["summary"])
        # event_pk = created.event.id

        # body['countries'] = [country2.id]
        # body['summary'] = 'test [updated]'
        # body['sources'] = [
        #     {'stype': source1.id, 'spec': 'something'},
        #     {'stype': source2.id, 'spec': 'other'},
        # ]
        # body['actions_taken'] = []
        # body['visibility'] = models.VisibilityChoices.PUBLIC
        # self.client.force_authenticate(user=user)
        # response = self.client.patch(f'/api/v2/field-report/{old_respone_id}/', body)
        # print(response.content)
        # updated = models.FieldReport.objects.get(pk=old_respone_id)

        # self.assertEqual(updated.countries.count(), 1)
        # self.assertEqual(updated.countries.first().name, 'xyz')
        # # region automatically removed
        # self.assertEqual(updated.regions.count(), 0)

        # self.assertEqual(updated.sources.count(), 2)
        # source_types = list([source.stype.name for source in updated.sources.all()])
        # self.assertTrue('Vanilla' in source_types)
        # self.assertTrue('Chocolate' in source_types)

        # self.assertEqual(updated.actions_taken.count(), 0)
        # self.assertEqual(updated.contacts.count(), 1)
        # self.assertEqual(updated.visibility, models.VisibilityChoices.PUBLIC)
        # # emergency still attached
        # self.assertEqual(updated.event.id, event_pk)
        # # Translated field test
        # # (Since with with self.capture_on_commit_callbacks(execute=True) is not used so translation has not been triggered)
        # self.assertEqual(updated.summary_en, 'test [updated]')
        # self.assertEqual(updated.description_en, 'this is a test description')
        # self.assertEqual(updated.summary_es, '')  # This has been reset
        # self.assertEqual(
        #     updated.description_es,
        #     self.aws_translator._fake_translation('this is a test description', 'es', 'en'),
        # )  # This has not been reset

        # body['summary'] = 'test [updated again]'
        # with self.capture_on_commit_callbacks(execute=True):
        #     response = self.client.put(f'/api/v2/update_field_report/{created.id}/', body, format='json').json()
        # updated = models.FieldReport.objects.get(pk=response['id'])
        # self.assertEqual(updated.summary_en, 'test [updated again]')
        # self.assertEqual(
        #     updated.summary_es,
        #     self.aws_translator._fake_translation('test [updated again]', 'es', 'en'),
        # )

        # # Check with GET (with different accept-language)
        # for lang, _ in settings.LANGUAGES:
        #     response = self.client.get(f'/api/v2/field_report/{created.id}/', HTTP_ACCEPT_LANGUAGE=lang)
        #     self.assert_200(response)
        #     self.assertEqual(
        #         response.json()['summary'],
        #         self.aws_translator._fake_translation(body['summary'], lang, 'en') if lang != 'en' else body['summary'],
        #     )


class VisibilityTest(APITestCase):
    def test_country_snippet_visibility(self):
        country = models.Country.objects.create(name="1")
        # create membership and IFRC snippets
        models.CountrySnippet.objects.create(country=country, visibility=models.VisibilityChoices.MEMBERSHIP)
        models.CountrySnippet.objects.create(country=country, visibility=models.VisibilityChoices.IFRC)
        response = self.client.get("/api/v2/country_snippet/").json()
        # no snippets available to anonymous user
        self.assertEqual(response["count"], 0)

        # perform the request with an authenticated user
        user = UserFactory(username="foo")
        self.client.force_authenticate(user=user)
        response = self.client.get("/api/v2/country_snippet/").json()
        # one snippets available to anonymous user
        self.assertEqual(response["count"], 1)

        # perform the request with an ifrc user
        user2 = UserFactory(username="bar")
        user2.user_permissions.add(self.ifrc_permission)
        self.client.force_authenticate(user=user2)
        response = self.client.get("/api/v2/country_snippet/").json()
        self.assertEqual(response["count"], 2)

        # perform the request with a superuser
        super_user = UserFactory(username="baz", email="foo@baz.com", password="12345678")
        super_user.is_superuser = True
        super_user.save()

        self.client.force_authenticate(user=super_user)
        response = self.client.get("/api/v2/country_snippet/").json()
        self.assertEqual(response["count"], 2)

        self.client.force_authenticate(user=None)


# class FieldReportsVisibilityTestCase(APITestCase):
#     fixtures = ['DisasterTypes',]
#     def setUp(self):
#         user = User.objects.create(username='foo')
#         User.objects.create_superuser(username='bar', email='foo@bar.com', password='12345678')
#         event = models.Event.objects.create(
#             dtype=models.DisasterType.objects.get(pk=1),
#             name='test event for FRs',
#             disaster_start_date=datetime.now()
#         )
#         models.FieldReport.objects.create(
#             dtype=models.DisasterType.objects.get(pk=1),
#             summary='membership field report',
#             bulletin='3',
#             visibility=1, # MEMBERSHIP
#             dref='2',
#             user=user,
#             event_id=event.id,
#         )
#         models.FieldReport.objects.create(
#             dtype=models.DisasterType.objects.get(pk=1),
#             summary='ifrc field report',
#             bulletin='3',
#             visibility=2, # IFRC
#             dref='2',
#             user=user,
#             event_id=event.id,
#         )
#         models.FieldReport.objects.create(
#             dtype=models.DisasterType.objects.get(pk=1),
#             summary='public field report',
#             bulletin='3',
#             visibility=3, # PUBLIC
#             dref='2',
#             user=user,
#             event_id=event.id,
#         )

#     def test_field_reports_visibility(self):
#         user = User.objects.get(username='foo')
#         user2 = User.objects.get(username='bar')

#         # perform the request without a user
#         # this user should see FRs with PUBLIC visibility
#         response = self.client.get('/api/v2/event/6').json()

#         self.assertEqual(len(response['field_reports']), 1)
#         self.assertEqual(response['field_reports'][0]['summary'], 'public field report')

#         # perform the request with an authenticated user
#         # this user should see FRs with MEMBERSHIP and PUBLIC visibility
#         self.client.force_authenticate(user=user)
#         response = self.client.get('/api/v2/event/6').json()

#         self.assertEqual(len(response['field_reports']), 2)

#         # perform the request with a superuser
#         # this user should see all FRs
#         self.client.force_authenticate(user=user2)
#         response = self.client.get('/api/v2/event/6').json()

#         self.assertEqual(len(response['field_reports']), 3)


class ActionTestCase(APITestCase):

    def test_action_api(self):
        EVENT = models.ActionType.EVENT
        EARLY_WARNING = models.ActionType.EARLY_WARNING
        NTLS = models.ActionOrg.NATIONAL_SOCIETY
        PNS = models.ActionOrg.FOREIGN_SOCIETY

        models.Action.objects.create(name="Test1", field_report_types=[EVENT, EARLY_WARNING], organizations=[NTLS, PNS])
        models.Action.objects.create(name="Test2", field_report_types=[EARLY_WARNING], organizations=[])
        response = self.client.get("/api/v2/action/").json()
        self.assertEqual(response["count"], 2)
        res1 = response["results"][0]
        self.assertEqual(res1["name"], "Test1")
        self.assertEqual(res1["field_report_types"], [EVENT, EARLY_WARNING])
        self.assertEqual(res1["organizations"], [NTLS, PNS])
        res2 = response["results"][1]
        self.assertEqual(res2["organizations"], [])
        self.assertEqual(res2["field_report_types"], [EARLY_WARNING])


class HistoricalEventTest(APITestCase):

    fixtures = ["DisasterTypes"]

    def test_historical_events(self):
        region1 = models.Region.objects.create(name=1)
        region2 = models.Region.objects.create(name=2)
        country1 = models.Country.objects.create(name="Nepal", iso3="NPL", region=region1)
        country2 = models.Country.objects.create(name="India", iso3="IND", region=region2)
        dtype1 = models.DisasterType.objects.get(pk=1)
        dtype2 = models.DisasterType.objects.get(pk=2)
        EventFactory.create(
            name="test1",
            dtype=dtype1,
        )
        event1 = EventFactory.create(name="test0", dtype=dtype1, num_affected=10000, countries=[country1])
        event2 = EventFactory.create(name="test2", dtype=dtype2, num_affected=99999, countries=[country2])
        event3 = EventFactory.create(name="test2", dtype=dtype2, num_affected=None, countries=[country2])
        appeal1 = AppealFactory.create(
            event=event1, dtype=dtype1, num_beneficiaries=9000, amount_requested=10000, amount_funded=1899999
        )
        AppealFactory.create(event=event2, dtype=dtype2, num_beneficiaries=90023, amount_requested=100440, amount_funded=12299999)
        AppealFactory.create(event=event3, dtype=dtype2, num_beneficiaries=91000, amount_requested=10000888, amount_funded=678888)
        response = self.client.get("/api/v2/go-historical/").json()
        self.assertEqual(response["count"], 3)  # should give event that have appeal associated with and num_affected=null
        self.assertEqual(sorted([event1.id, event2.id, event3.id]), sorted([data["id"] for data in response["results"]]))

        # test for filter by country iso3
        response = self.client.get(f"/api/v2/go-historical/?iso3={country1.iso3}").json()
        self.assertEqual(response["count"], 1)
        self.assertEqual(response["results"][0]["id"], event1.id)
        self.assertEqual(response["results"][0]["appeals"][0]["id"], appeal1.id)

        # test for region filter by
        response = self.client.get(f"/api/v2/go-historical/?region={region1.id}").json()
        self.assertEqual(response["count"], 1)
        self.assertEqual(response["results"][0]["id"], event1.id)


class Admin2Test(APITestCase):

    def test_admin2_api(self):
        region = models.Region.objects.create(name=1)
        country = models.Country.objects.create(name="Nepal", iso3="NPL", region=region)
        admin1_1 = models.District.objects.create(name="admin1 1", code="NPL01", country=country)
        admin1_2 = models.District.objects.create(name="admin1 2", code="NPL02", country=country)
        models.Admin2.objects.create(name="test 1", admin1=admin1_1, code="1")
        models.Admin2.objects.create(name="test 2", admin1=admin1_2, code="2")

        # test fetching all admin2-s
        response = self.client.get("/api/v2/admin2/").json()
        self.assertEqual(response["count"], 2)

        # test filtering by district
        response = self.client.get(f"/api/v2/admin2/?admin1={admin1_1.id}").json()
        self.assertEqual(response["count"], 1)
        self.assertEqual(response["results"][0]["name"], "test 1")

    def test_admin2_deprecation(self):
        region = models.Region.objects.create(name=1)
        country = models.Country.objects.create(name="Nepal", iso3="NPL", region=region)
        admin1_1 = models.District.objects.create(name="admin1 1", code="NPL01", country=country)
        admin1_2 = models.District.objects.create(name="admin1 2", code="NPL02", country=country)
        admin2_1 = models.Admin2.objects.create(name="test 1", admin1=admin1_1, code="1")
        admin2_2 = models.Admin2.objects.create(name="test 2", admin1=admin1_2, code="2")
        admin2_3 = models.Admin2.objects.create(name="test 3", admin1=admin1_2, code="3")

        # test fetching all admin2-s
        response = self.client.get("/api/v2/admin2/").json()
        self.assertEqual(response["count"], 3)

        admin2_2.is_deprecated = True
        admin2_2.save()
        response = self.client.get("/api/v2/admin2/").json()
        # 2 instead of 3, because 1 admin2 area became deprecated: api does not show it.
        self.assertEqual(response["count"], 2)

        # Tear down
        admin2_2.is_deprecated = False
        admin2_2.save()
        response = self.client.get("/api/v2/admin2/").json()
        self.assertEqual(response["count"], 3)

        admin2_1.is_deprecated = True
        admin2_2.is_deprecated = True
        admin2_1.save()
        admin2_2.save()
        # 2 admin2-s are deprecated, so 3-2 = 1
        response = self.client.get("/api/v2/admin2/").json()
        self.assertEqual(response["count"], 1)

        # Tear down
        admin2_1.is_deprecated = False
        admin2_2.is_deprecated = False
        admin2_1.save()
        admin2_2.save()
        response = self.client.get("/api/v2/admin2/").json()
        self.assertEqual(response["count"], 3)

        admin2_1.is_deprecated = True
        admin2_2.is_deprecated = True
        admin2_3.is_deprecated = True
        admin2_1.save()
        admin2_2.save()
        admin2_3.save()
        # All admin2-s are deprecated
        response = self.client.get("/api/v2/admin2/").json()
        self.assertEqual(response["count"], 0)

        # Tear down
        admin2_1.is_deprecated = False
        admin2_2.is_deprecated = False
        admin2_3.is_deprecated = False
        admin2_1.save()
        admin2_2.save()
        admin2_3.save()
        response = self.client.get("/api/v2/admin2/").json()
        self.assertEqual(response["count"], 3)

        admin1_2.is_deprecated = True
        admin1_2.save()
        response = self.client.get("/api/v2/admin2/").json()
        # There are 2 admin2-s in this district, so 3-2 = 1
        self.assertEqual(response["count"], 1)

        # Tear down
        admin1_2.is_deprecated = False
        admin1_2.save()
        response = self.client.get("/api/v2/admin2/").json()
        self.assertEqual(response["count"], 3)

        admin1_1.is_deprecated = True
        admin1_1.save()
        response = self.client.get("/api/v2/admin2/").json()
        # There is only 1 admin2-s in this district, so 3-1 = 2
        self.assertEqual(response["count"], 2)

        # Tear down
        admin1_1.is_deprecated = False
        admin1_1.save()
        response = self.client.get("/api/v2/admin2/").json()
        self.assertEqual(response["count"], 3)

        country.is_deprecated = True
        country.save()
        response = self.client.get("/api/v2/admin2/").json()
        # There are 3 admin2-s in this country, so 3-3 = 0
        self.assertEqual(response["count"], 0)

        # Tear down
        country.is_deprecated = False
        country.save()
        response = self.client.get("/api/v2/admin2/").json()
        self.assertEqual(response["count"], 3)


class DistrictTest(APITestCase):
    def test_district_deprecation(self):
        region = models.Region.objects.create(name=1)
        country = models.Country.objects.create(name="Nepal", iso3="NPL", region=region)
        admin1_1 = models.District.objects.create(name="admin1 1", code="NPL01", country=country)
        admin1_2 = models.District.objects.create(name="admin1 2", code="NPL02", country=country)

        # test fetching all districts
        response = self.client.get("/api/v2/district/").json()
        self.assertEqual(response["count"], 2)

        admin1_2.is_deprecated = True
        admin1_2.save()
        response = self.client.get("/api/v2/district/").json()
        # one district deprecated, 2-1 = 1
        self.assertEqual(response["count"], 1)

        # Tear down
        admin1_2.is_deprecated = False
        admin1_2.save()
        response = self.client.get("/api/v2/district/").json()
        self.assertEqual(response["count"], 2)

        admin1_1.is_deprecated = True
        admin1_2.is_deprecated = True
        admin1_1.save()
        admin1_2.save()
        response = self.client.get("/api/v2/district/").json()
        # two districts deprecated, 2-2 = 0
        self.assertEqual(response["count"], 0)

        # Tear down
        admin1_1.is_deprecated = False
        admin1_2.is_deprecated = False
        admin1_1.save()
        admin1_2.save()
        response = self.client.get("/api/v2/district/").json()
        self.assertEqual(response["count"], 2)

        country.is_deprecated = True
        country.save()
        response = self.client.get("/api/v2/district/").json()
        # There are 2 districts in this country, so 2-2 = 0
        self.assertEqual(response["count"], 0)

        # Tear down
        country.is_deprecated = False
        country.save()
        response = self.client.get("/api/v2/district/").json()
        self.assertEqual(response["count"], 2)


class GlobalEnumEndpointTest(APITestCase):
    def test_200_response(self):
        response = self.client.get("/api/v2/global-enums/")
        self.assert_200(response)
        self.assertIsNotNone(response.json())


class AppealTest(APITestCase):
    fixtures = ["DisasterTypes"]

    def test_appeal_key_figure(self):
        region1 = models.Region.objects.create(name=1)
        region2 = models.Region.objects.create(name=2)
        country1 = models.Country.objects.create(name="Nepal", iso3="NPL", region=region1)
        country2 = models.Country.objects.create(name="India", iso3="IND", region=region2)
        dtype1 = models.DisasterType.objects.get(pk=1)
        dtype2 = models.DisasterType.objects.get(pk=2)
        event1 = EventFactory.create(
            name="test1",
            dtype=dtype1,
        )
        event2 = EventFactory.create(name="test0", dtype=dtype1, num_affected=10000, countries=[country1])
        event3 = EventFactory.create(name="test2", dtype=dtype2, num_affected=99999, countries=[country2])
        AppealFactory.create(
            event=event1,
            dtype=dtype1,
            num_beneficiaries=9000,
            amount_requested=10000,
            amount_funded=1899999,
            code=12,
            start_date="2024-1-1",
            end_date="2024-1-1",
            atype=AppealType.APPEAL,
            country=country1,
        )
        AppealFactory.create(
            event=event2,
            dtype=dtype2,
            num_beneficiaries=90023,
            amount_requested=100440,
            amount_funded=12299999,
            code=123,
            start_date="2024-2-2",
            end_date="2024-2-2",
            atype=AppealType.DREF,
            country=country1,
        )
        AppealFactory.create(
            event=event3,
            dtype=dtype2,
            num_beneficiaries=91000,
            amount_requested=10000888,
            amount_funded=678888,
            code=1234,
            start_date="2024-3-3",
            end_date="2024-3-3",
            atype=AppealType.APPEAL,
            country=country1,
        )
        AppealFactory.create(
            event=event3,
            dtype=dtype2,
            num_beneficiaries=91000,
            amount_requested=10000888,
            amount_funded=678888,
            code=12345,
            start_date="2024-4-4",
            end_date="2024-4-4",
            atype=AppealType.APPEAL,
            country=country1,
        )
        url = f"/api/v2/country/{country1.id}/figure/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assert_200(response)
        self.assertIsNotNone(response.json())
        self.assertEqual(response.data["active_drefs"], 1)
        self.assertEqual(response.data["active_appeals"], 3)


class RegionSnippetVisibilityTest(APITestCase):
    def setUp(self):
        super().setUp()
        # Create a region and countries to support IFRC_NS intersection logic
        self.region = models.Region.objects.create(name=2)
        self.country_public = models.Country.objects.create(name="Publand", iso3="PUB", region=self.region)
        self.country_private = models.Country.objects.create(name="Privland", iso3="PRI", region=self.region)

        # Snippets with different visibilities
        self.snip_public = models.RegionSnippet.objects.create(
            region=self.region,
            snippet="<p>Public snippet</p>",
            visibility=models.VisibilityChoices.PUBLIC,
        )
        self.snip_ifrc = models.RegionSnippet.objects.create(
            region=self.region,
            snippet="<p>IFRC only snippet</p>",
            visibility=models.VisibilityChoices.IFRC,
        )
        self.snip_membership = models.RegionSnippet.objects.create(
            region=self.region,
            snippet="<p>Membership snippet</p>",
            visibility=models.VisibilityChoices.MEMBERSHIP,
        )
        self.snip_ifrc_ns = models.RegionSnippet.objects.create(
            region=self.region,
            snippet="<p>IFRC & NS snippet</p>",
            visibility=models.VisibilityChoices.IFRC_NS,
        )

    def _get_snippet_ids(self, response_json):
        return sorted([s["id"] for s in response_json.get("snippets", [])])

    def test_anonymous_sees_only_public(self):
        resp = self.client.get(f"/api/v2/region/{self.region.id}/")
        self.assertEqual(resp.status_code, 200)
        ids = self._get_snippet_ids(resp.json())
        self.assertEqual(ids, [self.snip_public.id])

    def test_guest_user_sees_only_public(self):
        guest = User.objects.create_user(username="guest", password="x")
        guest.profile.limit_access_to_guest = True
        guest.profile.save()
        self.client.force_authenticate(user=guest)
        resp = self.client.get(f"/api/v2/region/{self.region.id}/")
        self.assertEqual(resp.status_code, 200)
        ids = self._get_snippet_ids(resp.json())
        self.assertEqual(ids, [self.snip_public.id])

    def test_authenticated_non_ifrc_excludes_ifrc(self):
        user = User.objects.create_user(username="regular", password="x")
        self.client.force_authenticate(user=user)
        resp = self.client.get(f"/api/v2/region/{self.region.id}/")
        self.assertEqual(resp.status_code, 200)
        ids = self._get_snippet_ids(resp.json())
        # IFRC (2) excluded; IFRC_NS (4) excluded because no country relation; membership (1) included
        self.assertEqual(sorted(ids), sorted([self.snip_public.id, self.snip_membership.id]))

    def test_authenticated_non_ifrc_with_country_gets_ifrc_ns(self):
        user = User.objects.create_user(username="ns_user", password="x")
        # Attach country relation via Profile (simplest) or UserCountry
        user.profile.country = self.country_public
        user.profile.save()
        self.client.force_authenticate(user=user)
        resp = self.client.get(f"/api/v2/region/{self.region.id}/")
        self.assertEqual(resp.status_code, 200)
        ids = self._get_snippet_ids(resp.json())
        # IFRC only excluded; IFRC_NS now included due to region country intersection
        self.assertEqual(sorted(ids), sorted([self.snip_public.id, self.snip_membership.id, self.snip_ifrc_ns.id]))

    def test_ifrc_user_sees_all(self):
        ifrc_user = User.objects.create_user(username="ifrc_admin", password="x")
        # Grant IFRC permission to classify user as IFRC
        ifrc_user.user_permissions.add(self.ifrc_permission)
        ifrc_user.save()
        self.client.force_authenticate(user=ifrc_user)
        resp = self.client.get(f"/api/v2/region/{self.region.id}/")
        self.assertEqual(resp.status_code, 200)
        ids = self._get_snippet_ids(resp.json())
        self.assertEqual(
            sorted(ids),
            sorted(
                [
                    self.snip_public.id,
                    self.snip_ifrc.id,
                    self.snip_membership.id,
                    self.snip_ifrc_ns.id,
                ]
            ),
        )
