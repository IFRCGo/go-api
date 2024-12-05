import json
from unittest import mock

from api.factories.country import CountryFactory
from api.factories.region import RegionFactory
from api.models import AppealDocument, AppealType
from main.test_case import APITestCase
from per.factories import (
    AppealDocumentFactory,
    AppealFactory,
    FormAreaFactory,
    FormComponentFactory,
    FormPrioritizationFactory,
    OpsLearningFactory,
    OverviewFactory,
    PerWorkPlanFactory,
    SectorTagFactory,
)

from .models import OpsLearning, WorkPlanStatus


class PerTestCase(APITestCase):
    def test_create_peroverview(self):
        country = CountryFactory.create()
        data = {
            "date_of_orientation": "2021-03-11",
            "assessment_number": 1,
            "branches_involved": "test branches",
            "assess_preparedness_of_country": True,
            "assess_urban_aspect_of_country": True,
            "assess_climate_environment_of_country": True,
            "date_of_previous_assessment": "2021-03-10",
            "country": country.id,
            "user": self.user.id,
            "workplan_revision_date": "2021-03-11",
            "facilitator_name": "Test Name",
            "facilitator_email": "test@test",
            "facilitator_phone": "981818181",
            "facilitator_contact": "Nepal",
            "ns_focal_point_name": "Test Name",
            "ns_focal_point_email": "test@test",
            "ns_focal_point_phone": "981818181",
            "ns_focal_point_contact": "Nepal",
            "partner_focal_point_name": "Test Name",
            "partner_focal_point_email": "test@test",
            "partner_focal_point_phone": "981818181",
            "partner_focal_point_contact": "Nepal",
            "date_of_assessment": "2021-03-11",
        }
        url = "/api/v2/per-overview/"
        self.authenticate(self.user)
        response = self.client.post(url, data, format="multipart")
        self.assert_403(response)

        # authenticate with super_user

        self.authenticate(self.ifrc_user)
        response = self.client.post(url, data, format="json")
        response_data = json.loads(response.content)
        form_id = response_data["id"]
        self.assert_201(response)
        patch_url = f"/api/v2/per-overview/{form_id}/"
        patch_data = {
            "date_of_orientation": "2021-03-29",
            "assessment_number": 1,
            "branches_involved": "test branches",
            "assess_preparedness_of_country": True,
            "assess_urban_aspect_of_country": True,
            "assess_climate_environment_of_country": True,
            "date_of_previous_assessment": "2021-03-10",
            "country": country.id,
            "user": self.user.id,
            "workplan_revision_date": "2021-03-11",
            "facilitator_name": "Test Name",
            "facilitator_email": "test@test",
            "facilitator_phone": "981818181",
            "facilitator_contact": "Nepal",
            "ns_focal_point_name": "Test Name",
            "ns_focal_point_email": "test@test",
            "ns_focal_point_phone": "981818181",
            "ns_focal_point_contact": "Nepal",
            "partner_focal_point_name": "Test Name",
            "partner_focal_point_email": "test@test",
            "partner_focal_point_phone": "981818181",
            "partner_focal_point_contact": "Nepal",
            "date_of_assessment": "2021-03-22",
        }
        self.authenticate(self.ifrc_user)
        response = self.client.put(patch_url, patch_data, format="json")
        self.assert_200(response)

    def test_workplan_formdata(self):
        overview = OverviewFactory.create()
        area = FormAreaFactory.create()
        component = FormComponentFactory.create()
        workplan = PerWorkPlanFactory.create(
            overview=overview,
        )
        data = {
            "overview": overview.id,
            "workplan_component": [
                {
                    "actions": "tetststakaskljsakjdsakjaslhjkasdklhjasdhjklasdjklhasdk,l.j",
                    "responsible_email": "new@gmail.com",
                    "responsible_name": "nanananan",
                    "component": component.id,
                    "area": area.id,
                    "status": WorkPlanStatus.PENDING,
                },
                {
                    "actions": "tetststakaskljsakjdsakjaslhjkasdklhjasdhjklasdjklhasdk,l.j",
                    "responsible_email": "new@gmail.com",
                    "responsible_name": "nanananan",
                    "component": component.id,
                    "area": area.id,
                    "status": WorkPlanStatus.PENDING,
                },
            ],
        }
        url = f"/api/v2/per-work-plan/{workplan.id}/"
        self.authenticate(self.ifrc_user)
        response = self.client.patch(url, data=data, format="json")
        self.assert_200(response)

        # try to post to api

        url = "/api/v2/per-work-plan/"
        self.authenticate(self.ifrc_user)
        response = self.client.post(url, data=data, format="json")
        self.assert_400(response)

    def test_form_prioritization_formdata(self):
        overview = OverviewFactory.create()
        component = FormComponentFactory.create()
        component2 = FormComponentFactory.create()
        proritization = FormPrioritizationFactory.create(
            overview=overview,
        )
        data = {
            "overview": overview.id,
            "component_responses": [
                {"is_prioritized": True, "justification_text": "yeysysysyayas", "component": component.id},
                {
                    "component": component2.id,
                    "is_prioritized": None,
                    "justification_text": "asdasdasd",
                },
            ],
        }
        url = f"/api/v2/per-prioritization/{proritization.id}/"
        self.authenticate(self.ifrc_user)
        response = self.client.patch(url, data, format="json")
        self.assert_200(response)

        # try to post
        url = "/api/v2/per-prioritization/"
        self.authenticate(self.ifrc_user)
        response = self.client.post(url, data=data, format="json")
        self.assert_400(response)

    def test_overview_date_of_assessment(self):
        country = CountryFactory.create()
        data = {
            "date_of_orientation": "2021-03-11",
            "assessment_number": 1,
            "branches_involved": "test branches",
            "date_of_assessment": "2021-03-08",
            "assess_preparedness_of_country": True,
            "assess_urban_aspect_of_country": True,
            "assess_climate_environment_of_country": True,
            "date_of_previous_assessment": "2021-03-10",
            "type_of_per_assessment": "test",
            "date_of_mid_term_review": "2021-03-10",
            "date_of_next_asmt": "2021-03-11",
            "is_epi": True,
            "is_finalized": False,
            "country": country.id,
            "user": self.user.id,
            "workplan_revision_date": "2021-03-11",
            "facilitator_name": "Test Name",
            "facilitator_email": "test@test",
            "facilitator_phone": "981818181",
            "facilitator_contact": "Nepal",
            "ns_focal_point_name": "Test Name",
            "ns_focal_point_email": "test@test",
            "ns_focal_point_phone": "981818181",
            "ns_focal_point_contact": "Nepal",
            "partner_focal_point_name": "Test Name",
            "partner_focal_point_email": "test@test",
            "partner_focal_point_phone": "981818181",
            "partner_focal_point_contact": "Nepal",
        }
        url = "/api/v2/per-overview/"
        self.authenticate(self.user)
        response = self.client.post(url, data, format="multipart")
        self.assert_403(response)


