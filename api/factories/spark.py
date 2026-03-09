import datetime

import factory
import pytz
from django.utils import timezone
from factory import fuzzy

from .. import models


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

    fabric_id = factory.Sequence(lambda n: f"TESTAPPEAL{n:04d}")
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
    item_status_name = factory.Iterator(["Available", "NULL", "To be checked"])
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


class DimItemBatchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimItemBatch

    id = factory.Sequence(lambda n: f"TESTBATCH{n:06d}")
    customer = factory.Sequence(lambda n: f"ifrc#VENDOR{n:03d}")
    vendor = fuzzy.FuzzyText(length=20, prefix="TESTVENDOR{n:06d}")
    unit_volume = fuzzy.FuzzyDecimal(0, 100000)
    unit_weight = fuzzy.FuzzyDecimal(0, 100000)
    expiration_date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=timezone.utc))
    vendor_expiration_date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=timezone.utc))
    price = fuzzy.FuzzyDecimal(0, 1000000000)
    currency = fuzzy.FuzzyChoice(["USD", "CHF", "EUR", "JPY", "AED"])


class DimLocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimLocation

    id = factory.Sequence(lambda n: f"TESTLOC{n:03d}")
    location = "STOCK"


class DimLogisticsLocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimLogisticsLocation

    id = factory.Sequence(lambda n: f"{n:09d}")
    postal_address = fuzzy.FuzzyText(length=30)
    country = fuzzy.FuzzyText(length=3)
    city = fuzzy.FuzzyText(length=16)
    street = fuzzy.FuzzyText(length=30)
    zip_code = fuzzy.FuzzyText(length=9)


class DimPackingSlipLineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimPackingSlipLine

    id = factory.Sequence(lambda n: f"TESTSLIP{n:05d}")
    sales_order_line = factory.Sequence(lambda n: f"TESTSLIP{n:05d} - {n:02d}")
    delivery_date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=timezone.utc))
    quantity_delivered = fuzzy.FuzzyDecimal(0, 100000)


class DimProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimProduct

    id = factory.Sequence(lambda n: f"TESTPRODUCT{n:05d}")
    name = fuzzy.FuzzyText(length=20)
    type = fuzzy.FuzzyChoice(["Item", "Service"])
    unit_of_measure = fuzzy.FuzzyChoice(["ea", "kg", "g", "m2"])
    product_category = fuzzy.FuzzyText(length=30, prefix="ifrc#{n:04d}i - TESTCATEGORY")


class DimProductCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimProductCategory

    category_code = fuzzy.FuzzyText(length=8)
    name = fuzzy.FuzzyText(length=20)
    parent_category_code = fuzzy.FuzzyText(length=4)
    level = fuzzy.FuzzyInteger(1, 5)


class DimProductReceiptLineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimProductReceiptLine

    id = factory.Sequence(lambda n: f"TESTPRODUCTRECEIPTLINE{n:05d}#{n:02d}")
    product_receipt = factory.Sequence(lambda n: f"TESTPRODUCTRECEIPTLINE{n:05d}")
    purchase_order_line = factory.Sequence(lambda n: f"TESTPURCHASEORDER{n:05d}")
    received_quantity = fuzzy.FuzzyDecimal(0, 1000)
    unit = fuzzy.FuzzyChoice(["ea", "kg", "g", "m2"])
    value_accounting_currency = fuzzy.FuzzyDecimal(-1000000, 1000000)


class DimProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimProject

    id = factory.Sequence(lambda n: f"TESTPROJECT{n:03d}")
    project_name = fuzzy.FuzzyText(length=30)


class DimPurchaseOrderLineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimPurchaseOrderLine

    id = factory.Sequence(lambda n: f"TESTPURCHASEORDERLINE{n:05d}")
    line_number = factory.Sequence(lambda n: n + 1)
    description = fuzzy.FuzzyText(length=20)
    purchase_order = factory.Sequence(lambda n: f"TESTPURCHASEORDER{n:05d}")
    product = factory.Sequence(lambda n: f"TESTPRODUCT{n:05d}")
    product_category = "TESTPRODUCT"
    status = fuzzy.FuzzyChoice(["Open Order", "Received", "Invoiced", "Cancelled"])
    type = "OrderLine"
    agreement = "NULL"
    unit_of_measure = fuzzy.FuzzyChoice(["ea", "kg", "g", "m2"])
    currency_code = fuzzy.FuzzyChoice(["USD", "CHF", "EUR", "JPY", "AED"])
    humanitarian_procurement_center_transaction = fuzzy.FuzzyChoice([True, False])
    ordered_quantity_inventory_unit = fuzzy.FuzzyDecimal(0, 100000)
    ordered_quantity_purchasing_unit = fuzzy.FuzzyDecimal(-100000, 100000)
    price_per_unit = fuzzy.FuzzyDecimal(0, 100000000)
    price_per_unit_accounting_currency = fuzzy.FuzzyDecimal(0, 100000000)
    donated_price_per_unit = fuzzy.FuzzyDecimal(0, 100000000)
    donated_price_per_unit_accounting_currency = fuzzy.FuzzyDecimal(0, 100000000)
    amount = fuzzy.FuzzyDecimal(-100000000, 1000000000)
    amount_accounting_currency = fuzzy.FuzzyDecimal(-100000000, 1000000000)
    donated_amount = fuzzy.FuzzyDecimal(0, 1000000000)
    donated_amount_accounting_currency = fuzzy.FuzzyDecimal(0, 1000000000)
    actual_weight = fuzzy.FuzzyDecimal(0, 100000)
    actual_volume = fuzzy.FuzzyDecimal(0, 100000)
    warehouse = fuzzy.FuzzyText(length=10, prefix="WH{n:02d}")
    owner = fuzzy.FuzzyText(length=12, prefix="TESTOWNER{n:02d}")
    item_batch = factory.Sequence(lambda n: f"TESTBATCH{n:05d}")
    consignment = factory.Sequence(lambda n: f"CSGN{n:06d}")
    financial_dimension_project = factory.Sequence(lambda n: f"TESTPRJ{n:05d}")
    financial_dimension_appeal = factory.Sequence(lambda n: f"TESTAPPEAL{n:04d}")
    financial_dimension_funding_arrangement = factory.Sequence(lambda n: f"TESTFUND{n:04d}")
    requested_delivery_date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    confirmed_delivery_date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    delivery_mode = fuzzy.FuzzyChoice(["AIR", "ROAD", "NULL"])
    delivery_name = fuzzy.FuzzyText(length=20)
    delivery_address_description = fuzzy.FuzzyText(length=30)
    delivery_postal_address = fuzzy.FuzzyText(length=30)
    delivery_postal_address_country = fuzzy.FuzzyText(length=3)
    created_by = fuzzy.FuzzyText(length=12)
    created_datetime = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    modified_by = fuzzy.FuzzyText(length=12)
    modified_datetime = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))


class DimSalesOrderLineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimSalesOrderLine

    id = factory.Sequence(lambda n: f"SOL-{n:05d}")
    description = fuzzy.FuzzyText(length=20, prefix="sol-")
    product = factory.Sequence(lambda n: f"TESTPRODUCT{n:05d}")
    product_category = factory.Sequence(lambda n: f"PCAT{n:04d}")
    unit_of_measure = fuzzy.FuzzyChoice(["ea", "kg", "g", "m2"])
    currency_code = fuzzy.FuzzyChoice(["USD", "CHF", "EUR", "JPY", "AED"])
    status = fuzzy.FuzzyChoice(["Open", "Closed", "Pending"])
    type = fuzzy.FuzzyChoice(["OrderLine", "ReturnLine"])
    ordered_quantity_sales_unit = fuzzy.FuzzyDecimal(0, 100000)
    amount = fuzzy.FuzzyDecimal(-100000000, 1000000000)
    amount_accounting_currency = fuzzy.FuzzyDecimal(-100000000, 1000000000)
    price_per_unit = fuzzy.FuzzyDecimal(0, 100000000)
    price_per_unit_accounting_currency = fuzzy.FuzzyDecimal(0, 100000000)
    donated_price_per_unit = fuzzy.FuzzyDecimal(0, 100000000)
    donated_price_per_unit_accounting_currency = fuzzy.FuzzyDecimal(0, 100000000)
    donated_amount = fuzzy.FuzzyDecimal(0, 1000000000)
    donated_amount_accounting_currency = fuzzy.FuzzyDecimal(0, 1000000000)
    exchange_rate_factor = fuzzy.FuzzyDecimal(0, 10)
    delivery_mode = fuzzy.FuzzyChoice(["Air", "Road"])
    requested_shipping_date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    requested_receipt_date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    delivery_postal_address = fuzzy.FuzzyText(length=30, prefix="postal-")
    delivery_postal_address_country = fuzzy.FuzzyText(length=3)
    warehouse = factory.Sequence(lambda n: f"WH-{n:05d}")
    item_batch = factory.Sequence(lambda n: f"BATCH-{n:05d}")
    inventory_owner = fuzzy.FuzzyText(length=12, prefix="owner-")
    financial_dimension_project = factory.Sequence(lambda n: f"PRJ-{n:05d}")
    financial_dimension_appeal = factory.Sequence(lambda n: f"TESTAPPEAL{n:04d}")
    financial_dimension_funding_arrangement = fuzzy.FuzzyText(length=15, prefix="fund-")


class DimSiteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimSite

    id = factory.Sequence(lambda n: f"TESTSITE{n:02d}")
    name = fuzzy.FuzzyText(length=20)


class DimVendorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimVendor

    code = factory.Sequence(lambda n: f"TESTVENDOR{n:05d}")
    name = fuzzy.FuzzyText(length=20)


class DimVendorContactFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimVendorContact

    id = factory.Sequence(lambda n: f"VC-{n:05d}")
    first_name = fuzzy.FuzzyText(length=30)
    last_name = fuzzy.FuzzyText(length=30)
    active = fuzzy.FuzzyChoice([True, False])
    vendor = factory.Sequence(lambda n: f"TESTVENDOR{n:05d}")


class DimVendorContactEmailFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimVendorContactEmail

    id = factory.Sequence(lambda n: f"{n:06d}")
    email_address = factory.LazyAttribute(lambda obj: f"{obj.id.lower()}@example.com")
    primary = fuzzy.FuzzyChoice([True, False])


class DimVendorPhysicalAddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimVendorPhysicalAddress

    id = factory.Sequence(lambda n: f"VPA-{n:05d}")
    country = fuzzy.FuzzyText(length=3)
    city = fuzzy.FuzzyText(length=20)
    street = fuzzy.FuzzyText(length=20)
    valid_from = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    valid_to = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    zip_code = fuzzy.FuzzyText(length=9)


class DimWarehouseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DimWarehouse

    id = factory.Sequence(lambda n: f"WH{n:05d}")
    site = factory.Sequence(lambda n: f"TESTSITE{n:05d}")
    name = fuzzy.FuzzyText(length=20)
    country = fuzzy.FuzzyText(length=3)
    postal_address = fuzzy.FuzzyText(length=30)


class FctAgreementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.FctAgreement

    agreement_id = factory.Sequence(lambda n: f"PA-AA{n:07d}")
    status = fuzzy.FuzzyChoice(["Effective", "On hold", "Closed"])
    currency_code = fuzzy.FuzzyChoice(["USD", "CHF", "EUR", "JPY", "AED"])
    buyer_group = fuzzy.FuzzyText(length=12)
    vendor = factory.Sequence(lambda n: f"TESTVENDOR{n:05d}")
    parent_agreement = factory.Sequence(lambda n: f"PA-AA{n:07d}")
    managing_business_unit_organizational_unit = fuzzy.FuzzyText(length=20)
    requesting_department_organizational_unit = fuzzy.FuzzyText(length=20)
    preparer_worker = fuzzy.FuzzyText(length=12)
    classification = fuzzy.FuzzyChoice(["Local Service", "Global Service", "Regional Service", "Goods"])
    default_delivery_name = fuzzy.FuzzyText(length=20)
    default_payment_term = fuzzy.FuzzyText(length=20)
    document_title = fuzzy.FuzzyText(length=20)
    purpose = fuzzy.FuzzyText(length=20)
    document_external_reference = fuzzy.FuzzyText(length=20)
    code = factory.Sequence(lambda n: f"CLMX{n:06d}")
    workflow_status = fuzzy.FuzzyChoice(["Draft", "Active", "Closed"])
    default_agreement_line_effective_date = fuzzy.FuzzyDate(datetime.date(2008, 1, 1))
    default_agreement_line_expiration_date = fuzzy.FuzzyDate(datetime.date(2008, 1, 1))
    created_by = fuzzy.FuzzyText(length=12)
    created_datetime = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    modified_by = fuzzy.FuzzyText(length=12)
    modified_datetime = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))


class FctProductReceiptFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.FctProductReceipt

    id = factory.Sequence(lambda n: f"GRN-{n:05d}")
    purchase_order = factory.Sequence(lambda n: f"PO-{n:05d}")
    delivery_date = fuzzy.FuzzyDate(datetime.date(2008, 1, 1))


class FctPurchaseOrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.FctPurchaseOrder

    id = factory.Sequence(lambda n: f"FPO-{n:05d}")
    status = "Draft"
    delivery_mode = fuzzy.FuzzyChoice(["AIR", "ROAD", "SEA", "SEARO"])
    currency_code = fuzzy.FuzzyChoice(["USD", "CHF", "EUR", "JPY", "AED"])
    buyer_group = fuzzy.FuzzyText(length=12)
    vendor = factory.Sequence(lambda n: f"TESTVENDOR{n:05d}")
    agreement = factory.Sequence(lambda n: f"FA-AA{n:05d}")
    project = factory.Sequence(lambda n: f"TESTPROJECT{n:05d}")
    financial_dimension_funding_arrangement = fuzzy.FuzzyText(length=15)
    created_by_business_unit = fuzzy.FuzzyText(length=12)
    requested_by_organizational_unit = fuzzy.FuzzyText(length=12)
    sales_order = "NULL"
    in_kind_donation_pledge = factory.Sequence(lambda n: f"ifrc#{n:05d}")
    type = fuzzy.FuzzyChoice(["Purchase", "Return"])
    coordination_type = fuzzy.FuzzyText(length=12)
    apply_procurement_fees = fuzzy.FuzzyChoice([True, False])
    origin = fuzzy.FuzzyText(length=12)
    approval_status = fuzzy.FuzzyChoice(["Pending", "Approved", "Rejected"])
    customer_reference = fuzzy.FuzzyText(length=20)
    in_kind_donor_reference = fuzzy.FuzzyText(length=20)
    intercompany_origin = fuzzy.FuzzyText(length=12)
    exchange_rate = fuzzy.FuzzyDecimal(0, 10)
    created_by = fuzzy.FuzzyText(length=30)
    created_datetime = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    modified_by = fuzzy.FuzzyText(length=30)
    modified_datetime = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))


class FctSalesOrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.FctSalesOrder

    id = factory.Sequence(lambda n: f"FSO-{n:05d}")
    customer = fuzzy.FuzzyText(length=12)
    created_by_business_unit = fuzzy.FuzzyText(length=12)
    humanitarian_procurement_center_transaction = fuzzy.FuzzyChoice([True, False])
    customer_reference = fuzzy.FuzzyText(length=20)
    customer_requisition = fuzzy.FuzzyText(length=20)
    created_datetime = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))


class ProductCategoryHierarchyFlattenedFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProductCategoryHierarchyFlattened

    product_category = fuzzy.FuzzyText(length=7)
    level_4_product_category = fuzzy.FuzzyText(length=4)
    level_3_product_category = fuzzy.FuzzyText(length=1)
    level_2_product_category = "LVL#2_SUBMAIN"
    level_1_product_category = "LVL#1_MAIN"


class ItemCodeMappingFactory(factory.django.DjangoModelFactory):
    """Factory for ItemCodeMapping model."""

    class Meta:
        model = models.ItemCodeMapping

    code = factory.Sequence(lambda n: f"ITEM{n:05d}")
    url = factory.Faker("url")


class StockInventoryFactory(factory.django.DjangoModelFactory):
    """Factory for StockInventory model."""

    class Meta:
        model = models.StockInventory

    warehouse_id = factory.Sequence(lambda n: f"WH{n:03d}")
    warehouse = fuzzy.FuzzyText(length=20, prefix="Warehouse ")
    warehouse_country = fuzzy.FuzzyText(length=3)
    product_category = fuzzy.FuzzyText(length=20)
    item_name = fuzzy.FuzzyText(length=50)
    quantity = fuzzy.FuzzyDecimal(1.0, 1000.0, precision=2)
    unit_measurement = fuzzy.FuzzyChoice(["ea", "kg", "m", "litre", "box"])
