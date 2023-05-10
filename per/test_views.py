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
    FormData
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

    def test_update_workplan(self):
        overview = OverviewFactory.create()
        workplan_component_1, workplan_component_2 = PerWorkPlanComponentFactory.create_batch(2)
        work_plan = PerWorkPlanFactory.create(
            overview=overview,
        )
        work_plan.workplan_component.add(workplan_component_1)
        work_plan.workplan_component.add(workplan_component_2)
        area = FormAreaFactory.create()
        component = FormComponentFactory.create()
        data = {
            "workplan_component": [
                {
                    "actions": "tetststakaskljsakjdsakjaslhjkasdklhjasdhjklasdjklhasdk,l.j",
                    "responsible_email": "new@gmail.com",
                    "responsible_name": "nanananan",
                    "component": component.id,
                    "area": area.id,
                }
            ]
        }
        url = f"/api/v2/per-work-plan/{work_plan.id}/"
        self.authenticate(self.ifrc_user)
        response = self.client.patch(url, data=data, format="json")
        self.assert_200(response)
        self.assertEqual(PerWorkPlan.objects.filter(id=work_plan.id).values("workplan_component").count(), 1)

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
        data = {
            "overview": overview.id,
            "form_proritization_component": [
                {"is_prioritized": True, "justification_text": "yeysysysyayas", "component": component.id},
                {
                    "is_prioritized": True,
                    "justification_text": "ahahahashadhalkshdlajkshdkljashjkldasdasd",
                    "component": component.id,
                },
            ],
        }
        url = "/api/v2/per-prioritization/"
        self.authenticate(self.ifrc_user)
        response = self.client.post(url, data, format="json")
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

    def test_create_per_assessment(self):
        area1 = FormAreaFactory.create(title="area1")
        area2 = FormAreaFactory.create(title="area2")
        area3 = FormAreaFactory.create(title="area3")
        area4 = FormAreaFactory.create(title="area4")
        area5 = FormAreaFactory.create(title="area5")
        overview = OverviewFactory.create()
        question1, question2, question3, question4, question5 = FormQuestionFactory.create_batch(5)
        answer1, answer2, answer3, answer4, answer5 = FormAnswerFactory.create_batch(5)

        data = [
            {
                "area": area1.id,
                "overview": overview.id,
                "form_data": [
                    {
                        "question": question1.id,
                        "selected_answer": answer1.id,
                        "notes": "test description",
                    },
                    {
                        "question": question2.id,
                        "selected_answer": answer3.id,
                        "notes": "test description",
                    },
                    {
                        "question": question3.id,
                        "selected_answer": answer3.id,
                        "notes": "test description",
                    },
                    {
                        "question": question4.id,
                        "selected_answer": answer4.id,
                        "notes": "test description",
                    },
                    {
                        "question": question5.id,
                        "selected_answer": answer5.id,
                        "notes": "test description",
                    },
                ]
            },
            {
                "area": area2.id,
                "overview": overview.id,
                "form_data": [
                    {
                        "question": question1.id,
                        "selected_answer": answer1.id,
                        "notes": "test description",
                    },
                    {
                        "question": question2.id,
                        "selected_answer": answer3.id,
                        "notes": "test description",
                    },
                    {
                        "question": question3.id,
                        "selected_answer": answer3.id,
                        "notes": "test description",
                    },
                    {
                        "question": question4.id,
                        "selected_answer": answer4.id,
                        "notes": "test description",
                    },
                    {
                        "question": question5.id,
                        "selected_answer": answer5.id,
                        "notes": "test description",
                    },
                ]
            },
            {
                "area": area3.id,
                "overview": overview.id,
                "form_data": [
                    {
                        "question": question1.id,
                        "selected_answer": answer1.id,
                        "notes": "test description",
                    },
                    {
                        "question": question2.id,
                        "selected_answer": answer3.id,
                        "notes": "test description",
                    },
                    {
                        "question": question3.id,
                        "selected_answer": answer3.id,
                        "notes": "test description",
                    },
                    {
                        "question": question4.id,
                        "selected_answer": answer4.id,
                        "notes": "test description",
                    },
                    {
                        "question": question5.id,
                        "selected_answer": answer5.id,
                        "notes": "test description",
                    },
                ]
            },
            {
                "area": area4.id,
                "overview": overview.id,
                "form_data": [
                    {
                        "question": question1.id,
                        "selected_answer": answer1.id,
                        "notes": "test description",
                    },
                    {
                        "question": question2.id,
                        "selected_answer": answer3.id,
                        "notes": "test description",
                    },
                    {
                        "question": question3.id,
                        "selected_answer": answer3.id,
                        "notes": "test description",
                    },
                    {
                        "question": question4.id,
                        "selected_answer": answer4.id,
                        "notes": "test description",
                    },
                    {
                        "question": question5.id,
                        "selected_answer": answer5.id,
                        "notes": "test description",
                    },
                ]
            },
            {
                "area": area5.id,
                "overview": overview.id,
                "form_data": [
                    {
                        "question": question1.id,
                        "selected_answer": answer1.id,
                        "notes": "test description",
                    },
                    {
                        "question": question2.id,
                        "selected_answer": answer3.id,
                        "notes": "test description",
                    },
                    {
                        "question": question3.id,
                        "selected_answer": answer3.id,
                        "notes": "test description",
                    },
                    {
                        "question": question4.id,
                        "selected_answer": answer4.id,
                        "notes": "test description",
                    },
                    {
                        "question": question5.id,
                        "selected_answer": answer5.id,
                        "notes": "test description",
                    },
                ]
            }
        ]

        url = '/api/v2/per-draft-asessment/'
        self.authenticate(self.user)
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        form_id = response_data[0]['id']

        # Check for area created for provided
        self.assertEqual(Form.objects.filter(overview_id=overview.id, is_draft=True).count(), 5)
        self.assertEqual(FormData.objects.filter(form__overview=overview).count(), 25)

        # Some answer and question for formdata
        answer1 = FormAnswerFactory.create()
        answer2 = FormAnswerFactory.create()
        answer3 = FormAnswerFactory.create()
        answer4 = FormAnswerFactory.create()
        answer5 = FormAnswerFactory.create()

        question1 = FormQuestionFactory.create()
        question2 = FormQuestionFactory.create()
        question3 = FormQuestionFactory.create()
        question4 = FormQuestionFactory.create()
        question5 = FormQuestionFactory.create()

        form_data1 = FormDataFactory.create(
            selected_answer=answer1,
            question=question1
        )
        form_data2 = FormDataFactory.create(
            selected_answer=answer2,
            question=question2
        ) 

        # update the data for the assessment create
        update_data = {
            "area": area1.id,
            "overview": overview.id,
            "form_data": [
                {
                    "id": form_data1.id,
                    "question": question2.id,
                    "selected_answer": answer1.id,
                    "notes": "test description",
                },
                {
                    "id": form_data2.id,
                    "question": question2.id,
                    "selected_answer": answer3.id,
                    "notes": "test description",
                },
            ]
        }

        url = f'/api/v2/per-draft-asessment/{form_id}/'
        self.authenticate(self.user)
        response = self.client.patch(url, data=update_data, format="json")
        self.assertEqual(response.status_code, 200)

    def test_validate_custom_action(self):
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
            "custom_component": {
                "actions": "test",
                "due_date": "2020-10-20",
                "status": WorkPlanStatus.PENDING
            }
        }
        url = "/api/v2/per-work-plan/"
        self.authenticate(self.ifrc_user)
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(PerWorkPlan.objects.count(), old_count + 1)
        self.assert_201(response)
