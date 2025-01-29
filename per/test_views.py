import json
from unittest import mock

from django.core import management

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

from .models import WorkPlanStatus


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
