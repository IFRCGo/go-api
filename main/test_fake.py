from django.test import TestCase


class FakeTest(TestCase):
    """
    This test is for running migrations only
    docker-compose run --rm serve ./manage.py test -v 2 --pattern="test_fake.py""
    """
    def test_fake(self):
        pass
