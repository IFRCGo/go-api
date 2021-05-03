import factory
from factory import fuzzy

from .. import models
from . import country


class DistrictFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.District

    name = fuzzy.FuzzyText(length=100)
    code = fuzzy.FuzzyText(length=10)
    country = factory.SubFactory(country.CountryFactory)
    is_enclave = fuzzy.FuzzyChoice([True, False])
    is_deprecated = fuzzy.FuzzyChoice([True, False])
    wb_population = fuzzy.FuzzyInteger(0)
    wb_year = fuzzy.FuzzyText(length=4)
