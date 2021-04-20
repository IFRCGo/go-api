import datetime
import pytz
import pydash

import json
from unittest import mock

from main.test_case import SnapshotTestCase
from deployments.factories.user import UserFactory
from deployments.factories.project import ProjectFactory
from api.factories import country, district

from deployments.models import Project, VisibilityCharChoices

from .factories.personnel import PersonnelFactory


class TestProjectAPI(SnapshotTestCase):
    maxDiff = None

    @mock.patch(
        "django.utils.timezone.now",
        lambda: datetime.datetime(2019, 3, 23, 0, 0, 0, 123456, tzinfo=pytz.UTC),
    )
    def test_project_list_zero(self):
        # submit list request
        response = self.client.get("/api/v2/project/")

        # check response
        self.assert_200(response)
        self.assertMatchSnapshot(json.loads(response.content))

    @mock.patch(
        "django.utils.timezone.now",
        lambda: datetime.datetime(2019, 3, 23, 0, 0, 0, 123456, tzinfo=pytz.UTC),
    )
    def test_project_list_one(self):
        # create instance
        ProjectFactory.create(visibility=VisibilityCharChoices.PUBLIC)

        # submit list request
        response = self.client.get("/api/v2/project/")

        # check response
        self.assert_200(response)
        self.assertMatchSnapshot(json.loads(response.content))

    @mock.patch(
        "django.utils.timezone.now",
        lambda: datetime.datetime(2019, 3, 23, 0, 0, 0, 123456, tzinfo=pytz.UTC),
    )
    def test_project_list_two(self):
        # create instances
        ProjectFactory.create_batch(2, visibility=VisibilityCharChoices.PUBLIC)

        # submit list request
        response = self.client.get("/api/v2/project/")

        # check response
        self.assert_200(response)
        self.assertMatchSnapshot(json.loads(response.content))

    @mock.patch(
        "django.utils.timezone.now",
        lambda: datetime.datetime(2019, 3, 23, 0, 0, 0, 123456, tzinfo=pytz.UTC),
    )
    def test_project_create(self):
        # authenticate
        new_user = UserFactory.create()
        self.authenticate(new_user)

        # create project
        new_project_name = "Mock Project for Create API Test"
        new_project = ProjectFactory.stub(
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
        response = self.client.post("/api/v2/project/", new_project, format='json')

        # check response
        self.assert_201(response)
        self.assertMatchSnapshot(json.loads(response.content))
        self.assertTrue(Project.objects.get(name=new_project_name))

    @mock.patch(
        "django.utils.timezone.now",
        lambda: datetime.datetime(2019, 3, 23, 0, 0, 0, 123456, tzinfo=pytz.UTC),
    )
    def test_project_read(self):
        # create instance
        new_project = ProjectFactory.create(
            visibility=VisibilityCharChoices.PUBLIC
        )

        # submit read request
        response = self.client.get(f"/api/v2/project/{new_project.pk}/")

        # check response
        self.assert_200(response)
        self.assertMatchSnapshot(json.loads(response.content))

    @mock.patch(
        "django.utils.timezone.now",
        lambda: datetime.datetime(2019, 3, 23, 0, 0, 0, 123456, tzinfo=pytz.UTC),
    )
    def test_project_update(self):
        # create instance
        new_project = ProjectFactory.create(
            visibility=VisibilityCharChoices.PUBLIC
        )

        # authenticate
        self.authenticate()

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
        response = self.client.put(f"/api/v2/project/{new_project['id']}/", new_project, format='json')

        # check response
        self.assert_200(response)
        self.assertMatchSnapshot(json.loads(response.content))
        self.assertTrue(Project.objects.get(name=new_project_name))

    @mock.patch(
        "django.utils.timezone.now",
        lambda: datetime.datetime(2019, 3, 23, 0, 0, 0, 123456, tzinfo=pytz.UTC),
    )
    def test_project_delete(self):
        # create instance
        new_project = ProjectFactory.create(
            visibility=VisibilityCharChoices.PUBLIC
        )

        # authenticate
        self.authenticate()

        # submit delete request
        response = self.client.delete("/api/v2/project/{}/".format(new_project.pk))

        # check response
        self.assert_204(response)
        self.assertMatchSnapshot(response.content)
        self.assertFalse(Project.objects.count())

    def test_personnel_csv_api(self):
        [PersonnelFactory() for i in range(10)]

        url = '/api/v2/personnel/?format=csv'
        resp = self.client.get(url)
        self.assert_401(resp)

        self.authenticate()
        resp = self.client.get(url)
        self.assert_200(resp)
        self.assertMatchSnapshot(resp.content.decode('utf-8'))
