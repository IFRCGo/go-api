# 1. Create two users to function as gatekeepers
# 2. Make a request to views.NewRegistration with new user request
# 3. Access the Pending users table to obtain the user's token
# 4. Use the user token and user username to query views.VerifyEmail
# 5. Confirm that a user with an official email is activated, and a user without an official email is not activated
# 6. Use the admin token and new user username to query views.ValidateUser
# 7. Confirm that a user without an official email is activated.

import uuid
from datetime import timedelta
from unittest import mock

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.contrib.auth.models import User
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from api.models import Country, Profile
from deployments.factories.user import UserFactory
from main.test_case import APITestCase as GoAPITestCase

from .models import Pending, UserExternalToken


class TwoGatekeepersTest(APITestCase):
    def setUp(self):
        user1 = User.objects.create(username="jo", email="jo@arcs.org.af")
        user1.set_password("12345678")
        user1.save()
        user2 = User.objects.create(username="ke", email="ke@arcs.org.af")
        user2.set_password("12345678")
        user2.save()
        Country.objects.create(name="country")

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
        country = Country.objects.get(name="country")
        # We started to use the email as the username for new registrations
        newusr = "pet@voroskereszt.hu"
        body = {
            "email": newusr,
            "username": newusr,
            "password": "87654321",
            "country": country.pk,
            "organization_type": "OTHR",
            "organization": "Zoo",
            "first_name": "Peter",
            "last_name": "Falk",
            "justification": "aaaa",
            "city": "kathmandu",
        }
        headers = {"CONTENT_TYPE": "application/json"}
        resp = self.client.post("/register", data=body, format="json")
        # json.loads(resp.content): 'status': 'ok'
        self.assertEqual(resp.status_code, 200)

        # 3b. Accessing the Pending users table to obtain the user\'s token
        pending_user = Pending.objects.get(user__username=newusr)

        # 4b. Using the user token and user username to query views.VerifyEmail
        body1 = {
            "user": newusr,
            "token": pending_user.token,
        }
        resp = self.client.get("/verify_email", body1, format="json", headers=headers)
        # resp.content: ...validated your email address and your IFRC Go account is now approved
        self.assertEqual(resp.status_code, 200)

        # 5b. Confirming that a user with an official email is activated
        boarded_user = User.objects.get(username=newusr)
        self.assertTrue(boarded_user.is_active)

    @mock.patch("registrations.serializers.send_notification_create")
    def test_user_registration(self, send_notification_create):
        country = Country.objects.get(name="country")
        User.objects.create(username="testuser@gmail.com")
        old_user_count = User.objects.filter(is_active=False).count()
        newusr = "testuser@gmail.com"
        data = {
            "email": newusr,
            "username": "tetsts",
            "password": "87654321",
            "country": country.pk,
            "organization_type": "OTHR",
            "organization": "Zoo",
            "first_name": "Peter",
            "last_name": "Falk",
            "justification": "aaaa",
            "city": "kathmandu",
        }
        resp = self.client.post("/register", json=data)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(User.objects.filter(is_active=False).count(), old_user_count)  # No new user to be created

        # update the email now should create user
        data["email"] = "test@gmail.com"
        resp = self.client.post("/register", data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(User.objects.filter(is_active=False).count(), old_user_count + 1)

        # check profile is created for the user
        self.assertEqual(Profile.objects.filter(user__email=data["email"]).exists(), True)

        # check if the notification is called
        self.assertTrue(send_notification_create.is_called())


class UserExternalTokenTest(GoAPITestCase):

    def setUp(self):
        super().setUp()
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096, backend=default_backend())
        public_key = private_key.public_key()
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Serialize public key
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        self.OIDC_RSA_PRIVATE_KEY = private_key_pem.decode("utf-8")
        self.OIDC_RSA_PUBLIC_KEY = public_key_pem.decode("utf-8")

    def test_external_token_with_key(self):
        self.client.force_authenticate(self.user)
        url = f"/api/v2/user/{self.user.id}/accepted_license_terms/"

        # accept the terms and conditions
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.accepted_montandon_license_terms, True)

        data = {"title": "ok"}

        with override_settings(
            OIDC_RSA_PRIVATE_KEY=self.OIDC_RSA_PRIVATE_KEY,
            OIDC_RSA_PUBLIC_KEY=self.OIDC_RSA_PUBLIC_KEY,
        ):
            response = self.client.post("/api/v2/external-token/", data, format="json")
        self.assertEqual(response.status_code, 201)
        # get_token() returns the generated JWT on the creation path (a header.payload.signature string).
        body = response.json()
        self.assertTrue(body["token"])
        self.assertEqual(body["token"].count("."), 2)
        # id is returned so clients can later revoke the token
        self.assertEqual(body["id"], UserExternalToken.objects.get().id)

    def test_external_token_with_no_keys(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/v2/external-token/")
        self.assertEqual(response.status_code, 400)

    def test_verify_active_token(self):
        token = UserExternalToken.objects.create(
            title="active",
            user=self.user,
            expire_timestamp=timezone.now() + timedelta(days=1),
        )
        # NOTE: verify is unauthenticated (server-to-server introspection)
        response = self.client.post("/api/v2/external-token/verify/", {"jti": str(token.jti)}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"active": True})

    def test_verify_disabled_token(self):
        token = UserExternalToken.objects.create(
            title="disabled",
            user=self.user,
            expire_timestamp=timezone.now() + timedelta(days=1),
            is_disabled=True,
        )
        response = self.client.post("/api/v2/external-token/verify/", {"jti": str(token.jti)}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"active": False})

    def test_verify_expired_token(self):
        token = UserExternalToken.objects.create(
            title="expired",
            user=self.user,
            expire_timestamp=timezone.now() - timedelta(days=1),
        )
        response = self.client.post("/api/v2/external-token/verify/", {"jti": str(token.jti)}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"active": False})

    def test_verify_old_token(self):
        token = UserExternalToken.objects.create(
            title="old",
            user=self.user,
            expire_timestamp=timezone.now() + timedelta(days=1),
            is_old_token=True,
        )
        response = self.client.post("/api/v2/external-token/verify/", {"jti": str(token.jti)}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"active": False})

    def test_verify_unknown_jti(self):
        response = self.client.post("/api/v2/external-token/verify/", {"jti": str(uuid.uuid4())}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"active": False})

    def test_verify_invalid_jti(self):
        response = self.client.post("/api/v2/external-token/verify/", {"jti": "not-a-uuid"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_revoke_own_token(self):
        self.client.force_authenticate(self.user)
        token = UserExternalToken.objects.create(
            title="revoke-me",
            user=self.user,
            expire_timestamp=timezone.now() + timedelta(days=1),
        )

        # NOTE: verify is unauthenticated (server-to-server introspection)
        # Token is active before revocation.
        response = self.client.post("/api/v2/external-token/verify/", {"jti": str(token.jti)}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"active": True})

        response = self.client.post(f"/api/v2/external-token/{token.id}/revoke/")
        self.assertEqual(response.status_code, 200)
        token.refresh_from_db()
        self.assertIs(token.is_disabled, True)

        # Token is inactive after revocation.
        response = self.client.post("/api/v2/external-token/verify/", {"jti": str(token.jti)}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"active": False})

    def test_revoke_already_revoked_token_errors(self):
        self.client.force_authenticate(self.user)
        token = UserExternalToken.objects.create(
            title="revoke-twice",
            user=self.user,
            expire_timestamp=timezone.now() + timedelta(days=1),
        )
        response = self.client.post(f"/api/v2/external-token/{token.id}/revoke/")
        self.assertEqual(response.status_code, 200)

        # A second revoke on the same token is a client error.
        response = self.client.post(f"/api/v2/external-token/{token.id}/revoke/")
        self.assertEqual(response.status_code, 400)

    def test_revoke_other_users_token_not_found(self):
        other_user = UserFactory.create(
            username="other@dave.com",
            first_name="Other",
            last_name="User",
            password="test123",
            email="other@dave.com",
        )
        token = UserExternalToken.objects.create(
            title="not-mine",
            user=other_user,
            expire_timestamp=timezone.now() + timedelta(days=1),
        )
        self.client.force_authenticate(self.user)
        response = self.client.post(f"/api/v2/external-token/{token.id}/revoke/")
        self.assertEqual(response.status_code, 404)
        token.refresh_from_db()
        self.assertIs(token.is_disabled, False)

    def test_revoke_requires_auth(self):
        token = UserExternalToken.objects.create(
            title="revoke-unauth",
            user=self.user,
            expire_timestamp=timezone.now() + timedelta(days=1),
        )
        response = self.client.post(f"/api/v2/external-token/{token.id}/revoke/")
        self.assertEqual(response.status_code, 401)

    def test_list_includes_is_disabled(self):
        self.client.force_authenticate(self.user)
        UserExternalToken.objects.create(
            title="listed",
            user=self.user,
            expire_timestamp=timezone.now() + timedelta(days=1),
        )
        response = self.client.get("/api/v2/external-token/")
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertIn("is_disabled", results[0])
        # get_token() returns None for stored instances, so the JWT is never re-exposed on list.
        self.assertIsNone(results[0]["token"])
