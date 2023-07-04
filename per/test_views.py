import json

from main.test_case import APITestCase
from .models import (
    PerWorkPlan,
    WorkPlanStatus,
)
from api.factories.country import CountryFactory
from per.factories import (
    OverviewFactory,
    FormAreaFactory,
    FormComponentFactory,
    FormPrioritizationFactory,
    PerWorkPlanFactory
)


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
        form_id = response_data['id']
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
                {
                    "is_prioritized": True,
                    "justification_text": "yeysysysyayas",
                    "component": component.id
                },
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
