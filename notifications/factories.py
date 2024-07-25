import factory
from factory import fuzzy

from .models import SurgeAlert, SurgeAlertStatus


class SurgeAlertFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SurgeAlert

    message = fuzzy.FuzzyText(length=100)
    molnix_id = fuzzy.FuzzyInteger(low=1)
    atype = fuzzy.FuzzyInteger(low=1)
    category = fuzzy.FuzzyInteger(low=1)
    molnix_status = fuzzy.FuzzyChoice(choices=SurgeAlertStatus)

    @factory.post_generation
    def molnix_tags(self, create, extracted, **_):
        if not create:
            return
        if extracted:
            for item in extracted:
                self.molnix_tags.add(item)
