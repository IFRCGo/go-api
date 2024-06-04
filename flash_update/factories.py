import factory
from django.core.files.base import ContentFile
from factory import fuzzy

from api.factories import disaster_type
from api.models import ActionCategory, ActionOrg, ActionType
from flash_update.models import (
    DonorGroup,
    Donors,
    FlashAction,
    FlashGraphicMap,
    FlashUpdate,
)


class FlashGraphicMapFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FlashGraphicMap

    file = factory.LazyAttribute(
        lambda _: ContentFile(factory.django.ImageField()._make_data({"width": 1024, "height": 768}), "flash_update.jpg")
    )


class FlashActionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FlashAction

    name = fuzzy.FuzzyText(length=50)
    organizations = fuzzy.FuzzyChoice(ActionOrg.choices)
    flash_update_types = fuzzy.FuzzyChoice(ActionType.choices)
    category = fuzzy.FuzzyChoice(ActionCategory.choices)
    tooltip_text = fuzzy.FuzzyText(length=50)


class FlashUpdateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FlashUpdate

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

    share_with = fuzzy.FuzzyChoice(FlashUpdate.FlashShareWith)

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


class DonorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Donors


class DonorGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DonorGroup
