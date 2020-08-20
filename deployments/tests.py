from snapshottest.django import TestCase

from deployments.factories import project


class TestProjectAPI(TestCase):
    def test_project_list_zero(self):
        response = self.client.get("/api/v2/project/")
        self.assertEqual(response.status_code, 200)
        self.assertMatchSnapshot(response.content)

    def test_project_list_one(self):
        project.ProjectFactory.create()
        response = self.client.get("/api/v2/project/")
        self.assertEqual(response.status_code, 200)
        self.assertMatchSnapshot(response.content)
