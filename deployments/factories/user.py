import factory
from django.contrib.auth import get_user_model


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: "user_%d" % n)
    email = factory.Sequence(lambda n: "user_%d@ifrc.org" % n)
