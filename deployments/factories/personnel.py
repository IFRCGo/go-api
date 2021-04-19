import factory

from api.factories.country import CountryFactory
from api.factories.region import RegionFactory
from deployments.models import (
    Personnel,
    PersonnelDeployment,
)


class PersonnelDeploymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PersonnelDeployment

    country_deployed_to = factory.SubFactory(CountryFactory)
    region_deployed_to = factory.SubFactory(RegionFactory)


class PersonnelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Personnel

    deployment = factory.SubFactory(PersonnelDeploymentFactory)
