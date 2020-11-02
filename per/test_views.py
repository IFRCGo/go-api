from django.conf import settings
from modeltranslation.utils import build_localized_fieldname

from main.test_case import APITestCase
from api.models import Country
from .models import Language, Form, FormArea, FormComponent, FormQuestion, FormAnswer


class PerTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.country = Country.objects.create(name='Country 1')
        self.area = FormArea.objects.create(title='Area 1', area_num=1)
        self.component = FormComponent.objects.create(
            id=1,
            area_id=self.area.pk,
            component_num=1
        )
        FormQuestion.objects.create(
            id=1,
            component_id=self.component.pk,
            question='Are you?',
            question_num=1
        )
        FormAnswer.objects.create(id=1, text='Answer 1')

    def formbase(self):
        return {
            'id': 1,
            'area_id': self.area.pk,
            'user_id': self.user.pk,
            'country_id': self.country.pk,
            'is_draft': False,
            'comment': 'test comment'
        }

    def formbase_with_question(self):
        base = self.formbase()
        base['questions'] = {1: {'selected_answer': 1, 'notes': 'very notes'}}
        return base

    def formdraft(self):
        base = self.formbase()
        base['is_draft'] = True
        return base

    def test_createperform_with_questions(self):
        body = self.formbase_with_question()
        headers = {'CONTENT_TYPE': 'application/json'}
        resp = self.client.post('/createperform', body, format='json', headers=headers)
        self.assertEqual(resp.status_code, 200)

    def test_createperform(self):
        ''' PER Form without "questions" should fail with bad_request '''
        body = {
            'area_id': self.area.pk,
            'user_id': self.user.pk,
            'country_id': self.country.pk,
            'comment': 'test comment',
        }
        resp = self.client.post('/createperform', body, format='json')
        self.assert_400(resp)

    def test_updateperform(self):
        body = self.formbase()
        form = Form.objects.create(**body)
        updatebody = self.formbase_with_question()
        updatebody['id'] = form.pk
        updatebody['comment'] += ' [updated]'

        self.authenticate(self.user)
        resp = self.client.post('/updateperform', updatebody, format='json')
        self.assert_200(resp)

    # def test_deleteperform(self):
    #     body = {
    #         'id': 1
    #     }
    #     import pdb; pdb.set_trace()
    #     base = self.formbase()
    #     # TODO: self.user is 'jon@dave.com' but request below gets Anonymoususer
    #     Form.objects.create(**base)
    #     resp = self.client.post('/deleteperform', body, format='json')
    #     self.assert_200(resp)
