from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

import api.models as models
from api.admin import EventAdmin
from api.factories import country as countryFactory
from api.factories import event as eventFactory
from api.factories import field_report as fieldReportFactory
from api.factories import spark as sparkFactory
from api.factories.region import RegionFactory
from main.mock import erp_request_side_effect_mock


class DisasterTypeTest(TestCase):

    fixtures = ["DisasterTypes"]

    def test_disaster_type_data(self):
        objs = models.DisasterType.objects.all()
        self.assertEqual(len(objs), 24)


class EventTest(TestCase):

    fixtures = ["DisasterTypes"]

    def setUp(self):
        dtype = models.DisasterType.objects.get(pk=1)
        models.Event.objects.create(name="disaster1", summary="test disaster", dtype=dtype)
        event = models.Event.objects.create(name="disaster2", summary="another test disaster", dtype=dtype)
        models.KeyFigure.objects.create(event=event, number=7, deck="things", source="website")
        models.Snippet.objects.create(event=event, snippet="this is a snippet")

    def test_disaster_create(self):
        obj1 = models.Event.objects.get(name="disaster1")
        obj2 = models.Event.objects.get(name="disaster2")
        self.assertEqual(obj1.summary, "test disaster")
        self.assertEqual(obj2.summary, "another test disaster")
        keyfig = obj2.key_figures.all()
        self.assertEqual(keyfig[0].deck, "things")
        self.assertEqual(keyfig[0].number, "7")
        snippet = obj2.snippets.all()
        self.assertEqual(snippet[0].snippet, "this is a snippet")


class CountryTest(TestCase):

    fixtures = ["Regions", "Countries"]

    def test_country_data(self):
        regions = models.Region.objects.all()
        self.assertEqual(regions.count(), 5)
        countries = models.Country.objects.all()
        self.assertEqual(countries.count(), 274)


class ProfileTest(TestCase):
    def setUp(self):
        user = User.objects.create(username="username", first_name="pat", last_name="smith", password="password")
        user.profile.org = "org"
        user.profile.save()

    def test_profile_create(self):
        profile = models.Profile.objects.get(user__username="username")
        self.assertEqual(profile.org, "org")


class AppealTest(APITestCase):
    def setUp(self):
        # An appeal with needs_confirmation=True should not return the event in the API response.
        event = models.Event.objects.create(name="associated event", summary="foo")
        country = models.Country.objects.create(name="country")
        models.Appeal.objects.create(
            aid="test1", name="appeal", atype=1, code="abc", needs_confirmation=True, event=event, country=country
        )

    def test_unconfirmed_event(self):
        response = self.client.get("/api/v2/appeal/?code=abc")
        response = dict(dict(response.data)["results"][0])
        self.assertIsNone(response["event"])
        self.assertIsNotNone(response["country"])


class FieldReportTest(TestCase):

    fixtures = ["DisasterTypes"]

    def setUp(self):
        dtype = models.DisasterType.objects.get(pk=1)
        event = models.Event.objects.create(name="disaster1", summary="test disaster", dtype=dtype)
        country = models.Country.objects.create(name="country")
        report = models.FieldReport.objects.create(rid="test1", event=event, dtype=dtype)
        report.countries.add(country)

    def test_field_report_create(self):
        event = models.Event.objects.get(name="disaster1")
        country = models.Country.objects.get(name="country")
        self.assertEqual(event.field_reports.all()[0].countries.all()[0], country)
        obj = models.FieldReport.objects.get(rid="test1")
        self.assertEqual(obj.rid, "test1")
        self.assertEqual(obj.countries.all()[0], country)
        self.assertEqual(obj.event, event)
        self.assertIsNotNone(obj.report_date)

    @patch("requests.post", side_effect=erp_request_side_effect_mock)
    def test_ERP_related_field_report(self, mocked_requests_post):
        dtype = models.DisasterType.objects.get(pk=1)
        country = countryFactory.CountryFactory()
        event = eventFactory.EventFactory(name="disaster2", summary="test disaster 2", dtype=dtype)
        event.countries.set([country])
        report = fieldReportFactory.FieldReportFactory.create(
            rid="test2",
            event=event,
            dtype=dtype,
            ns_request_assistance=True,
        )
        ERP = models.ERPGUID.objects.get(api_guid="FindThisGUID")
        self.assertEqual(ERP.field_report_id, report.id)
        self.assertEqual(mocked_requests_post.called, True)


