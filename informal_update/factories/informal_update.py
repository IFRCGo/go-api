import factory
from factory import fuzzy

from api.factories import disaster_type
from .informal_graphic_map import InformalGraphicMapFactory
from .informal_refrences import InformalRefrenceFactory
from informal_update.models import InformalUpdate


class InformalUpdateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InformalUpdate

    hazard_type = factory.SubFactory(disaster_type.DisasterTypeFactory)
    title = fuzzy.FuzzyText(length=300)
    situational_overview = fuzzy.FuzzyText(length=200)
    map = factory.SubFactory(InformalGraphicMapFactory)
    graphics = factory.SubFactory(InformalGraphicMapFactory)
    originator_name = fuzzy.FuzzyText(length=50)
    originator_title = fuzzy.FuzzyText(length=50)
    originator_email = fuzzy.FuzzyText(length=50)
    originator_phone = fuzzy.FuzzyInteger(0, 9)

    ifrc_name = fuzzy.FuzzyText(length=50)
    ifrc_title = fuzzy.FuzzyText(length=50)
    ifrc_email = fuzzy.FuzzyText(length=50)
    ifrc_phone = fuzzy.FuzzyInteger(0, 9)

    share_with = fuzzy.FuzzyChoice(InformalUpdate.InformalShareWith)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        references = InformalRefrenceFactory.create_batch(3)
        informal_update = super()._create(model_class, *args, **kwargs)
        for obj in references:
            informal_update.references.add(obj)
        return informal_update
