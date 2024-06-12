import factory
from django.core.files.base import ContentFile
from factory import fuzzy

from .. import models
from . import region


class CountryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Country

    name = fuzzy.FuzzyText(length=50, prefix="country-")
    record_type = fuzzy.FuzzyChoice(models.CountryType)
    iso = fuzzy.FuzzyText(length=2)
    iso3 = fuzzy.FuzzyText(length=3)
    society_name = fuzzy.FuzzyText(length=50, prefix="society-name-")
    society_url = fuzzy.FuzzyText(length=200)
    url_ifrc = fuzzy.FuzzyText(length=200)
    region = factory.SubFactory(region.RegionFactory)
    overview = fuzzy.FuzzyText(length=500)
    key_priorities = fuzzy.FuzzyText(length=500)
    inform_score = fuzzy.FuzzyDecimal(0)
    logo = factory.LazyAttribute(
        lambda _: ContentFile(
            factory.django.ImageField()._make_data({"width": 32, "height": 32}),
            "logo.png",
        )
    )
    wb_population = fuzzy.FuzzyInteger(0)
    wb_year = fuzzy.FuzzyText(length=4)