class ProfileTestDepartment(TestCase):
    def setUp(self):
        user = User.objects.create(username="test1", password="12345678!")
        user.profile.department = "testdepartment"
        user.save()

    def test_profile_create(self):
        obj = models.Profile.objects.get(user__username="test1")
        self.assertEqual(obj.department, "testdepartment")


class EventSeverityLevelHistoryTest(TestCase):

    fixtures = ["DisasterTypes"]

    def setUp(self):
        self.user = User.objects.create(username="username", first_name="pat", last_name="smith", password="password")
        self.region = RegionFactory()
        self.country = countryFactory.CountryFactory()
        self.dtype = models.DisasterType.objects.get(pk=1)

        self.event = eventFactory.EventFactory.create(
            dtype=self.dtype,
            ifrc_severity_level=models.AlertLevel.YELLOW,
        )
        self.event.regions.set([self.region])
        self.event.countries.set([self.country])
        self.event._current_user = self.user
        self.admin = EventAdmin(models.Event, AdminSite())
        self.factory = RequestFactory()

    def test_ifrc_severity_level_history_created_from_admin(self):
        # Simulate admin request
        request = self.factory.post("/")
        request.user = self.user

        # Update the instance
        self.event.ifrc_severity_level = models.AlertLevel.RED
        self.event.ifrc_severity_level_update_date = timezone.now()

        # Trigger admin save_model (where your logic lives)
        self.admin.save_model(request, self.event, None, change=True)

        history = models.EventSeverityLevelHistory.objects.filter(event=self.event)
        self.assertEqual(history.count(), 1)
        self.assertEqual(history[0].ifrc_severity_level, models.AlertLevel.RED)
        self.assertEqual(history[0].created_by, self.user)

    def test_no_history_created_if_severity_level_not_changed(self):
        # Save the event with the current severity level (no change)
        self.event.ifrc_severity_level = models.AlertLevel.YELLOW  # same as initial value
        self.event.save()

        history = models.EventSeverityLevelHistory.objects.filter(event=self.event)
        self.assertEqual(history.count(), 0)


