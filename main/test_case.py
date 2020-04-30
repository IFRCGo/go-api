from rest_framework.authtoken.models import Token
from rest_framework import test

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
