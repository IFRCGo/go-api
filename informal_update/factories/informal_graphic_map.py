import factory
from factory import fuzzy
from django.core.files.base import ContentFile

from informal_update import models


class InformalGraphicMapFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.InformalGraphicMap

    file = factory.LazyAttribute(
        lambda _: ContentFile(
            factory.django.ImageField()._make_data({"width": 32, "height": 32}),
            "file.png",
        )
    )
    caption = fuzzy.FuzzyText(length=50)
