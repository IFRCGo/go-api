import factory
from factory import fuzzy

from api.factories import disaster_type
from api.models import (
    ActionOrg,
    ActionType,
    ActionCategory
)
from informal_update.models import (
    InformalUpdate,
    InformalGraphicMap,
    InformalAction
)


class InformalGraphicMapFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InformalGraphicMap


class InformalActionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InformalAction

    name = fuzzy.FuzzyText(length=50)
    organizations = fuzzy.FuzzyChoice(ActionOrg.CHOICES)
    informal_update_types = fuzzy.FuzzyChoice(ActionType.CHOICES)
    category = fuzzy.FuzzyChoice(ActionCategory.CHOICES)
    tooltip_text = fuzzy.FuzzyText(length=50)


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
