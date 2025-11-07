
import factory

from factory import fuzzy

from eap.models import EAPRegistration, EAPStatus, EAPType, SimplifiedEAP

class EAPRegistrationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EAPRegistration

    status = fuzzy.FuzzyChoice(EAPStatus)
    eap_type = fuzzy.FuzzyChoice(EAPType)

    @factory.post_generation
    def partners(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for partner in extracted:
                self.partners.add(partner)


class SimplifiedEAPFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SimplifiedEAP

    seap_timeframe = fuzzy.FuzzyInteger(2)
    total_budget = fuzzy.FuzzyInteger(1000, 1000000)
    readiness_budget = fuzzy.FuzzyInteger(1000, 1000000)
    pre_positioning_budget = fuzzy.FuzzyInteger(1000, 1000000)
    early_action_budget = fuzzy.FuzzyInteger(1000, 1000000)
