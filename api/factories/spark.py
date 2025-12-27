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


class DimInventoryItemStatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimInventoryItemStatus

    id = factory.Iterator(["AVAILABLE", "BROKEN", "INCORRECT", "QUALITY", "OK", "CHECK"])
    name = factory.Iterator(["Available", "Broken", "Incorrect item", "Quality Issue", "Available", "To be checked"])


class DimInventoryModuleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimInventoryModule

    id = factory.Sequence(lambda n: f"TESTMODULE{n:02d}#{n:01d}")
    unit_of_measure = fuzzy.FuzzyChoice(["ea", "kg", "g", "m2"])
    item_id = factory.Sequence(lambda n: f"TESTMODULE{n:02d}")
    type = fuzzy.FuzzyChoice(["purchase", "sales", "inventory"])


class DimInventoryOwnerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimInventoryOwner

    id = factory.Sequence(lambda n: f"ifrc#CODE{n:02d}")
    name = fuzzy.FuzzyText(length=16)


class DimInventoryTransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimInventoryTransaction

    id = factory.Sequence(lambda n: f"{n:06d}")
    reference_category = fuzzy.FuzzyChoice(["Purchase Order", "Sales Order", "Counting", "Transaction"])
    reference_number = factory.Sequence(lambda n: f"TESTREF{n:04d}")
    excluded_from_inventory_value = fuzzy.FuzzyChoice([True, False])


class DimInventoryTransactionLineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimInventoryTransactionLine

    id = factory.Sequence(lambda n: f"{n:010d}")
    item_status = factory.Iterator(["OK", "NULL", "CHECK"])
    item_status_name = factory.Iterator(["Available", "NULL","To be checked"])
    product = factory.Sequence(lambda n: f"TESTPRODUCT{n:05d}")
    voucher_physical = factory.Sequence(lambda n: f"ifrc#{n:05d}")
    project = factory.Sequence(lambda n: f"ifrc#{n:05d}")
    batch = factory.Sequence(lambda n: f"TESTBATCH{n:06d}")
    warehouse = fuzzy.FuzzyText(length=10, prefix="WH{n:02d}")
    owner = fuzzy.FuzzyText(length=12, prefix="ifrc#OWN{n:01d}")
    inventory_transaction = factory.Sequence(lambda n: f"{n:06d}")
    project_category = fuzzy.FuzzyText(length=30, prefix="ifrc#{n:04d}i - TESTCATEGORY")
    activity = fuzzy.FuzzyText(length=20, prefix="ifrc#TESTACTIVITY{n:03d}")
    physical_date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    financial_date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    status_date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    expected_date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    quantity = fuzzy.FuzzyDecimal(0, 1000)
    cost_amount_posted = fuzzy.FuzzyDecimal(-1000000, 1000000)
    cost_amount_adjustment = fuzzy.FuzzyDecimal(-10000, 10000)
    status = fuzzy.FuzzyChoice(["Purchased", "Sold", "Deducted", "Ordered", "Received"])
    packing_slip = factory.LazyFunction(lambda: fuzzy.FuzzyDate(datetime.date(2008, 1, 1)).fuzz().strftime("%d/%m/%Y"))
    packing_slip_returned = fuzzy.FuzzyChoice([True, False])


class DimInventoryTransactionOriginFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimInventoryTransactionOrigin

    id = factory.Sequence(lambda n: f"{n:06d}")
    reference_category = fuzzy.FuzzyChoice(["Purchase Order", "Sales Order", "Counting", "Transaction"])
    reference_number = factory.Sequence(lambda n: f"TESTREF{n:07d}")
    excluded_from_inventory_value = fuzzy.FuzzyChoice(["No", "Yes"])
