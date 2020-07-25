import factory
from factory import fuzzy

from .. import models

class RegionFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Region

    name = fuzzy.FuzzyChoice(models.RegionName)