class OpsLearningSummaryTestCase(APITestCase):

    def check_response_id(self, url, data):
        response = self.client.get(url, data)
        self.assert_200(response)
        response_data = json.loads(response.content)
        id = response_data["id"]

        # NOTE: Checking if the object is same for the filters
        response = self.client.get(url, data)
        self.assert_200(response)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], id)

    @mock.patch("per.task.generate_summary")
    def test_summary_generation(self, generate_summary):
        country = CountryFactory.create()

        url = "/api/v2/ops-learning/summary/"
        filters = {
            "appeal_code__dtype": AppealType.DREF,
        }
        self.check_response_id(url=url, data=filters)
        self.assertTrue(generate_summary.assert_called)

        # checking with different filters
        filters = {
            "appeal_code__dtype": AppealType.APPEAL,
            "appeal_code__country": country.id,
        }
        self.check_response_id(url=url, data=filters)
        self.assertTrue(generate_summary.assert_called)


class OpsLearningStatsTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.region = RegionFactory()
        cls.country = CountryFactory(region=cls.region)

        SectorTagFactory.create_batch(5)
        OpsLearningFactory.create_batch(10)

        for _ in range(5):
            appeal = AppealFactory(region=cls.region)
            AppealDocumentFactory.create_batch(4, appeal=appeal)

    def test_ops_learning_stats(self):
        url = "/api/v2/ops-learning/stats/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Validate keys in response
        expected_keys = [
            "operations_included",
            "sources_used",
            "learning_extracts",
            "sectors_covered",
            "sources_overtime",
            "learning_by_region",
            "learning_by_sector",
            "learning_by_country",
        ]
        for key in expected_keys:
            self.assertIn(key, response.data)

        # Validate counts
        self.assertEqual(response.data["operations_included"], OpsLearning.objects.values("learning").distinct().count())

        appeal_codes = OpsLearning.objects.values_list("appeal_code", flat=True).distinct()
        sources_count = AppealDocument.objects.filter(appeal__aid__in=appeal_codes).distinct().count()
        self.assertEqual(response.data["sources_used"], sources_count)

        validated_learning_extracts = OpsLearning.objects.filter(learning_validated__isnull=False).distinct().count()
        self.assertEqual(response.data["learning_extracts"], validated_learning_extracts)

        sectors_covered_count = (
            OpsLearning.objects.filter(sector_validated__isnull=False).values("sector_validated").distinct().count()
        )
        self.assertEqual(response.data["sectors_covered"], sectors_covered_count)

        # Validate sources_overtime
        for appeal_type, label in AppealType.choices:
            self.assertIn(label, response.data["sources_overtime"])
            for item in response.data["sources_overtime"][label]:
                self.assertIn("year", item)
                self.assertIn("count", item)

        # Validate learning_by_region
        for item in response.data["learning_by_region"]:
            self.assertIn("region_name", item)
            self.assertIn("region_id", item)
            self.assertIn("count", item)

            region_id = item["region_id"]
            expected_count = OpsLearning.objects.filter(appeal_code__region_id=region_id).count()
            self.assertEqual(item["count"], expected_count)

        # Validate learning_by_sector
        for item in response.data["learning_by_sector"]:
            self.assertIn("id", item)
            self.assertIn("title", item)
            self.assertIn("count", item)

            sector_id = item["id"]
            expected_count = OpsLearning.objects.filter(sector_validated=sector_id).count()
            self.assertEqual(item["count"], expected_count)

        # Verify the operation count for each country
        for item in response.data["learning_by_country"]:
            self.assertIn("country_name", item)
            self.assertIn("country_id", item)
            self.assertIn("operation_count", item)

            country_id = item["country_id"]
            expected_operation_count = OpsLearning.objects.filter(appeal_code__country_id=country_id).count()
            self.assertEqual(item["operation_count"], expected_operation_count)
