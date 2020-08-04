from rest_framework.authtoken.models import Token
from rest_framework import test

from django.db import DEFAULT_DB_ALIAS, connections
from django.contrib.auth.models import User


class APITestCase(test.APITestCase):
    """
    Base TestCase
    """
    def setUp(self):
        self.root_user = User.objects.create_user(
            username='root@test.com',
            first_name='Root',
            last_name='Toot',
            password='admin123',
            email='root@test.com',
            is_superuser=True,
            is_staff=True,
        )

        self.user = User.objects.create_user(
            username='jon@dave.com',
            first_name='Jon',
            last_name='Mon',
            password='test123',
            email='jon@dave.com',
        )

        self.ifrc_user = User.objects.create_user(
            username='jon@@ifrc.org',
            first_name='IFRC',
            last_name='GO',
            password='test123',
            email='jon@@ifrc.org',
        )

    def authenticate(self, user=None):
        user = user or self.user
        api_key, created = Token.objects.get_or_create(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token {}'.format(api_key)
        )
        return api_key

    @classmethod
    def capture_on_commit_callbacks(cls, *, using=DEFAULT_DB_ALIAS, execute=False):
        """
        This method ensures that transaction.on_commit are not reverted back
        Usages:
        self.capture_on_commit_callbacks(execute=True):
            resp = self.client.post(url, body)
        """
        return CaptureOnCommitCallbacksContext(using=using, execute=execute)


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
