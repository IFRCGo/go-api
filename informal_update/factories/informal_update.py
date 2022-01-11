import factory
import datetime
import pytz
from factory import fuzzy

from django.core.files.base import ContentFile

from api.factories import disaster_type
from informal_update.models import (
    InformalUpdate,
    InformalGraphicMap,
    ReferenceUrls,
    InformalReferences
)


class ReferenceUrlsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReferenceUrls

    url = factory.Sequence(lambda n: f'https://{n}@xyz.com')


class InformalRefrenceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InformalReferences

    date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    source_description = fuzzy.FuzzyText(length=50)


class InformalGraphicMapFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InformalGraphicMap

    # file = factory.LazyAttribute(
    #     lambda _: ContentFile(
    #         factory.django.ImageField()._make_data({"width": 32, "height": 32}),
    #         "file.png",
    #     )
    # )
    # caption = fuzzy.FuzzyText(length=50)


class InformalUpdateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InformalUpdate

    hazard_type = factory.SubFactory(disaster_type.DisasterTypeFactory)
    title = fuzzy.FuzzyText(length=300)
    situational_overview = fuzzy.FuzzyText(length=200)
    originator_name = fuzzy.FuzzyText(length=50)
    originator_title = fuzzy.FuzzyText(length=50)
    originator_email = fuzzy.FuzzyText(length=50)
    originator_phone = fuzzy.FuzzyInteger(0, 9)

    ifrc_name = fuzzy.FuzzyText(length=50)
    ifrc_title = fuzzy.FuzzyText(length=50)
    ifrc_email = fuzzy.FuzzyText(length=50)
    ifrc_phone = fuzzy.FuzzyInteger(0, 9)

    share_with = fuzzy.FuzzyChoice(InformalUpdate.InformalShareWith)

    @factory.post_generation
    def references(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for reference in extracted:
                self.references.add(reference)

    @factory.post_generation
    def map(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for map in extracted:
                self.map.add(map)

    @factory.post_generation
    def graphics(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for graphic in extracted:
                self.graphics.add(graphic)

    # @classmethod
    # def _create(cls, model_class, *args, **kwargs):
    #     references = InformalRefrenceFactory.create_batch(3)
    #     map = InformalGraphicMapFactory.create_batch(3)
    #     graphics = InformalGraphicMapFactory.create_batch(3)
    #     informal_update = super()._create(model_class, *args, **kwargs)
    #     for obj in references:
    #         informal_update.references.add(obj)
    #     for obj in map:
    #         informal_update.map.add(obj)
    #     for obj in graphics:
    #         informal_update.graphics.add(obj)
    #     return informal_update
