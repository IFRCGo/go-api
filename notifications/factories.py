import factory
from factory import fuzzy

from deployments.factories.user import UserFactory

from .models import AlertSubscription, HazardType, SurgeAlert, SurgeAlertStatus


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


class AlertSubscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AlertSubscription

    user = factory.SubFactory(UserFactory)

    @factory.post_generation
    def countries(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for country in extracted:
                self.countries.add(country)

    @factory.post_generation
    def regions(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for region in extracted:
                self.regions.add(region)

    @factory.post_generation
    def hazard_types(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for alert_type in extracted:
                self.hazard_types.add(alert_type)


class HazardTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HazardType
