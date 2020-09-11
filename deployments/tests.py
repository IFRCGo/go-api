from snapshottest.django import TestCase
from unittest import mock

import datetime
import pytz
import pydash

import json
import factory.random

from deployments.factories import project, user
from api.factories import country, district

from deployments.models import Project, VisibilityCharChoices


class TestProjectAPI(TestCase):
    def setUp(self):
        factory.random.reseed_random(
            42
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

    @mock.patch(
        "django.utils.timezone.now",
        lambda: datetime.datetime(2019, 3, 23, 0, 0, 0, 123456, tzinfo=pytz.UTC),
    )
    def test_project_list_two(self):
        project.ProjectFactory.create_batch(2, visibility=VisibilityCharChoices.PUBLIC)
        response = self.client.get("/api/v2/project/")
        self.assertEqual(response.status_code, 200)
        self.assertMatchSnapshot(json.loads(response.content))

    @mock.patch(
        "django.utils.timezone.now",
        lambda: datetime.datetime(2019, 3, 23, 0, 0, 0, 123456, tzinfo=pytz.UTC),
    )
    def test_project_create(self):
        # authenticate
        new_user = user.UserFactory.create()
        self.client.force_login(new_user)

        # create project
        new_project_name = "Mock Project for Create API Test"
        new_project = project.ProjectFactory.stub(
            name=new_project_name,
            visibility=VisibilityCharChoices.PUBLIC,
            user=new_user,
        )
        new_country = country.CountryFactory()
        new_district = district.DistrictFactory(country=new_country)
        new_project = pydash.omit(
            new_project,
            [
                "user",
                "reporting_ns",
                "project_country",
                "event",
                "dtype",
                "regional_project",
            ],
        )
        new_project["reporting_ns"] = new_country.id
        new_project["project_country"] = new_country.id
        new_project["project_districts"] = [new_district.id]

        # submit create request
        response = self.client.post(
            "/api/v2/project/", new_project, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertMatchSnapshot(json.loads(response.content))
        self.assertTrue(Project.objects.get(name=new_project_name))
