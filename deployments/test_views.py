import json
from django.test import TestCase
from rest_framework.test import APITestCase
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Permission
from api.models import Country, District
from .models import Project

username = 'jo'
password = '12345678'

class ProjectGetTest(APITestCase):
    def setUp(self):
        user = User.objects.create(username=username)
        user.set_password(password)
        user.save()

        country1 = Country.objects.create(name='country1', iso='XX')
        country1.save()
        country2 = Country.objects.create(name='country2', iso='YY')
        country2.save()

        district1 = District.objects.create(name='district1', country=country1)
        district1.save
        district2 = District.objects.create(name='district2', country=country2)
        district2.save

        first = Project.objects.create(
                     user             = user
                    ,reporting_ns     = country1
                    ,project_district = district1
                    ,name             = 'aaa'
                    ,programme_type   = 0
                    ,sector           = 0
                    ,start_date       = '2011-11-11'
                    ,end_date         = '2011-11-11'
                    ,budget_amount    = 6000
                    ,status           = 0)
        first.save()

        second = Project.objects.create(
                     user             = user
                    ,reporting_ns     = country1
                    ,project_district = district2
                    ,name             = 'bbb'
                    ,programme_type   = 1
                    ,sector           = 1
                    ,start_date       = '2012-12-12'
                    ,end_date         = '2013-01-01'
                    ,budget_amount    = 3000
                    ,status           = 1)

        second.save()

    def test_1(self):
        user = User.objects.get(username=username)
        body = {
            'username': username,
            'password': password
        }
        headers = {'CONTENT_TYPE': 'application/json'}
        response = self.client.post('/get_auth_token', body, format='json', headers=headers).content
        response = json.loads(response)
        token = response.get('token')
        self.assertIsNotNone(token)
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + token)
        resp = self.client.get('/api/v2/project/')
        self.assertEqual(resp.status_code, 200)

    def test_2(self):
        country2 = Country.objects.get(name='country2')
        district2 = District.objects.get(name='district2')
        user = User.objects.get(username=username)
        body = {
            'username': username,
            'password': password
        }
        headers = {'CONTENT_TYPE': 'application/json'}
        response = self.client.post('/get_auth_token', body, format='json', headers=headers).content
        response = json.loads(response)
        token = response.get('token')
        self.assertIsNotNone(token)
        body = {
            'user'             : user.id,
            'reporting_ns'     : country2.id,
            'project_district' : district2.id,
            'name'             : 'CreateMePls',
            'programme_type'   : 0,
            'sector'           : 0,
            'start_date'       : '2012-11-12',
            'end_date'         : '2013-11-13',
            'budget_amount'    : 7000,
            'status'           : 0
        }
        self.client.credentials(HTTP_AUTHORIZATION = 'Token ' + token)
        self.client.force_authenticate(user=user, token=token)
        resp = self.client.post('/api/v2/create_project/', body, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(Project.objects.all()), 3) # we created 2 projects until now here

    # def test_get_projects(self):
    #     resp = self.client.get('/api/v2/project/', format='json')
    #     self.assertEqual(resp.status_code, 200)
    #     data = json.loads(resp.content)
    #     print(data)


