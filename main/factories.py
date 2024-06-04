import factory
from django.contrib.auth.models import Group


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Group
