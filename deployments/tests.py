from snapshottest.django import TestCase


class TestProjectAPI(TestCase):
    def test_project_list(self):
        response = self.client.get("/api/v2/project/")
        self.assertEqual(response.status_code, 200)
        self.assertMatchSnapshot(response.content)
