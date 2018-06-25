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
from django.utils.crypto import get_random_string
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
        user1 = User.objects.create(username='jo',email='jo@arcs.org.af')
        user1.set_password('12345678')
        user1.save()
        user2 = User.objects.create(username='ke',email='ke@arcs.org.af')
        user2.set_password('12345678')
        user2.save()
        country = Country.objects.create(name='country')

    def test_two_gatekeepers(self):
        verbose = True
        verboseprint = print if verbose else lambda *a, **k: None
        verboseprint ('\n\n1. Created two users to function as gatekeepers (with checkable email)')

        verboseprint ('\n------------ A user with a non-official email (series a) : -------')

        verboseprint ('2a. Making a request to views.NewRegistration with new user request') 
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
            'contact': [ {'email':'jo@arcs.org.af'},{'email':'ke@arcs.org.af'},]
        }
        headers = {'CONTENT_TYPE': 'application/json'}
        response = self.client.post('/register', body, format='json', headers=headers).content
        response = json.loads(response)
        verboseprint(response)

        verboseprint ('3a. Accessing the Pending users table to obtain the user\'s token')
        pending_user = Pending.objects.get(user__username=newusr)
        verboseprint(" Pending user username: ",pending_user.user)
        verboseprint(" Pending user key: ",pending_user.pk)
        verboseprint(" Pending user token: ",pending_user.token)
        verboseprint(" Pending user admin_token: ",pending_user.admin_token)
        verboseprint(" Pending user email: ",pending_user)
        if verbose:
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint (pending_user.user)
        verboseprint ('4a. Using the user token and user username to query views.VerifyEmail')
        body1 = {
            'user': newusr,
            'token': pending_user.token,
        }
        response = self.client.get('/verify_email', body1, format='json', headers=headers).content
        verboseprint(response[:999])

        verboseprint ('5a. Confirming that a user without an official email is not activated')
        self.assertFalse(pending_user.user.is_active)

        verboseprint ('6a. Using the admin token and new user username to query views.ValidateUser')
        body2 = {
            'user': newusr,
            'token': pending_user.admin_token
        }
        verboseprint(body2)
        response = self.client.get('/validate_user', body2, format='json', headers=headers).content
        verboseprint(response[:999])
        #pending_user.save()


        verboseprint ('7a. Confirming that a user without an official email is activated')
        boarded_user = User.objects.get(username=newusr)
        verboseprint(boarded_user)
        self.assertTrue(boarded_user.is_active)

        verboseprint ('\n------------ A user with official email (series b) : -------')


        verboseprint ('2b. Making a request to views.NewRegistration with new user request') 
        country = Country.objects.get(name='country')
        newusr='pet'
        body = {
            'email': 'pet@voroskereszt.hu',
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
        verboseprint(response)
        
        verboseprint ('3b. Accessing the Pending users table to obtain the user\'s token')
        pending_user = Pending.objects.get(user__username=newusr)
        verboseprint(" Pending user username: ",pending_user.user)
        verboseprint(" Pending user key: ",pending_user.pk)
        verboseprint(" Pending user token: ",pending_user.token)
        verboseprint(" Pending user admin_token: ",pending_user.admin_token)
        verboseprint(" Pending user email: ",pending_user)
        if verbose:
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint (pending_user.user)

        verboseprint ('4b. Using the user token and user username to query views.VerifyEmail')
        body1 = {
            'user': newusr,
            'token': pending_user.token,
        }
        verboseprint(body1)
        response = self.client.get('/verify_email', body1, format='json', headers=headers).content
        verboseprint(response[:27])

        verboseprint ('5b. Confirming that a user with an official email is activated')
        boarded_user = User.objects.get(username=newusr)
        verboseprint(boarded_user)
        self.assertTrue(boarded_user.is_active)
#       self.assertIsNotNone(response.get('expires')) #just another assertion example
