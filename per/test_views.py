import json
from datetime import date
from unittest import mock

from django.core import management
from django.core.cache import cache
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext

from api.factories.country import CountryFactory
from api.factories.region import RegionFactory
from api.models import AppealType
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

from .models import (
    AreaResponse,
    FormComponentResponse,
    FormPrioritizationComponent,
    PerAssessment,
    PerComponentRating,
    WorkPlanStatus,
)

TEST_LOC_MEM_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "per-dashboard-tests",
    }
}


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

    def setUp(self):
        super().setUp()
        self.region = RegionFactory.create(label="Region A")
        self.country = CountryFactory.create(region=self.region, name="Country A")

        self.sector1 = SectorTagFactory.create(title="Sector 1")
        self.sector2 = SectorTagFactory.create(title="Sector 2")

        self.appeal1 = AppealFactory.create(
            region=self.region, country=self.country, code="APP001", atype=0, start_date="2023-01-01"
        )
        self.appeal2 = AppealFactory.create(
            region=self.region, country=self.country, code="APP002", atype=1, start_date="2023-02-01"
        )

        appeal_document_1 = AppealDocumentFactory.create(appeal=self.appeal1)
        appeal_document_2 = AppealDocumentFactory.create(appeal=self.appeal2)

        self.ops_learning1 = OpsLearningFactory.create(
            is_validated=True, appeal_code=self.appeal1, appeal_document_id=appeal_document_1.id
        )
        self.ops_learning1.sector_validated.set([self.sector1])

        self.ops_learning2 = OpsLearningFactory.create(
            is_validated=True, appeal_code=self.appeal2, appeal_document_id=appeal_document_2.id
        )
        self.ops_learning2.sector_validated.set([self.sector2])

        self.ops_learning3 = OpsLearningFactory.create(
            is_validated=False, appeal_code=self.appeal2, appeal_document_id=appeal_document_2.id
        )
        self.ops_learning3.sector_validated.set([self.sector2])

    def test_ops_learning_stats(self):
        url = "/api/v2/ops-learning/stats/"
        response = self.client.get(url)

        self.assert_200(response)

        # Updated counts based on validated entries
        self.assertEqual(response.data["operations_included"], 2)
        self.assertEqual(response.data["sources_used"], 2)
        self.assertEqual(response.data["learning_extracts"], 2)
        self.assertEqual(response.data["sectors_covered"], 2)

        # Validate learning by region
        region_data = response.data["learning_by_region"]
        self.assertEqual(region_data[0]["count"], 2)

        # Validate learning by sector
        sector_data = response.data["learning_by_sector"]
        self.assertEqual(len(sector_data), 2)

        # Validate learning by country
        country_data = response.data["learning_by_country"]
        self.assertEqual(len(country_data), 1)

        sources_overtime = response.data["sources_overtime"]
        self.assertEqual(len(sources_overtime), 2)

    def test_migrate_subcomponents(self):
        parent_component_14 = FormComponentFactory.create(component_num=14, is_parent=True)

        sub_components_14 = FormComponentFactory.create_batch(3, component_num=14)
        other_components = FormComponentFactory.create_batch(2, component_num=1)

        # OpsLearning with only parent component and no sub components of component 14
        ops_learning_with_only_parent_component = OpsLearningFactory.create()
        ops_learning_with_only_parent_component.per_component.add(parent_component_14)
        ops_learning_with_only_parent_component.per_component.add(*other_components)

        ops_learning_with_only_parent_component.per_component_validated.add(parent_component_14)
        ops_learning_with_only_parent_component.per_component_validated.add(*other_components)

        # OpsLearning with parent component and sub components
        ops_learning_with_parent_component = OpsLearningFactory.create()

        ops_learning_with_parent_component.per_component.add(parent_component_14)
        ops_learning_with_parent_component.per_component.add(*sub_components_14)
        ops_learning_with_parent_component.per_component.add(*other_components)

        ops_learning_with_parent_component.per_component_validated.add(parent_component_14)
        ops_learning_with_parent_component.per_component_validated.add(*sub_components_14)
        ops_learning_with_parent_component.per_component_validated.add(*other_components)

        # OpsLearning without parent component but with sub components
        ops_learning_without_parent_component = OpsLearningFactory.create()
        ops_learning_without_parent_component.per_component.add(*sub_components_14)
        ops_learning_without_parent_component.per_component.add(*other_components)

        ops_learning_without_parent_component.per_component_validated.add(*sub_components_14)
        ops_learning_without_parent_component.per_component_validated.add(*other_components)

        # Operational learning with one sub component without parent component
        ops_learning = OpsLearningFactory.create()
        ops_learning.per_component.add(sub_components_14[0])
        ops_learning.per_component_validated.add(sub_components_14[0])
        ops_learning.per_component_validated.add(sub_components_14[1])
        ops_learning.per_component.add(other_components[0])
        ops_learning.per_component_validated.add(other_components[0])

        # Run the management command
        management.call_command("migrate_sub_components_to_component14")

        ops_learning_with_only_parent_component.refresh_from_db()
        self.assertEqual(ops_learning_with_only_parent_component.per_component.count(), 3)
        self.assertEqual(ops_learning_with_only_parent_component.per_component_validated.count(), 3)

        ops_learning_with_parent_component.refresh_from_db()
        self.assertEqual(ops_learning_with_parent_component.per_component.count(), 3)
        self.assertEqual(ops_learning_with_parent_component.per_component_validated.count(), 3)

        ops_learning_without_parent_component.refresh_from_db()
        self.assertEqual(ops_learning_without_parent_component.per_component.count(), 3)
        self.assertEqual(ops_learning_without_parent_component.per_component_validated.count(), 3)

        ops_learning.refresh_from_db()
        self.assertEqual(ops_learning.per_component.count(), 2)
        self.assertEqual(ops_learning.per_component_validated.count(), 2)


