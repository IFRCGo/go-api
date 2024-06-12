import factory
from factory import fuzzy

from deployments.models import MolnixTag


class MolnixTagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MolnixTag

    molnix_id = factory.Sequence(lambda n: n)
    description = fuzzy.FuzzyText(length=512)
    color = fuzzy.FuzzyText(length=6)
    tag_type = fuzzy.FuzzyChoice(choices=["regular", "language"])
    tag_category = fuzzy.FuzzyChoice(choices=["molnix_language", "molnix_region", "molnix_operation"])

    @factory.lazy_attribute
    def name(self):
        return f"{self.tag_category}-{self.molnix_id}"

    @factory.post_generation
    def groups(self, create, extracted, **_):
        if not create:
            return
        if extracted:
            for item in extracted:
                self.groups.add(item)
