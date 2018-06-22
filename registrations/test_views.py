# 1. create two users to function as gatekeepers
# 2. Make a request to views.NewRegistration with new user request
# 3. Access the Pending users table to obtain the user's token
# 4. Use the user token and user username to query views.VerifyEmail
# 5. Confirm that a user with an official email is activated, and a user without an official email is not activated
# 6. Use the admin token and new user username to query views.ValidateUser
# 7. Confirm that a user without an official email is activated.

import json, pprint
from django.test import TestCase
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from .models import Pending
from api.models import Country

from api.views import (
    bad_request,
    bad_http_request,
    PublicJsonPostView,
    PublicJsonRequestView,
    GetAuthToken,
)

class TwoGatekeepersTest(APITestCase):
    def setUp(self):
        print ('\n1. Creating two users to function as gatekeepers')
        user1 = User.objects.create(username='jo')
        user1.set_password('12345678')
        user1.save()
        user2 = User.objects.create(username='ke')
        user2.set_password('12345678')
        user2.save()
        country = Country.objects.create(name='country')

    def test_two_gatekeepers(self):
        print ('2a. Making a request to views.NewRegistration with new user request') 
        country = Country.objects.get(name='country')
        newusr='pe'
        body = {
            'email': 'pe@doesnotexist.hu',
            'username': newusr,
            'password': '87654321',
            'country':  country.pk,
            'organizationType': 'OTHR',
            'organization': 'Zoo',
            'firstname': 'Peter',
            'lastname': 'Falk',
        }
        headers = {'CONTENT_TYPE': 'application/json'}
        try:
            response = self.client.post('/register', body, format='json', headers=headers).content
        except ObjectDoesNotExist:
            print ('Does Not exist error')
        except:
            print ('Contact error')
#           assertRaises(exception, callable, *args, **kwds)¶
#           assertRaises(exception, msg=None)

        print ('2b. Making a request to views.NewRegistration with new user request') 
        country = Country.objects.get(name='country')
        newusr='pe'
        body = {
            'email': 'pe@voroskereszt.hu',
            'username': newusr,
            'password': '87654321',
            'country':  country.pk,
            'organizationType': 'OTHR',
            'organization': 'Zoo',
            'firstname': 'Peter',
            'lastname': 'Falk',
        }
        headers = {'CONTENT_TYPE': 'application/json'}
        response = self.client.post('/register', body, format='json', headers=headers).content
        response = json.loads(response)
        print(response)
        
        print ('3. Accessing the Pending users table to obtain the user\'s token')
        pending_user = Pending.objects.get(user__username=newusr)
        print("Pending user username: ",pending_user.user)
        print("Pending user key: ",pending_user.pk)
        print("Pending user token: ",pending_user.token)
        print("Pending user email: ",pending_user)
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint (pending_user.user)

        print ('4. Using the user token and user username to query views.VerifyEmail')

        body1 = {
            'user': newusr,
            'token': pending_user.token,
        }
        response = self.client.get('/verify_email', body1, format='json', headers=headers).content
        print(response[:27])

        print ('5. Confirming that a user with an official email is activated, and a user without an official email is not activated (2a)')
        self.assertTrue(pending_user.user.is_active)
        print ('6. Using the admin token and new user username to query views.ValidateUser') #url(r'^validate_user', ValidateUser
        print ('7. Confirming that a user without an official email is activated.')


#    def test_get_auth(self):
#        body = {
#            'username': 'jo',
#            'password': '12345678',
#        }
#        headers = {'CONTENT_TYPE': 'application/json'}
#        response = self.client.post('/get_auth_token', body, format='json', headers=headers).content
#        response = json.loads(response)
#        self.assertIsNotNone(response.get('token'))
#        self.assertIsNotNone(response.get('expires'))
