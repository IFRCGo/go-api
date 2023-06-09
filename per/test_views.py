import json

from main.test_case import APITestCase
from api.models import Country
from .models import (
    Form,
    FormArea,
    FormComponent,
    FormQuestion,
    FormAnswer,
    PerWorkPlan,
    WorkPlanStatus,
    PerWorkPlanComponent,
    FormData,
    FormComponentResponse
)
from api.factories.country import CountryFactory
from per.factories import (
    OverviewFactory,
    PerWorkPlanComponentFactory,
    PerWorkPlanFactory,
    FormAreaFactory,
    FormComponentFactory,
    FormAnswerFactory,
    FormQuestionFactory,
    FormDataFactory,
)


class PerTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.country = Country.objects.create(name="Country 1")
        self.area = FormArea.objects.create(title="Area 1", area_num=1)
        self.component = FormComponent.objects.create(id=1, area_id=self.area.pk, component_num=1)
        FormQuestion.objects.create(id=1, component_id=self.component.pk, question="Are you?", question_num=1)
        FormAnswer.objects.create(id=1, text="Answer 1")

    def formbase(self):
        return {"id": 1, "area_id": self.area.pk, "user_id": self.user.pk, "comment": "test comment"}

    def formbase_with_question(self):
        base = self.formbase()
        base["questions"] = {1: {"selected_answer": 1, "notes": "very notes"}}
        return base

    # TODO: fix tests (new Overview structure)...
    # def test_createperform_with_questions(self):
    #     body = self.formbase_with_question()
    #     headers = {'CONTENT_TYPE': 'application/json'}
    #     resp = self.client.post('/createperform', body, format='json', headers=headers)
    #     self.assertEqual(resp.status_code, 200)

    # def test_createperform(self):
    #     ''' PER Form without "questions" should fail with bad_request '''
    #     body = {
    #         'area_id': self.area.pk,
    #         'user_id': self.user.pk,
    #         'comment': 'test comment',
    #     }
    #     resp = self.client.post('/createperform', body, format='json')
    #     self.assert_400(resp)

    # FIXME: ...
    # def test_updateperform(self):
    #     body = self.formbase()
    #     form = Form.objects.create(**body)
    #     updatebody = self.formbase_with_question()
    #     updatebody['id'] = form.pk
    #     updatebody['comment'] += ' [updated]'

    #     self.authenticate(self.user)
    #     resp = self.client.post('/updateperform', updatebody, format='json')
    #     self.assert_200(resp)


class PerTestCase(APITestCase):
    def test_create_peroverview(self):
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
        url = "/api/v2/new-per/"
        self.authenticate(self.user)
        response = self.client.post(url, data, format="multipart")
        self.assert_403(response)

        # authenticate with super_user

        self.authenticate(self.ifrc_user)
        response = self.client.post(url, data, format="json")
        self.assert_201(response)

    def test_workplan_formdata(self):
        overview = OverviewFactory.create()
        area = FormAreaFactory.create()
        component = FormComponentFactory.create()
        old_count = PerWorkPlan.objects.count()
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
        url = "/api/v2/per-work-plan/"
        self.authenticate(self.ifrc_user)
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(PerWorkPlan.objects.count(), old_count + 1)
        self.assert_201(response)

    def test_form_prioritization_formdata(self):
        overview = OverviewFactory.create()
        component = FormComponentFactory.create()
        component2 = FormComponentFactory.create()
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
        url = "/api/v2/per-prioritization/"
        self.authenticate(self.ifrc_user)
        response = self.client.post(url, data, format="json")
        print(response.content)
        self.assert_201(response)

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
        url = "/api/v2/new-per/"
        self.authenticate(self.user)
        response = self.client.post(url, data, format="multipart")
        self.assert_403(response)

    # def test_create_per_assessment(self):
    #     area1 = FormAreaFactory.create(title="area1")
    #     area2 = FormAreaFactory.create(title="area2")
    #     area3 = FormAreaFactory.create(title="area3")
    #     area4 = FormAreaFactory.create(title="area4")
    #     area5 = FormAreaFactory.create(title="area5")
    #     overview = OverviewFactory.create()
    #     question1, question2, question3, question4, question5 = FormQuestionFactory.create_batch(5)
    #     answer1, answer2, answer3, answer4, answer5 = FormAnswerFactory.create_batch(5)
    #     component = FormComponentFactory.create()
    #     component2 = FormComponentFactory.create()

    #     data = {
    #         "overview": overview.id,
    #         #"user": self.user.id,
    #         "area_responses": [
    #             {

    #                 "area": area1.id,
    #                 "component_response": [
    #                     {
    #                         "component": component.id,
    #                         #"status": FormComponentResponse.FormComponentStatus.HIGH_PERFORMANCE,
    #                         "consideration_responses": [
    #                             {
    #                                 "urban_considerations": "testtss",
    #                                 "epi_considerations": "dasdasd",
    #                                 "climate_environmental_conisderations": "dasdasdasd"
    #                             }
    #                         ],
    #                         "question_responses": [
    #                             {
    #                                 "question": question1.id,
    #                                 "answer": answer1.id,
    #                                 "notes": "testststs"
    #                             }
    #                         ],
    #                     }
    #                 ],
    #                 #"is_draft": True
    #             }
    #         ]
    # }

    #     url = '/api/v2/per-assessment/'
    #     self.authenticate(self.user)
    #     response = self.client.post(url, data=data, format="json")
    #     print(response.content)
    #     self.assertEqual(response.status_code, 201)
    #     response_data = json.loads(response.content)
    #     form_id = response_data[0]['id']
