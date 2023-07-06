# 1. Create two users to function as gatekeepers
# 2. Make a request to views.NewRegistration with new user request
# 3. Access the Pending users table to obtain the user's token
# 4. Use the user token and user username to query views.VerifyEmail
# 5. Confirm that a user with an official email is activated, and a user without an official email is not activated
# 6. Use the admin token and new user username to query views.ValidateUser
# 7. Confirm that a user without an official email is activated.

from unittest import mock

from rest_framework.test import APITestCase
from django.contrib.auth.models import User

from .models import Pending
from api.models import Country, Profile
from .utils import send_notification_create


class TwoGatekeepersTest(APITestCase):
    def setUp(self):
        user1 = User.objects.create(username='jo', email='jo@arcs.org.af')
        user1.set_password('12345678')
        user1.save()
        user2 = User.objects.create(username='ke', email='ke@arcs.org.af')
        user2.set_password('12345678')
        user2.save()
        Country.objects.create(name='country')

    # def test_two_gatekeepers(self):
    #     # 1. Created two users to function as gatekeepers (with checkable email)
    #     # 2a. Making a request to views.NewRegistration with new user request
    #     country = Country.objects.get(name='country')
    #     # We started to use the email as the username for new registrations
    #     newusr = 'pe@doesnotexist.hu'
    #     body = {
    #         'email': newusr,
    #         'username': newusr,
    #         'password': '87654321',
    #         'country': country.pk,
    #         'organizationType': 'OTHR',
    #         'organization': 'Zoo',
    #         'firstname': 'Peter',
    #         'lastname': 'Falk',
    #         'contact': [{'email': 'jo@arcs.org.af'}, {'email': 'ke@arcs.org.af'}]
    #     }
    #     headers = {'CONTENT_TYPE': 'application/json'}
    #     resp = self.client.post('/register', body, format='json', headers=headers)
    #     # json.loads(resp.content): 'status': 'ok'
    #     self.assertEqual(resp.status_code, 200)

    #     # 3a. Accessing the Pending users table to obtain the user\'s token
    #     pending_user = Pending.objects.get(user__username=newusr)
    #     # 4a. Using the user token and user username to query views.VerifyEmail
    #     body1 = {
    #         'user': newusr,
    #         'token': pending_user.token,
    #     }
    #     resp = self.client.get('/verify_email', body1, format='json', headers=headers)
    #     # resp.content: We are verifying your IFRC references and will notify you
    #     self.assertEqual(resp.status_code, 200)

    #     # 5a. Confirming that a user without an official email is not activated
    #     self.assertFalse(pending_user.user.is_active)

    #     # 6a_1. Using the first admin token and new user username to query views.ValidateUser
    #     body2 = {
    #         'user': newusr,
    #         'token': pending_user.admin_token_1
    #     }
    #     resp = self.client.get('/validate_user', body2, format='json', headers=headers)
    #     # resp.content: The IFRC GO user account is still not active because an other administrator has to approve it also
    #     self.assertEqual(resp.status_code, 200)

    #     # 6a_1repeat. The first token should be unusable now to query views.ValidateUser again
    #     resp = self.client.get('/validate_user', body2, format='json', headers=headers)
    #     # resp.content: You, as an administrator has already confirmed the registration of pe user
    #     self.assertEqual(resp.status_code, 400)

    #     # 7a_1. Confirming that a user without an official email is STILL NOT activated
    #     boarded_user = User.objects.get(username=newusr)
    #     self.assertFalse(boarded_user.is_active)

    #     # 6a_2. Using the second admin token and new user username to query views.ValidateUser
    #     body3 = {
    #         'user': newusr,
    #         'token': pending_user.admin_token_2
    #     }
    #     resp = self.client.get('/validate_user', body3, format='json', headers=headers)
    #     # resp.content: The IFRC GO user account is now active and a confirmation email has been sent
    #     self.assertEqual(resp.status_code, 200)

    #     # 7a_2. Confirming that a user without an official email is finally ACTIVATED
    #     boarded_user = User.objects.get(username=newusr)
    #     self.assertTrue(boarded_user.is_active)

    def test_official_email(self):
        # 2b. Making a request to views.NewRegistration with new user request
        country = Country.objects.get(name='country')
        # We started to use the email as the username for new registrations
        newusr = 'pet@voroskereszt.hu'
        body = {
            'email': newusr,
            'username': newusr,
            'password': '87654321',
            'country': country.pk,
            'organization_type': 'OTHR',
            'organization': 'Zoo',
            'first_name': 'Peter',
            'last_name': 'Falk',
            'justification': 'aaaa',
            'city': 'kathmandu'
        }
        headers = {'CONTENT_TYPE': 'application/json'}
        resp = self.client.post('/register', data=body, format='json')
        # json.loads(resp.content): 'status': 'ok'
        self.assertEqual(resp.status_code, 200)

        # 3b. Accessing the Pending users table to obtain the user\'s token
        pending_user = Pending.objects.get(user__username=newusr)

        # 4b. Using the user token and user username to query views.VerifyEmail
        body1 = {
            'user': newusr,
            'token': pending_user.token,
        }
        resp = self.client.get('/verify_email', body1, format='json', headers=headers)
        # resp.content: ...validated your email address and your IFRC Go account is now approved
        self.assertEqual(resp.status_code, 200)

        # 5b. Confirming that a user with an official email is activated
        boarded_user = User.objects.get(username=newusr)
        self.assertTrue(boarded_user.is_active)

    @mock.patch('registrations.serializers.send_notification_create')
    def test_user_registration(self, send_notification_create):
        country = Country.objects.get(name='country')
        User.objects.create(username='testuser@gmail.com')
        old_user_count = User.objects.filter(is_active=False).count()
        newusr = 'testuser@gmail.com'
        data = {
            'email': newusr,
            'username': "tetsts",
            'password': '87654321',
            'country': country.pk,
            'organization_type': 'OTHR',
            'organization': 'Zoo',
            'first_name': 'Peter',
            'last_name': 'Falk',
            'justification': 'aaaa',
            'city': 'kathmandu'
        }
        resp = self.client.post('/register', json=data)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(User.objects.filter(is_active=False).count(), old_user_count)  # No new user to be cr

        # update the email now should create user
        data['email'] = "test@gmail.com"
        resp = self.client.post('/register', data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(User.objects.filter(is_active=False).count(), old_user_count + 1)

        # check profile is created for the user
        self.assertEqual(Profile.objects.filter(user__email=data['email']).exists(), True)

        # check if the notification is called
        self.assertTrue(send_notification_create.is_called())
