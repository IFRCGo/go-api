import factory
from factory import fuzzy

from .. import models


class DisasterTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DisasterType

    name = fuzzy.FuzzyText(length=100)
    summary = fuzzy.FuzzyText(length=500)
