from snapshottest.django import TestCase

from .models import Project
from api.factories import country


class TestDeploymentsModelsProject(TestCase):
    def test_deployments_models_project(self):
        project_model = Project(name="Test Project", reporting_ns=country.CountryFactory.build())
        self.assertMatchSnapshot(project_model)
