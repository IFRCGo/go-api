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


class CountryCustomsSnapshotTest(TestCase):
    def setUp(self):
        self.snapshot = models.CountryCustomsSnapshot.objects.create(
            country_name="Kenya",
            summary_text="Test customs summary for Kenya.",
            status="success",
            confidence="High",
            evidence_hash="abc123",
            search_query="Kenya customs import",
        )

    def test_snapshot_str(self):
        expected = f"Kenya - {self.snapshot.generated_at.strftime('%Y-%m-%d')}"
        self.assertEqual(str(self.snapshot), expected)

    def test_snapshot_defaults(self):
        snapshot = models.CountryCustomsSnapshot.objects.create(
            country_name="Uganda",
            summary_text="Test summary",
        )
        self.assertTrue(snapshot.is_current)
        self.assertEqual(snapshot.confidence, "Medium")
        self.assertEqual(snapshot.status, "success")
        self.assertEqual(snapshot.model_name, "gpt-4")
        self.assertEqual(snapshot.current_situation_bullets, [])
        self.assertEqual(snapshot.official_doc_url, "")
        self.assertEqual(snapshot.official_doc_title, "")
        self.assertEqual(snapshot.rc_society_url, "")
        self.assertEqual(snapshot.rc_society_title, "")

    def test_snapshot_with_official_doc(self):
        snapshot = models.CountryCustomsSnapshot.objects.create(
            country_name="Tanzania",
            summary_text="Test summary",
            official_doc_url="https://customs.gov.tz/regulations",
            official_doc_title="Tanzania Revenue Authority - Import Regulations",
        )
        self.assertEqual(snapshot.official_doc_url, "https://customs.gov.tz/regulations")
        self.assertEqual(snapshot.official_doc_title, "Tanzania Revenue Authority - Import Regulations")

    def test_snapshot_with_rc_society(self):
        snapshot = models.CountryCustomsSnapshot.objects.create(
            country_name="Rwanda",
            summary_text="Test summary",
            rc_society_url="https://rwandarcs.org/logistics",
            rc_society_title="Rwanda Red Cross Society - Logistics Updates",
        )
        self.assertEqual(snapshot.rc_society_url, "https://rwandarcs.org/logistics")
        self.assertEqual(snapshot.rc_society_title, "Rwanda Red Cross Society - Logistics Updates")

    def test_unique_current_snapshot_per_country(self):
        """Only one is_current=True snapshot per country_name is allowed."""
        with self.assertRaises(Exception):
            models.CountryCustomsSnapshot.objects.create(
                country_name="Kenya",
                summary_text="Duplicate current snapshot",
                is_current=True,
            )

    def test_multiple_non_current_snapshots_allowed(self):
        self.snapshot.is_current = False
        self.snapshot.save()
        models.CountryCustomsSnapshot.objects.create(
            country_name="Kenya",
            summary_text="New snapshot",
            is_current=False,
        )
        self.assertEqual(
            models.CountryCustomsSnapshot.objects.filter(country_name="Kenya").count(),
            2,
        )

    def test_cascade_delete_removes_sources_and_snippets(self):
        source = models.CountryCustomsSource.objects.create(
            snapshot=self.snapshot,
            rank=1,
            url="https://example.com",
            title="Test Source",
        )
        models.CountryCustomsEvidenceSnippet.objects.create(
            source=source,
            snippet_order=1,
            snippet_text="Test snippet text",
        )
        self.snapshot.delete()
        self.assertEqual(models.CountryCustomsSource.objects.count(), 0)
        self.assertEqual(models.CountryCustomsEvidenceSnippet.objects.count(), 0)


class CountryCustomsSourceTest(TestCase):
    def setUp(self):
        self.snapshot = models.CountryCustomsSnapshot.objects.create(
            country_name="Ethiopia",
            summary_text="Test summary",
        )
        self.source = models.CountryCustomsSource.objects.create(
            snapshot=self.snapshot,
            rank=1,
            url="https://customs.gov.et/import",
            title="Ethiopia Customs Import Guide",
            publisher="customs.gov.et",
            authority_score=50,
            freshness_score=30,
            relevance_score=25,
            specificity_score=20,
            total_score=125,
        )

    def test_source_str(self):
        self.assertEqual(str(self.source), "Ethiopia Customs Import Guide (Rank 1)")

    def test_source_defaults(self):
        source = models.CountryCustomsSource.objects.create(
            snapshot=self.snapshot,
            rank=2,
            url="https://example.com",
            title="Another Source",
        )
        self.assertEqual(source.authority_score, 0)
        self.assertEqual(source.freshness_score, 0)
        self.assertEqual(source.relevance_score, 0)
        self.assertEqual(source.specificity_score, 0)
        self.assertEqual(source.total_score, 0)
        self.assertEqual(source.content_hash, "")
        self.assertIsNone(source.published_at)

    def test_source_ordering(self):
        models.CountryCustomsSource.objects.create(
            snapshot=self.snapshot,
            rank=3,
            url="https://example.com/3",
            title="Third",
        )
        models.CountryCustomsSource.objects.create(
            snapshot=self.snapshot,
            rank=2,
            url="https://example.com/2",
            title="Second",
        )
        sources = list(self.snapshot.sources.values_list("rank", flat=True))
        self.assertEqual(sources, [1, 2, 3])

    def test_source_related_name(self):
        self.assertEqual(self.snapshot.sources.count(), 1)
        self.assertEqual(self.snapshot.sources.first(), self.source)


class CountryCustomsEvidenceSnippetTest(TestCase):
    def setUp(self):
        self.snapshot = models.CountryCustomsSnapshot.objects.create(
            country_name="Somalia",
            summary_text="Test summary",
        )
        self.source = models.CountryCustomsSource.objects.create(
            snapshot=self.snapshot,
            rank=1,
            url="https://example.com",
            title="Test Source",
        )
        self.snippet = models.CountryCustomsEvidenceSnippet.objects.create(
            source=self.source,
            snippet_order=1,
            snippet_text="Humanitarian goods imported into Somalia require a customs declaration form.",
        )

    def test_snippet_str(self):
        self.assertEqual(
            str(self.snippet),
            "Snippet 1 - Humanitarian goods imported into Somalia require a...",
        )

    def test_snippet_defaults(self):
        self.assertEqual(self.snippet.claim_tags, [])

    def test_snippet_ordering(self):
        models.CountryCustomsEvidenceSnippet.objects.create(
            source=self.source,
            snippet_order=3,
            snippet_text="Third snippet",
        )
        models.CountryCustomsEvidenceSnippet.objects.create(
            source=self.source,
            snippet_order=2,
            snippet_text="Second snippet",
        )
        orders = list(self.source.snippets.values_list("snippet_order", flat=True))
        self.assertEqual(orders, [1, 2, 3])

    def test_snippet_related_name(self):
        self.assertEqual(self.source.snippets.count(), 1)
        self.assertEqual(self.source.snippets.first(), self.snippet)

    def test_snippet_with_claim_tags(self):
        snippet = models.CountryCustomsEvidenceSnippet.objects.create(
            source=self.source,
            snippet_order=2,
            snippet_text="Duty-free exemption available for NGOs.",
            claim_tags=["exemption", "duty-free"],
        )
        self.assertEqual(snippet.claim_tags, ["exemption", "duty-free"])

    def test_cascade_delete_source_removes_snippets(self):
        self.source.delete()
        self.assertEqual(models.CountryCustomsEvidenceSnippet.objects.count(), 0)
