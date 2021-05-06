import snapshottest.django as django_snapshottest
import factory.random

from rest_framework.authtoken.models import Token
from rest_framework import test, status

from django.core import management
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import DEFAULT_DB_ALIAS, connections

from api.models import Country
from deployments.factories.user import UserFactory

from lang.translation import AmazonTranslate


class GoAPITestMixin():
    """
    Base TestCase
    """
    client_class = test.APIClient

    def setUp(self):
        super().setUp()

        self.root_user = UserFactory.create(
            username='root@test.com',
            first_name='Root',
            last_name='Toot',
            password='admin123',
            email='root@test.com',
            is_superuser=True,
            is_staff=True,
        )

        self.user = UserFactory.create(
            username='jon@dave.com',
            first_name='Jon',
            last_name='Mon',
            password='test123',
            email='jon@dave.com',
        )

        self.ifrc_user = UserFactory.create(
            username='jon@@ifrc.org',
            first_name='IFRC',
            last_name='GO',
            password='test123',
            email='jon@@ifrc.org',
        )
        self.aws_translator = AmazonTranslate()

        self.ifrc_permission = Permission.objects.create(
            codename='ifrc_admin',
            content_type=ContentType.objects.get_for_model(Country),
            name='IFRC Admin',
        )
        self.ifrc_user.user_permissions.add(self.ifrc_permission)

    def authenticate(self, user=None):
        if user is None:
            if not hasattr(self, 'user'):
                self.user = UserFactory.create(
                    username='jon@dave.com',
                    first_name='Jon',
                    last_name='Mon',
                    password='test123',
                    email='jon@dave.com',
                )
            user = self.user
        api_key, created = Token.objects.get_or_create(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token {}'.format(api_key)
        )
        return api_key

    def assert_http_code(self, response, code):
        self.assertEqual(response.status_code, code, response.content)

    def assert_200(self, response):
        self.assert_http_code(response, status.HTTP_200_OK)

    def assert_201(self, response):
        self.assert_http_code(response, status.HTTP_201_CREATED)

    def assert_202(self, response):
        self.assert_http_code(response, status.HTTP_202_ACCEPTED)

    def assert_204(self, response):
        self.assert_http_code(response, status.HTTP_204_NO_CONTENT)

    def assert_302(self, response):
        self.assert_http_code(response, status.HTTP_302_FOUND)

    def assert_400(self, response):
        self.assert_http_code(response, status.HTTP_400_BAD_REQUEST)

    def assert_401(self, response):
        self.assert_http_code(response, status.HTTP_401_UNAUTHORIZED)

    def assert_403(self, response):
        self.assert_http_code(response, status.HTTP_403_FORBIDDEN)

    def assert_404(self, response):
        self.assert_http_code(response, status.HTTP_404_NOT_FOUND)

    def assert_405(self, response):
        self.assert_http_code(response, status.HTTP_405_METHOD_NOT_ALLOWED)

    def assert_500(self, response):
        self.assert_http_code(response, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @classmethod
    def capture_on_commit_callbacks(cls, *, using=DEFAULT_DB_ALIAS, execute=False):
        """
        This method ensures that transaction.on_commit are not reverted back
        Usages:
        self.capture_on_commit_callbacks(execute=True):
            resp = self.client.post(url, body)
        """
        return CaptureOnCommitCallbacksContext(using=using, execute=execute)


class APITestCase(GoAPITestMixin, test.APITestCase):
    pass


class SnapshotTestCase(GoAPITestMixin, django_snapshottest.TestCase):
    def setUp(self):
        management.call_command("flush", "--no-input")
        factory.random.reseed_random(42)


class CaptureOnCommitCallbacksContext:
    def __init__(self, *, using=DEFAULT_DB_ALIAS, execute=False):
        self.using = using
        self.execute = execute
        self.callbacks = None

    def __enter__(self):
        if self.callbacks is not None:
            raise RuntimeError("Cannot re-enter captureOnCommitCallbacks()")
        self.start_count = len(connections[self.using].run_on_commit)
        self.callbacks = []
        return self.callbacks

    def __exit__(self, exc_type, exc_valuei, exc_traceback):
        run_on_commit = connections[self.using].run_on_commit[self.start_count:]
        self.callbacks[:] = [func for sids, func in run_on_commit]
        if exc_type is None and self.execute:
            for callback in self.callbacks:
                callback()
