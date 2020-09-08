from snapshottest.django import TestCase
from unittest import mock

import datetime
import pytz

import json
import factory.random

from deployments.factories import project
from deployments.models import VisibilityCharChoices


class TestProjectAPI(TestCase):
    def setUp(self):
        factory.random.reseed_random(
            111
        )  # https://factoryboy.readthedocs.io/en/latest/recipes.html#using-reproducible-randomness

    @mock.patch(
        "django.utils.timezone.now",
        lambda: datetime.datetime(2019, 3, 23, 0, 0, 0, 123456, tzinfo=pytz.UTC),
    )
    def test_project_list_zero(self):
        response = self.client.get("/api/v2/project/")
        self.assertEqual(response.status_code, 200)
        self.assertMatchSnapshot(json.loads(response.content))

    @mock.patch(
        "django.utils.timezone.now",
        lambda: datetime.datetime(2019, 3, 23, 0, 0, 0, 123456, tzinfo=pytz.UTC),
    )
    def test_project_list_one(self):
        project.ProjectFactory.create(visibility=VisibilityCharChoices.PUBLIC)
        response = self.client.get("/api/v2/project/")
        self.assertEqual(response.status_code, 200)
        self.assertMatchSnapshot(json.loads(response.content))