class SparkModelStrTests(TestCase):
    def setUp(self):
        self.now = timezone.now()

    def _country(self):
        return models.Country.objects.create(name="Test Country", iso="TL", record_type=models.CountryType.COUNTRY)

    def test_dim_agreement_line_str(self):
        line = sparkFactory.DimAgreementLineFactory.create(
            agreement_line_id="FA-TEST001",
            agreement_id="FA-TEST001-01",
            line_number=1,
        )
        self.assertEqual(str(line), "FA-TEST001")

    def test_dim_appeal_str(self):
        appeal = sparkFactory.DimAppealFactory.create(fabric_id="AP-TEST001", appeal_name="Appeal")
        self.assertEqual(str(appeal), "AP-TEST001 - Appeal")

    def test_dim_buyer_group_str(self):
        buyer_group = sparkFactory.DimBuyerGroupFactory.create(code="BG-TEST001", name="Buyer Group")
        self.assertEqual(str(buyer_group), "BG-TEST001 - Buyer Group")

    def test_dim_consignment_str(self):
        consignment = sparkFactory.DimConsignmentFactory.create(id="C-TEST001", delivery_mode="Air")
        self.assertEqual(str(consignment), "C-TEST001 - Air")

    def test_dim_delivery_mode_str(self):
        delivery_mode = sparkFactory.DimDeliveryModeFactory.create(id="DM-TEST001", description="Test Description")
        self.assertEqual(str(delivery_mode), "DM-TEST001 - Test Description")

    def test_dim_donor_str(self):
        donor = sparkFactory.DimDonorFactory.create(donor_code="D-TEST001", donor_name="Donor")
        self.assertEqual(str(donor), "D-TEST001 - Donor")

    def test_dim_inventory_item_str(self):
        item = sparkFactory.DimInventoryItemFactory.create(id="ITEM-TEST001", unit_of_measure="KG")
        self.assertEqual(str(item), "ITEM-TEST001 - KG")

    def test_dim_inventory_item_status_str(self):
        status = sparkFactory.DimInventoryItemStatusFactory.create(id="STATUS-TEST001", name="Available")
        self.assertEqual(str(status), "STATUS-TEST001 - Available")

    def test_dim_inventory_module_str(self):
        module = sparkFactory.DimInventoryModuleFactory.create(
            id="MODULE-TEST001", unit_of_measure="KG", item_id="ITEM-TEST001", type="Type"
        )
        self.assertEqual(str(module), "MODULE-TEST001 - ITEM-TEST001")

    def test_dim_inventory_owner_str(self):
        owner = sparkFactory.DimInventoryOwnerFactory.create(id="OWNER-TEST001", name="Owner")
        self.assertEqual(str(owner), "OWNER-TEST001 - Owner")

    def test_dim_inventory_transaction_str_with_reference_number(self):
        transaction = sparkFactory.DimInventoryTransactionFactory.create(
            id="TRANSACTION-TEST001",
            reference_category="Cat",
            reference_number="Ref-1",
            excluded_from_inventory_value=False,
        )
        self.assertEqual(str(transaction), "TRANSACTION-TEST001 - Cat - Ref-1")

    def test_dim_inventory_transaction_str_without_reference_number(self):
        transaction = sparkFactory.DimInventoryTransactionFactory.create(
            id="TRANSACTION-TEST002",
            reference_category="Cat",
            reference_number=None,
            excluded_from_inventory_value=False,
        )
        self.assertEqual(str(transaction), "TRANSACTION-TEST002 - Cat")

    def test_dim_inventory_transaction_line_str_with_product_and_inventory(self):
        line = sparkFactory.DimInventoryTransactionLineFactory.create(
            id="TL-TEST001", product="Prod", inventory_transaction="INV-TEST001"
        )
        self.assertEqual(str(line), "TL-TEST001 - Prod - INV-TEST001")

    def test_dim_inventory_transaction_line_str_with_product_only(self):
        line = sparkFactory.DimInventoryTransactionLineFactory.create(id="TL-TEST002", product="Prod", inventory_transaction=None)
        self.assertEqual(str(line), "TL-TEST002 - Prod")

    def test_dim_inventory_transaction_line_str_base(self):
        line = sparkFactory.DimInventoryTransactionLineFactory.create(
            id="TL-TEST003",
            product=None,
            inventory_transaction=None,
        )
        self.assertEqual(str(line), "TL-TEST003")

    def test_dim_inventory_transaction_origin_str_with_reference_number(self):
        origin = sparkFactory.DimInventoryTransactionOriginFactory.create(
            id="O-TEST001",
            reference_category="Cat",
            reference_number="Ref-TEST001",
            excluded_from_inventory_value=False,
        )
        self.assertEqual(str(origin), "O-TEST001 - Cat - Ref-TEST001")

    def test_dim_inventory_transaction_origin_str_without_reference_number(self):
        origin = sparkFactory.DimInventoryTransactionOriginFactory.create(
            id="O-TEST002",
            reference_category="Cat",
            reference_number=None,
            excluded_from_inventory_value=False,
        )
        self.assertEqual(str(origin), "O-TEST002 - Cat")


