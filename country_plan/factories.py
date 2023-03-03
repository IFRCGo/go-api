import factory

from .models import CountryPlan


class CountryPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CountryPlan
