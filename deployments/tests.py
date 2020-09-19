from snapshottest.django import TestCase
from unittest import mock
from django.core import management

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
        management.call_command("flush", "--no-input")
        factory.random.reseed_random(42)

    @mock.patch(
        "django.utils.timezone.now",
        lambda: datetime.datetime(2019, 3, 23, 0, 0, 0, 123456, tzinfo=pytz.UTC),
    )
    def test_project_list_zero(self):
        # submit list request
        response = self.client.get("/api/v2/project/")

        # check response
        self.assertEqual(response.status_code, 200)
        self.assertMatchSnapshot(json.loads(response.content))

    @mock.patch(
        "django.utils.timezone.now",
        lambda: datetime.datetime(2019, 3, 23, 0, 0, 0, 123456, tzinfo=pytz.UTC),
    )
    def test_project_list_one(self):
        # create instance
        project.ProjectFactory.create(visibility=VisibilityCharChoices.PUBLIC)

        # submit list request
        response = self.client.get("/api/v2/project/")

        # check response
        self.assertEqual(response.status_code, 200)
        self.assertMatchSnapshot(json.loads(response.content))

    @mock.patch(
        "django.utils.timezone.now",
        lambda: datetime.datetime(2019, 3, 23, 0, 0, 0, 123456, tzinfo=pytz.UTC),
    )
    def test_project_list_two(self):
        # create instances
        project.ProjectFactory.create_batch(2, visibility=VisibilityCharChoices.PUBLIC)

        # submit list request
        response = self.client.get("/api/v2/project/")

        # check response
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

        # check response
        self.assertEqual(response.status_code, 201)
        self.assertMatchSnapshot(json.loads(response.content))
        self.assertTrue(Project.objects.get(name=new_project_name))

    @mock.patch(
        "django.utils.timezone.now",
        lambda: datetime.datetime(2019, 3, 23, 0, 0, 0, 123456, tzinfo=pytz.UTC),
    )
    def test_project_read(self):
        # create instance
        new_project = project.ProjectFactory.create(
            visibility=VisibilityCharChoices.PUBLIC
        )

        # submit read request
        response = self.client.get("/api/v2/project/{}/".format(new_project.pk))

        # check response
        self.assertEqual(response.status_code, 200)
        self.assertMatchSnapshot(json.loads(response.content))

    @mock.patch(
        "django.utils.timezone.now",
        lambda: datetime.datetime(2019, 3, 23, 0, 0, 0, 123456, tzinfo=pytz.UTC),
    )
    def test_project_update(self):
        # create instance
        new_project = project.ProjectFactory.create(
            visibility=VisibilityCharChoices.PUBLIC
        )

        # authenticate
        new_user = user.UserFactory.create()
        self.client.force_login(new_user)

        new_project = pydash.omit(
            new_project,
            ["_state", "modified_at", "user", "event", "dtype", "regional_project"],
        )
        # update project name
        new_project_name = "Mock Project for Update API Test"
        new_country = country.CountryFactory()
        new_district = district.DistrictFactory(country=new_country)
        new_project["name"] = new_project_name
        new_project["reporting_ns"] = new_country.id
        new_project["project_country"] = new_country.id
        new_project["project_districts"] = [new_district.id]

        # submit update request
        response = self.client.put(
            "/api/v2/project/{}/".format(new_project["id"]),
            new_project,
            content_type="application/json",
        )

        # check response
        self.assertEqual(response.status_code, 200)
        self.assertMatchSnapshot(json.loads(response.content))
        self.assertTrue(Project.objects.get(name=new_project_name))

    @mock.patch(
        "django.utils.timezone.now",
        lambda: datetime.datetime(2019, 3, 23, 0, 0, 0, 123456, tzinfo=pytz.UTC),
    )
    def test_project_delete(self):
        # create instance
        new_project = project.ProjectFactory.create(
            visibility=VisibilityCharChoices.PUBLIC
        )

        # authenticate
        new_user = user.UserFactory.create()
        self.client.force_login(new_user)

        # submit delete request
        response = self.client.delete("/api/v2/project/{}/".format(new_project.pk))

        # check response
        self.assertEqual(response.status_code, 204)
        self.assertMatchSnapshot(response.content)
        self.assertFalse(Project.objects.all().count())