class ExportRegulationModelTests(TestCase):
    """Tests for the export regulation models (CountryExportSnapshot, CountryExportSource, CountryExportEvidenceSnippet)."""

    def test_country_export_snapshot_str(self):
        """Test CountryExportSnapshot __str__ method."""
        snapshot = models.CountryExportSnapshot.objects.create(
            country_name="Germany",
            is_current=True,
            confidence="High",
            summary_text="Germany has straightforward export procedures for humanitarian goods.",
            status="success",
        )
        expected_str = f"Germany Export - {snapshot.generated_at.strftime('%Y-%m-%d')}"
        self.assertEqual(str(snapshot), expected_str)

    def test_country_export_snapshot_unique_current_constraint(self):
        """Test that only one current snapshot per country is allowed."""
        models.CountryExportSnapshot.objects.create(
            country_name="France",
            is_current=True,
            confidence="Medium",
            status="success",
        )
        # Creating another current snapshot for the same country should fail
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            models.CountryExportSnapshot.objects.create(
                country_name="France",
                is_current=True,
                confidence="High",
                status="success",
            )

    def test_country_export_snapshot_multiple_non_current_allowed(self):
        """Test that multiple non-current snapshots for the same country are allowed."""
        models.CountryExportSnapshot.objects.create(
            country_name="Spain",
            is_current=False,
            confidence="Low",
            status="success",
        )
        # Creating another non-current snapshot should work
        snapshot2 = models.CountryExportSnapshot.objects.create(
            country_name="Spain",
            is_current=False,
            confidence="Medium",
            status="success",
        )
        self.assertIsNotNone(snapshot2.id)
        self.assertEqual(models.CountryExportSnapshot.objects.filter(country_name="Spain").count(), 2)

    def test_country_export_source_str(self):
        """Test CountryExportSource __str__ method."""
        snapshot = models.CountryExportSnapshot.objects.create(
            country_name="Belgium",
            is_current=True,
            confidence="High",
            status="success",
        )
        source = models.CountryExportSource.objects.create(
            snapshot=snapshot,
            rank=1,
            url="https://example.com/export-info",
            title="Belgian Export Procedures Guide",
            publisher="Belgian Customs",
            authority_score=90,
            total_score=85,
        )
        self.assertEqual(str(source), "Belgian Export Procedures Guide (Rank 1)")

    def test_country_export_source_ordering(self):
        """Test that sources are ordered by snapshot and rank."""
        snapshot = models.CountryExportSnapshot.objects.create(
            country_name="Netherlands",
            is_current=True,
            confidence="Medium",
            status="success",
        )
        source2 = models.CountryExportSource.objects.create(
            snapshot=snapshot,
            rank=2,
            url="https://example.com/source2",
            title="Source 2",
        )
        source1 = models.CountryExportSource.objects.create(
            snapshot=snapshot,
            rank=1,
            url="https://example.com/source1",
            title="Source 1",
        )
        source3 = models.CountryExportSource.objects.create(
            snapshot=snapshot,
            rank=3,
            url="https://example.com/source3",
            title="Source 3",
        )
        sources = list(models.CountryExportSource.objects.filter(snapshot=snapshot))
        self.assertEqual(sources[0].rank, 1)
        self.assertEqual(sources[1].rank, 2)
        self.assertEqual(sources[2].rank, 3)

    def test_country_export_evidence_snippet_str(self):
        """Test CountryExportEvidenceSnippet __str__ method."""
        snapshot = models.CountryExportSnapshot.objects.create(
            country_name="Italy",
            is_current=True,
            confidence="Low",
            status="partial",
        )
        source = models.CountryExportSource.objects.create(
            snapshot=snapshot,
            rank=1,
            url="https://example.com/italy-export",
            title="Italy Export Regulations",
        )
        snippet = models.CountryExportEvidenceSnippet.objects.create(
            source=source,
            snippet_order=1,
            snippet_text="Italy requires a specific export declaration for humanitarian goods being shipped to third countries.",
        )
        # The __str__ method truncates to first 50 chars of snippet_text
        self.assertEqual(str(snippet), "Export Snippet 1 - Italy requires a specific export declaration for h...")

    def test_country_export_evidence_snippet_ordering(self):
        """Test that snippets are ordered by source and snippet_order."""
        snapshot = models.CountryExportSnapshot.objects.create(
            country_name="Austria",
            is_current=True,
            confidence="High",
            status="success",
        )
        source = models.CountryExportSource.objects.create(
            snapshot=snapshot,
            rank=1,
            url="https://example.com/austria",
            title="Austria Export Info",
        )
        snippet3 = models.CountryExportEvidenceSnippet.objects.create(
            source=source, snippet_order=3, snippet_text="Third snippet"
        )
        snippet1 = models.CountryExportEvidenceSnippet.objects.create(
            source=source, snippet_order=1, snippet_text="First snippet"
        )
        snippet2 = models.CountryExportEvidenceSnippet.objects.create(
            source=source, snippet_order=2, snippet_text="Second snippet"
        )
        snippets = list(models.CountryExportEvidenceSnippet.objects.filter(source=source))
        self.assertEqual(snippets[0].snippet_order, 1)
        self.assertEqual(snippets[1].snippet_order, 2)
        self.assertEqual(snippets[2].snippet_order, 3)

    def test_cascade_delete_snapshot_deletes_sources_and_snippets(self):
        """Test that deleting a snapshot cascades to sources and snippets."""
        snapshot = models.CountryExportSnapshot.objects.create(
            country_name="Portugal",
            is_current=True,
            confidence="Medium",
            status="success",
        )
        source = models.CountryExportSource.objects.create(
            snapshot=snapshot,
            rank=1,
            url="https://example.com/portugal",
            title="Portugal Export",
        )
        models.CountryExportEvidenceSnippet.objects.create(source=source, snippet_order=1, snippet_text="Evidence text")
        snapshot_id = snapshot.id
        source_id = source.id

        # Delete snapshot
        snapshot.delete()

        # Verify cascade deletion
        self.assertEqual(models.CountryExportSnapshot.objects.filter(id=snapshot_id).count(), 0)
        self.assertEqual(models.CountryExportSource.objects.filter(id=source_id).count(), 0)
        self.assertEqual(models.CountryExportEvidenceSnippet.objects.filter(source_id=source_id).count(), 0)

    def test_snapshot_default_values(self):
        """Test that snapshot has correct default values."""
        snapshot = models.CountryExportSnapshot.objects.create(
            country_name="Sweden",
        )
        self.assertTrue(snapshot.is_current)
        self.assertEqual(snapshot.confidence, "Medium")
        self.assertEqual(snapshot.status, "success")
        self.assertEqual(snapshot.summary_text, "")
        self.assertEqual(snapshot.current_situation_bullets, [])

    def test_snapshot_status_choices(self):
        """Test snapshot status field accepts valid choices."""
        for status, _ in models.CountryExportSnapshot.STATUS_CHOICES:
            snapshot = models.CountryExportSnapshot.objects.create(
                country_name=f"Test Country {status}",
                is_current=False,
                status=status,
            )
            self.assertEqual(snapshot.status, status)

    def test_snapshot_confidence_choices(self):
        """Test snapshot confidence field accepts valid choices."""
        for confidence, _ in models.CountryExportSnapshot.CONFIDENCE_CHOICES:
            snapshot = models.CountryExportSnapshot.objects.create(
                country_name=f"Test Country {confidence}",
                is_current=False,
                confidence=confidence,
            )
            self.assertEqual(snapshot.confidence, confidence)
    def test_cleaned_framework_agreement_str_with_vendor(self):
        agreement = models.CleanedFrameworkAgreement.objects.create(
            agreement_id="FA-TEST001",
            vendor_name="Test Vendor Inc",
        )
        self.assertEqual(str(agreement), "FA-TEST001 - Test Vendor Inc")

    def test_cleaned_framework_agreement_str_without_vendor(self):
        agreement = models.CleanedFrameworkAgreement.objects.create(
            agreement_id="FA-TEST002",
            vendor_name="",
        )
        self.assertEqual(str(agreement), "FA-TEST002 - ")
