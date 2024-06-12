from django.contrib.auth.models import AnonymousUser, User
from django.test import override_settings

from api import models
from main.settings import env
from main.test_case import APITestCase

FAKE_REDIS_CACHE = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("CACHE_TEST_REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}


class CacheForUserMiddlewareTest(APITestCase):
    fixtures = ["DisasterTypes", "Actions"]

    @override_settings(CACHES=FAKE_REDIS_CACHE)
    def test_caches_for_user(self):
        user = User.objects.create(username="jo")
        region = models.Region.objects.create(name=1)
        country1 = models.Country.objects.create(name="abc", region=region)
        country2 = models.Country.objects.create(name="xyz")
        body = {
            "countries": [country1.id, country2.id],
            "dtype": 7,
            "summary": "test",
            "description": "this is a test description",
            "bulletin": "3",
            "num_assisted": 100,
            "visibility": models.VisibilityChoices.PUBLIC,
            "sources": [
                {"stype": "Government", "spec": "A source"},
                {"stype": "Other", "spec": "Another source"},
            ],
            "actions_taken": [
                {"organization": "NTLS", "summary": "actions taken", "actions": ["37", "30", "39"]},
            ],
            "dref": "2",
            "appeal": "1",
            "contacts": [{"ctype": "Originator", "name": "jo", "title": "head", "email": "123"}],
            "user": user.id,
        }
        self.client.force_authenticate(user=user)
        with self.capture_on_commit_callbacks(execute=True):
            self.client.post("/api/v2/create_field_report/", body, format="json").json()

        response = self.client.get("/api/v2/field_report/", HTTP_ACCEPT_LANGUAGE="en")
        response_json = response.json()
        self.assert_200(response)
        self.assertEquals(response_json["count"], 1)

        # Create a new object
        with self.capture_on_commit_callbacks(execute=True):
            self.client.post("/api/v2/create_field_report/", body, format="json").json()

        # The result should be cached, the user only sees one object
        response = self.client.get("/api/v2/field_report/", HTTP_ACCEPT_LANGUAGE="en")
        response_json = response.json()
        self.assert_200(response)
        self.assertEquals(response_json["count"], 1)

        # A different user, accessing for the first time should see both items
        user2 = User.objects.create(username="john")
        self.client.force_authenticate(user=user2)
        response = self.client.get("/api/v2/field_report/", HTTP_ACCEPT_LANGUAGE="en")
        response_json = response.json()
        self.assert_200(response)
        self.assertEquals(response_json["count"], 2)

    @override_settings(CACHES=FAKE_REDIS_CACHE)
    def test_caches_for_anonymous_user(self):
        user = User.objects.create(username="jo")
        region = models.Region.objects.create(name=1)
        country1 = models.Country.objects.create(name="abc", region=region)
        country2 = models.Country.objects.create(name="xyz")
        body = {
            "countries": [country1.id, country2.id],
            "dtype": 7,
            "summary": "test",
            "description": "this is a test description",
            "bulletin": "3",
            "num_assisted": 100,
            "visibility": models.VisibilityChoices.PUBLIC,
            "sources": [
                {"stype": "Government", "spec": "A source"},
                {"stype": "Other", "spec": "Another source"},
            ],
            "actions_taken": [
                {"organization": "NTLS", "summary": "actions taken", "actions": ["37", "30", "39"]},
            ],
            "dref": "2",
            "appeal": "1",
            "contacts": [{"ctype": "Originator", "name": "jo", "title": "head", "email": "123"}],
            "user": user.id,
        }
        self.client.force_authenticate(user=user)
        with self.capture_on_commit_callbacks(execute=True):
            self.client.post("/api/v2/create_field_report/", body, format="json").json()

        self.client.force_authenticate(user=AnonymousUser())
        response = self.client.get("/api/v2/field_report/", HTTP_ACCEPT_LANGUAGE="en")
        response_json = response.json()
        self.assert_200(response)
        self.assertEquals(response_json["count"], 1)

        # Create a new object
        self.client.force_authenticate(user=user)
        with self.capture_on_commit_callbacks(execute=True):
            self.client.post("/api/v2/create_field_report/", body, format="json").json()

        # The result should be cached, the user only sees one object
        self.client.force_authenticate(user=AnonymousUser())
        response = self.client.get("/api/v2/field_report/", HTTP_ACCEPT_LANGUAGE="en")
        response_json = response.json()
        self.assert_200(response)
        self.assertEquals(response_json["count"], 1)
