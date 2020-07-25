import factory
from django.contrib.auth import get_user_model

class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = get_user_model()
