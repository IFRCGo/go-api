import factory
from factory import fuzzy
import datetime
import pytz

from informal_update.models import ReferenceUrls, InformalReferences


class ReferenceUrlsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReferenceUrls

    url = factory.Sequence(lambda n: f'https://{n}@xyz.com')


class InformalRefrenceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InformalReferences

    date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    source_description = fuzzy.FuzzyText(length=50)