class OpsLearningCoverageTestCase(APITestCase):

    def setUp(self):
        super().setUp()
        country = CountryFactory.create()
        self.appeal1 = AppealFactory.create(code="APP-COV-1", country=country)
        self.appeal2 = AppealFactory.create(code="APP-COV-2", country=country)
        self.ops_learning1 = OpsLearningFactory.create(is_validated=True, appeal_code=self.appeal1)
        self.ops_learning2 = OpsLearningFactory.create(is_validated=False, appeal_code=self.appeal2)

    def test_ops_learning_coverage_list(self):
        url = "/api/v2/ops-learning-coverage/"
        response = self.client.get(url)

        self.assert_200(response)
        results = response.data["results"]
        self.assertEqual(len(results), 2)

        result_keys = set(results[0].keys())
        self.assertEqual(result_keys, {"appeal_code", "tagging_status", "counts"})

        appeal_codes = {item["appeal_code"] for item in results}
        self.assertEqual(appeal_codes, {self.appeal1.code, self.appeal2.code})
        result_by_appeal = {item["appeal_code"]: item for item in results}
        self.assertEqual(result_by_appeal[self.appeal1.code]["tagging_status"], "completed")
        self.assertEqual(result_by_appeal[self.appeal2.code]["tagging_status"], "not_started")
        self.assertEqual(result_by_appeal[self.appeal1.code]["counts"], 1)
        self.assertEqual(result_by_appeal[self.appeal2.code]["counts"], 1)

    def test_ops_learning_coverage_list_admin(self):
        url = "/api/v2/ops-learning-coverage/"
        self.authenticate(self.ifrc_user)
        response = self.client.get(url)

        self.assert_200(response)
        results = response.data["results"]
        self.assertEqual(len(results), 2)

        appeal_codes = {item["appeal_code"] for item in results}
        self.assertEqual(appeal_codes, {self.appeal1.code, self.appeal2.code})
        result_by_appeal = {item["appeal_code"]: item for item in results}
        self.assertEqual(result_by_appeal[self.appeal1.code]["tagging_status"], "completed")
        self.assertEqual(result_by_appeal[self.appeal2.code]["tagging_status"], "not_started")
        self.assertEqual(result_by_appeal[self.appeal1.code]["counts"], 1)
        self.assertEqual(result_by_appeal[self.appeal2.code]["counts"], 1)

    def test_ops_learning_coverage_filter_validated_is_ignored(self):
        url = "/api/v2/ops-learning-coverage/"
        response = self.client.get(url, {"is_validated": "true"})

        self.assert_200(response)
        results = response.data["results"]
        self.assertEqual(len(results), 2)
        result_by_appeal = {item["appeal_code"]: item for item in results}
        self.assertEqual(result_by_appeal[self.appeal1.code]["tagging_status"], "completed")
        self.assertEqual(result_by_appeal[self.appeal2.code]["tagging_status"], "not_started")

    def test_ops_learning_coverage_aggregates_duplicate_appeal(self):
        OpsLearningFactory.create(is_validated=False, appeal_code=self.appeal1)

        url = "/api/v2/ops-learning-coverage/"
        self.authenticate(self.ifrc_user)
        response = self.client.get(url)

        self.assert_200(response)
        results = response.data["results"]
        result_by_appeal = {item["appeal_code"]: item for item in results}

        self.assertEqual(result_by_appeal[self.appeal1.code]["counts"], 2)
        self.assertEqual(result_by_appeal[self.appeal1.code]["tagging_status"], "in_progress")


class PerDashboardDataTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.region = RegionFactory.create(name=0, label="Africa")

    def create_country(self, name: str, iso: str, iso3: str):
        return CountryFactory.create(name=name, iso=iso, iso3=iso3, region=self.region)

    def create_component_assessment(self, overview, *, component_id=None, duplicate=False, priority_value=True):
        area = FormAreaFactory.create(title="Analysis and planning", area_num=2)
        component = FormComponentFactory.create(
            area=area,
            component_num=3,
            title="Component three",
            **({"id": component_id} if component_id is not None else {}),
        )
        rating = PerComponentRating.objects.create(title="High", value=4)
        component_response = FormComponentResponse.objects.create(
            component=component,
            rating=rating,
            epi_considerations="yes",
            migration_considerations=None,
        )
        area_response = AreaResponse.objects.create(area=area)
        area_response.component_response.add(component_response)

        assessment = PerAssessment.objects.create(overview=overview)
        assessment.area_responses.add(area_response)

        if duplicate:
            duplicate_area_response = AreaResponse.objects.create(area=area)
            duplicate_area_response.component_response.add(component_response)
            assessment.area_responses.add(duplicate_area_response)

        prioritization = FormPrioritizationFactory.create(overview=overview)
        prioritized_component = FormPrioritizationComponent.objects.create(
            component=component,
            is_prioritized=priority_value,
        )
        prioritization.prioritized_action_responses.add(prioritized_component)
        return assessment, component

    def test_map_data_returns_complete_history_and_deterministic_latest_processes(self):
        country_one = self.create_country("Country One", "C1", "C01")
        country_two = self.create_country("Country Two", "C2", "C02")
        older_dated = OverviewFactory.create(
            country=country_one,
            assessment_number=1,
            date_of_assessment=None,
        )
        latest_dated = OverviewFactory.create(
            country=country_one,
            assessment_number=1,
            date_of_assessment=date(2024, 1, 1),
        )
        latest_number = OverviewFactory.create(
            country=country_two,
            assessment_number=2,
            date_of_assessment=None,
        )

        response = self.client.get("/api/v2/per-map-data")

        self.assert_200(response)
        self.assertEqual(
            {item["id"] for item in response.data["processes"]},
            {
                older_dated.id,
                latest_dated.id,
                latest_number.id,
            },
        )
        self.assertEqual(len(response.data["results"]), 2)
        latest_by_country = {item["country_id"]: item for item in response.data["results"]}
        self.assertEqual(latest_by_country[country_one.id]["id"], latest_dated.id)
        self.assertEqual(latest_by_country[country_two.id]["id"], latest_number.id)

    def test_map_data_results_are_ordered_by_country(self):
        first_country = self.create_country("First Country", "F1", "F01")
        second_country = self.create_country("Second Country", "S1", "S01")
        OverviewFactory.create(country=second_country)
        OverviewFactory.create(country=first_country)

        response = self.client.get("/api/v2/per-map-data")

        self.assert_200(response)
        self.assertEqual(
            [item["country_id"] for item in response.data["results"]],
            [first_country.id, second_country.id],
        )

    def test_map_data_preserves_authoritative_considerations_and_priorities(self):
        country = self.create_country("Country With Considerations", "C3", "C03")
        overview = OverviewFactory.create(
            country=country,
            assess_preparedness_of_country=True,
            assess_climate_environment_of_country=False,
            assess_urban_aspect_of_country=None,
            assess_migration_aspect_of_country=True,
        )
        self.create_component_assessment(overview)

        response = self.client.get("/api/v2/per-map-data")

        self.assert_200(response)
        process = response.data["results"][0]
        self.assertIs(process["epi_considerations"], True)
        self.assertIs(process["climate_environmental_considerations"], False)
        self.assertIsNone(process["urban_considerations"])
        self.assertIs(process["migration_considerations"], True)
        self.assertEqual(process["migration_considerations_from_assessment"], False)
        self.assertEqual(process["prioritized_components"][0]["componentId"], process["components"][0]["component_id"])

    def test_map_data_keeps_legacy_null_priority_components(self):
        country = self.create_country("Country With Legacy Priorities", "C6", "C06")
        overview = OverviewFactory.create(country=country)
        _, component = self.create_component_assessment(overview, component_id=100_000, priority_value=None)

        response = self.client.get("/api/v2/per-map-data")

        self.assert_200(response)
        process = response.data["results"][0]
        self.assertEqual(
            [item["componentId"] for item in process["prioritized_components"]],
            [component.id],
        )

    def test_dashboard_data_enriches_component_assessments_and_retains_empty_country_assessments(self):
        country_with_components = self.create_country("Country With Components", "C4", "C04")
        country_without_components = self.create_country("Country Without Components", "C5", "C05")
        overview_with_components = OverviewFactory.create(country=country_with_components)
        assessment, component = self.create_component_assessment(overview_with_components, duplicate=True)
        overview_without_components = OverviewFactory.create(country=country_without_components)
        empty_assessment = PerAssessment.objects.create(overview=overview_without_components)

        response = self.client.get("/api/v2/per-dashboard-data")

        self.assert_200(response)
        component_item = next(item for item in response.data["assessments"] if item["component_id"] == component.id)
        component_assessment = next(item for item in component_item["assessments"] if item["assessment_id"] == assessment.id)
        self.assertEqual(component_assessment["country_id"], country_with_components.id)
        self.assertEqual(component_assessment["country_name"], country_with_components.name)
        self.assertEqual(component_assessment["region_id"], self.region.id)
        self.assertEqual(component_assessment["region_name"], "Africa")
        self.assertIn("date_of_assessment", component_assessment)
        self.assertEqual(component_assessment["rating_value"], 4)
        self.assertEqual(component_assessment["rating_title"], "High")

        country_entry = response.data["countryAssessments"][country_with_components.name][0]
        self.assertEqual(country_entry["assessment_id"], assessment.id)
        self.assertEqual(country_entry["country_iso3"], "C04")
        self.assertEqual(country_entry["phase_display"], "Orientation")
        self.assertNotIn("components", country_entry)

        empty_country_entry = response.data["countryAssessments"][country_without_components.name][0]
        self.assertEqual(empty_country_entry["assessment_id"], empty_assessment.id)
        self.assertNotIn("components", empty_country_entry)

    @override_settings(CACHES=TEST_LOC_MEM_CACHE)
    def test_map_data_uses_cache_in_read_only_mode(self):
        country = self.create_country("Cached Map Country", "M1", "M01")
        OverviewFactory.create(country=country)

        with override_settings(DJANGO_READ_ONLY=True):
            cache.clear()
            try:
                first_response = self.client.get("/api/v2/per-map-data")

                self.assert_200(first_response)
                with mock.patch("per.drf_views.get_per_map_data") as get_per_map_data:
                    second_response = self.client.get("/api/v2/per-map-data")

                self.assert_200(second_response)
                get_per_map_data.assert_not_called()
                self.assertEqual(second_response.data, first_response.data)
            finally:
                cache.clear()

    @override_settings(CACHES=TEST_LOC_MEM_CACHE)
    def test_dashboard_data_uses_cache_in_read_only_mode(self):
        country = self.create_country("Cached Dashboard Country", "D1", "D01")
        overview = OverviewFactory.create(country=country)
        self.create_component_assessment(overview)

        with override_settings(DJANGO_READ_ONLY=True):
            cache.clear()
            try:
                first_response = self.client.get("/api/v2/per-dashboard-data")

                self.assert_200(first_response)
                with mock.patch("per.drf_views.get_per_dashboard_data") as get_per_dashboard_data:
                    second_response = self.client.get("/api/v2/per-dashboard-data")

                self.assert_200(second_response)
                get_per_dashboard_data.assert_not_called()
                self.assertEqual(second_response.data, first_response.data)
            finally:
                cache.clear()

    def test_map_data_query_count_is_bounded_for_many_overviews(self):
        for index in range(12):
            country = self.create_country(f"Query Country {index}", f"Q{chr(65 + index)}", f"Q{index:02d}")
            overview = OverviewFactory.create(country=country, date_of_assessment=None)
            self.create_component_assessment(overview)

        with CaptureQueriesContext(connection) as queries:
            response = self.client.get("/api/v2/per-map-data")

        self.assert_200(response)
        self.assertLessEqual(len(queries), 8)

    def test_dashboard_data_query_count_is_bounded_for_many_assessments(self):
        for index in range(12):
            country = self.create_country(f"Assessment Country {index}", f"R{chr(65 + index)}", f"R{index:02d}")
            overview = OverviewFactory.create(country=country, date_of_assessment=None)
            self.create_component_assessment(overview)

        with CaptureQueriesContext(connection) as queries:
            response = self.client.get("/api/v2/per-dashboard-data")

        self.assert_200(response)
        self.assertEqual(len(response.data["countryAssessments"]), 12)
        self.assertLessEqual(len(queries), 8)
