import string

import factory
from django.core.files.base import ContentFile
from factory import fuzzy

from .. import models
from . import region

CODE_ATTEMPTS = 100


def unused_code(field: str, length: int) -> str:
    """Country `field` code of `length` lowercase letters that no existing Country holds.

    `Country.iso` and `Country.iso3` are unique. Lowercase keeps generated codes out of the
    uppercase space that tests pin to specific values.
    """
    fuzzer = fuzzy.FuzzyText(length=length, chars=string.ascii_lowercase)
    taken = set(models.Country.objects.values_list(field, flat=True))
    for _ in range(CODE_ATTEMPTS):
        code = fuzzer.fuzz()
        if code not in taken:
            return code
    raise RuntimeError(f"No free {length}-character {field} found for CountryFactory")


class CountryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Country

    name = fuzzy.FuzzyText(length=50, prefix="country-")
    record_type = fuzzy.FuzzyChoice(models.CountryType)
    iso = factory.LazyFunction(lambda: unused_code("iso", 2))
    iso3 = factory.LazyFunction(lambda: unused_code("iso3", 3))
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
