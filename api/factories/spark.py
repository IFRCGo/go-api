import datetime

import factory
import pytz
from django.utils import timezone
from factory import fuzzy

from .. import models
from .country import CountryFactory

class DimAgreementLineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimAgreementLine

    agreement_line_id = factory.Sequence(lambda n: f"PA-AA{n:07d}-{n:02d}")
    agreement_id = factory.Sequence(lambda n: f"PA-AA{n:07d}")
    line_number = factory.Sequence(lambda n: n + 1)
    product = factory.Sequence(lambda n: f"TESTPRODUCT{n:05d}")
    product_category = fuzzy.FuzzyText(length=8)
    effective_date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=timezone.utc))
    expiration_date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=timezone.utc))
    commitment_type = fuzzy.FuzzyText(length=20)
    committed_quantity = fuzzy.FuzzyDecimal(0, 100)
    committed_amount = fuzzy.FuzzyDecimal(0, 1000)
    delivery_term = fuzzy.FuzzyText(length=3)
    unit_of_measure = fuzzy.FuzzyChoice(["ea", "kg", "g", "m2"])
    price_per_unit = fuzzy.FuzzyDecimal(0, 500)
    line_discount_percent = fuzzy.FuzzyDecimal(0, 0.5)


class DimAppealFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimAppeal

    id = factory.Sequence(lambda n: f"TESTAPPEAL{n:04d}")
    appeal_name = fuzzy.FuzzyText(length=20)


class DimBuyerGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimBuyerGroup

    code = factory.Sequence(lambda n: f"TESTBUYERGROUP{n:04d}")
    name = fuzzy.FuzzyText(length=20)


class DimConsignmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimConsignment

    id = factory.Sequence(lambda n: f"CSGN{n:06d}")
    delivery_mode = fuzzy.FuzzyChoice(["AIR", "ROAD", "SEA", "SEARO"])


class DimDeliveryModeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimDeliveryMode

    id = fuzzy.FuzzyText(length=6)
    description = fuzzy.FuzzyText(length=20)


class DimDonorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimDonor

    donor_code = factory.Sequence(lambda n: f"TESTDONOR{n:03d}")
    donor_name = fuzzy.FuzzyText(length=20)


class DimInventoryItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimInventoryItem

    id = fuzzy.FuzzyText(length=10)
    unit_of_measure = fuzzy.FuzzyChoice(["ea", "kg", "g", "m2"])
