"""
Integration tests for SPARK-related API endpoints (Stock inventory, Framework agreements, etc.).
"""

from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse

from api.models import (
    CleanedFrameworkAgreement,
    Country,
    CountryCustomsSnapshot,
    StockInventory,
)
from main.test_case import APITestCase

# Fixed maps returned by mocked _fetch_goadmin_maps (no network calls in tests).
GOADMIN_MAPS = (
    {"AE": "ARE", "AR": "ARG", "MY": "MYS"},  # iso2_to_iso3
    {"ARE": "United Arab Emirates", "ARG": "Argentina", "MYS": "Malaysia"},  # iso3_to_country_name
    {"ARE": "MENA", "ARG": "Americas", "MYS": "Asia Pacific"},  # iso3_to_region_name
)


class StockInventoryViewTest(APITestCase):
    """Integration tests for Stock inventory endpoints."""

    def setUp(self):
        super().setUp()
        self._goadmin_patcher = patch(
            "api.stock_inventory_view.fetch_goadmin_maps",
            return_value=GOADMIN_MAPS,
        )
        self._goadmin_patcher.start()

    def tearDown(self):
        self._goadmin_patcher.stop()
        super().tearDown()

    def _seed_stock_inventory(self):
        StockInventory.objects.create(
            warehouse_id="AE1DUB002",
            warehouse="Dubai Hub",
            warehouse_country="United Arab Emirates",
            region="MENA",
            product_category="Shelter",
            item_name="Tent A",
            quantity=Decimal("5.00"),
            unit_measurement="ea",
        )
        StockInventory.objects.create(
            warehouse_id="AE1DUB002",
            warehouse="Dubai Hub",
            warehouse_country="United Arab Emirates",
            region="MENA",
            product_category="Shelter",
            item_name="Tent B",
            quantity=Decimal("3.00"),
            unit_measurement="ea",
        )
        StockInventory.objects.create(
            warehouse_id="AR1BUE002",
            warehouse="Buenos Aires Hub",
            warehouse_country="Argentina",
            region="Americas",
            product_category="Health",
            item_name="Kit C",
            quantity=Decimal("20.00"),
            unit_measurement="ea",
        )

    def test_list_returns_200_and_results(self):
        resp = self.client.get("/api/v1/stock-inventory/")
        self.assert_200(resp)
        data = resp.json()
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)

    def test_list_with_page_params_returns_200_and_results(self):
        resp = self.client.get("/api/v1/stock-inventory/?page=1&page_size=10")
        self.assert_200(resp)
        data = resp.json()
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)
        if "page" in data and "page_size" in data:
            self.assertEqual(data["page"], 1)
            self.assertEqual(data["page_size"], 10)

    def test_list_with_distinct_returns_filter_options(self):
        resp = self.client.get("/api/v1/stock-inventory/?distinct=1")
        self.assert_200(resp)
        data = resp.json()
        self.assertIn("regions", data)
        self.assertIn("countries", data)
        self.assertIn("item_groups", data)
        self.assertIn("item_names", data)
        self.assertIsInstance(data["regions"], list)
        self.assertIsInstance(data["countries"], list)
        self.assertIsInstance(data["item_groups"], list)
        self.assertIsInstance(data["item_names"], list)

    def test_aggregated_returns_200_and_results(self):
        resp = self.client.get("/api/v1/stock-inventory/aggregated/")
        self.assert_200(resp)
        data = resp.json()
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)

    def test_summary_returns_200_and_shape(self):
        resp = self.client.get("/api/v1/stock-inventory/summary/")
        self.assert_200(resp)
        data = resp.json()
        self.assertIn("total", data)
        self.assertIn("by_item_group", data)
        self.assertIn("low_stock", data)
        self.assertIsInstance(data["by_item_group"], list)
        self.assertIsInstance(data["low_stock"], dict)
        self.assertIn("threshold", data["low_stock"])
        self.assertIn("count", data["low_stock"])

    def test_summary_respects_low_stock_threshold(self):
        resp = self.client.get("/api/v1/stock-inventory/summary/?low_stock_threshold=10")
        self.assert_200(resp)
        data = resp.json()
        self.assertEqual(data["low_stock"]["threshold"], 10)

    def test_list_filter_sort_and_pagination_returns_expected_rows(self):
        self._seed_stock_inventory()

        with patch("api.stock_inventory_view.ES_CLIENT", None):
            resp = self.client.get(
                "/api/v1/stock-inventory/?"
                "region=MENA&"
                "product_category=Shelter&"
                "country_iso3=ARE&"
                "warehouse_ids=AE1DUB002&"
                "sort=quantity&order=asc&"
                "page=1&page_size=1"
            )

        self.assert_200(resp)
        data = resp.json()
        self.assertEqual(data["total"], 2)
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 1)
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["item_name"], "Tent B")
        self.assertEqual(data["results"][0]["country_iso3"], "ARE")

        with patch("api.stock_inventory_view.ES_CLIENT", None):
            resp_page_2 = self.client.get(
                "/api/v1/stock-inventory/?"
                "region=MENA&"
                "product_category=Shelter&"
                "country_iso3=ARE&"
                "warehouse_ids=AE1DUB002&"
                "sort=quantity&order=asc&"
                "page=2&page_size=1"
            )
        self.assert_200(resp_page_2)
        data_page_2 = resp_page_2.json()
        self.assertEqual(len(data_page_2["results"]), 1)
        self.assertEqual(data_page_2["results"][0]["item_name"], "Tent A")

    def test_aggregated_returns_expected_country_totals(self):
        self._seed_stock_inventory()

        with patch("api.stock_inventory_view.ES_CLIENT", None):
            resp = self.client.get(
                "/api/v1/stock-inventory/aggregated/?"
                "warehouse_ids=AE1DUB002,AR1BUE002"
            )

        self.assert_200(resp)
        rows = resp.json()["results"]
        keyed = {r["country_iso3"]: r for r in rows}

        self.assertIn("ARE", keyed)
        self.assertIn("ARG", keyed)
        self.assertEqual(Decimal(keyed["ARE"]["total_quantity"]), Decimal("8.00"))
        self.assertEqual(keyed["ARE"]["warehouse_count"], 1)
        self.assertEqual(Decimal(keyed["ARG"]["total_quantity"]), Decimal("20.00"))

    def test_summary_returns_expected_aggregates(self):
        self._seed_stock_inventory()

        resp = self.client.get("/api/v1/stock-inventory/summary/?low_stock_threshold=10")
        self.assert_200(resp)
        data = resp.json()

        self.assertEqual(data["total"], 3)
        self.assertEqual(data["low_stock"]["threshold"], 10)
        self.assertEqual(data["low_stock"]["count"], 2)

        by_category = {row["product_category"]: row for row in data["by_item_group"]}
        self.assertEqual(by_category["Shelter"]["count"], 2)
        self.assertEqual(Decimal(by_category["Shelter"]["total_quantity"]), Decimal("8.00"))
        self.assertEqual(by_category["Health"]["count"], 1)
        self.assertEqual(Decimal(by_category["Health"]["total_quantity"]), Decimal("20.00"))


class CleanedFrameworkAgreementViewTest(APITestCase):
    """Integration tests for Framework agreements (Cleaned Framework Agreement) endpoints."""

    def test_list_unauthenticated_returns_401(self):
        resp = self.client.get("/api/v2/fabric/cleaned-framework-agreements/")
        self.assert_401(resp)

    def test_list_authenticated_returns_200_and_results(self):
        self.authenticate()
        resp = self.client.get("/api/v2/fabric/cleaned-framework-agreements/")
        self.assert_200(resp)
        data = resp.json()
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)

    def test_item_categories_unauthenticated_returns_401(self):
        url = reverse("fabric_cleaned_framework_agreement_item_categories")
        resp = self.client.get(url)
        self.assert_401(resp)

    def test_item_categories_authenticated_returns_200_and_results(self):
        self.authenticate()
        url = reverse("fabric_cleaned_framework_agreement_item_categories")
        resp = self.client.get(url)
        self.assert_200(resp)
        data = resp.json()
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)

    def test_summary_unauthenticated_returns_401(self):
        url = reverse("fabric_cleaned_framework_agreement_summary")
        resp = self.client.get(url)
        self.assert_401(resp)

    def test_summary_authenticated_returns_200_and_shape(self):
        self.authenticate()
        url = reverse("fabric_cleaned_framework_agreement_summary")
        resp = self.client.get(url)
        self.assert_200(resp)
        data = resp.json()
        self.assertIn("ifrcFrameworkAgreements", data)
        self.assertIn("suppliers", data)
        self.assertIn("otherFrameworkAgreements", data)
        self.assertIn("otherSuppliers", data)
        self.assertIn("countriesCovered", data)
        self.assertIn("itemCategoriesCovered", data)

    def test_map_stats_unauthenticated_returns_401(self):
        url = reverse("fabric_cleaned_framework_agreement_map_stats")
        resp = self.client.get(url)
        self.assert_401(resp)

    def test_map_stats_authenticated_returns_200_and_results(self):
        self.authenticate()
        url = reverse("fabric_cleaned_framework_agreement_map_stats")
        resp = self.client.get(url)
        self.assert_200(resp)
        data = resp.json()
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)

    def _seed_framework_agreements(self):
        CleanedFrameworkAgreement.objects.create(
            agreement_id="A-100",
            owner="IFRC",
            vendor_name="Vendor One",
            vendor_country="KEN",
            region_countries_covered="Kenya",
            item_category="Shelter",
        )
        CleanedFrameworkAgreement.objects.create(
            agreement_id="A-200",
            owner="Partner",
            vendor_name="Vendor Two",
            vendor_country="KEN",
            region_countries_covered="Kenya",
            item_category="Health",
        )
        CleanedFrameworkAgreement.objects.create(
            agreement_id="A-300",
            owner="IFRC",
            vendor_name="Vendor Three",
            vendor_country="UGA",
            region_countries_covered="Uganda",
            item_category="Health",
        )

    def test_summary_returns_expected_framework_aggregates(self):
        self.authenticate()
        self._seed_framework_agreements()

        with patch("api.framework_agreement_views.ES_CLIENT", None):
            resp = self.client.get(reverse("fabric_cleaned_framework_agreement_summary"))

        self.assert_200(resp)
        data = resp.json()
        self.assertEqual(data["ifrcFrameworkAgreements"], 3)
        self.assertEqual(data["suppliers"], 3)
        self.assertEqual(data["otherFrameworkAgreements"], 1)
        self.assertEqual(data["otherSuppliers"], 1)
        self.assertEqual(data["itemCategoriesCovered"], 2)

    def test_map_stats_returns_expected_counts_for_country(self):
        self.authenticate()
        self._seed_framework_agreements()
        Country.objects.update_or_create(
            name="Kenya",
            defaults={
                "iso": "KE",
                "iso3": "KEN",
                "independent": True,
                "is_deprecated": False,
            },
        )

        with patch("api.framework_agreement_views.ES_CLIENT", None):
            resp = self.client.get(reverse("fabric_cleaned_framework_agreement_map_stats"))

        self.assert_200(resp)
        rows = resp.json()["results"]
        kenya = next((r for r in rows if r["iso3"] == "KEN"), None)
        self.assertIsNotNone(kenya)
        self.assertEqual(kenya["exclusiveFrameworkAgreements"], 2)
        self.assertEqual(kenya["exclusiveIfrcAgreements"], 1)
        self.assertEqual(kenya["exclusiveOtherAgreements"], 1)
        self.assertEqual(kenya["vendorCountryAgreements"], 2)


class ProBonoServicesViewTest(APITestCase):
    """Integration tests for Pro bono services endpoint."""

    def test_pro_bono_returns_200_and_results(self):
        resp = self.client.get("/api/v1/pro-bono-services/")
        self.assert_200(resp)
        data = resp.json()
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)

    def test_pro_bono_when_file_missing_returns_200_empty_results(self):
        with patch("api.pro_bono_views.os.path.exists", return_value=False):
            resp = self.client.get("/api/v1/pro-bono-services/")
        self.assert_200(resp)
        data = resp.json()
        self.assertEqual(data["results"], [])

    def test_pro_bono_when_read_fails_returns_500(self):
        with (
            patch("api.pro_bono_views.os.path.exists", return_value=True),
            patch("api.pro_bono_views.open", side_effect=IOError("No such file")),
        ):
            resp = self.client.get("/api/v1/pro-bono-services/")
        self.assert_500(resp)
        data = resp.json()
        self.assertIn("error", data)
        self.assertIn("results", data)
        self.assertEqual(data["results"], [])


# Mock data for customs regulations (matches load_customs_regulations() response shape).
CUSTOMS_REGULATIONS_MOCK_DATA = {
    "metadata": {
        "source": "IFRC Customs & Import Regulations",
        "generated_at": "2025-01-01T00:00:00Z",
    },
    "countries": [
        {
            "country": "Kenya",
            "sections": [
                {
                    "section": "Import",
                    "items": [
                        {"question": "Q1", "answer": "A1", "notes": ""},
                    ],
                },
            ],
        },
        {
            "country": "Uganda",
            "sections": [],
        },
    ],
}


class CustomsRegulationsViewTest(APITestCase):
    """Integration tests for Customs regulations (country regulations) endpoints."""

    def test_list_unauthenticated_returns_401(self):
        resp = self.client.get(reverse("country_regulations"))
        self.assert_401(resp)

    def test_list_authenticated_returns_200_with_mock_data(self):
        self.authenticate()
        with patch("api.customs_spark_views.load_customs_regulations", return_value=CUSTOMS_REGULATIONS_MOCK_DATA):
            resp = self.client.get(reverse("country_regulations"))
        self.assert_200(resp)
        data = resp.json()
        self.assertIn("metadata", data)
        self.assertIn("countries", data)
        self.assertIsInstance(data["countries"], list)
        self.assertEqual(len(data["countries"]), 2)

    def test_list_when_loader_fails_returns_500(self):
        self.authenticate()
        with patch("api.customs_spark_views.load_customs_regulations", side_effect=FileNotFoundError("No file")):
            resp = self.client.get(reverse("country_regulations"))
        self.assert_500(resp)
        data = resp.json()
        self.assertIn("detail", data)
        self.assertIn("Failed to load customs regulations", data["detail"])

    def test_country_detail_unauthenticated_returns_401(self):
        resp = self.client.get(reverse("country_regulations_detail", kwargs={"country": "Kenya"}))
        self.assert_401(resp)

    def test_country_detail_authenticated_country_found_returns_200(self):
        self.authenticate()
        with patch("api.customs_spark_views.load_customs_regulations", return_value=CUSTOMS_REGULATIONS_MOCK_DATA):
            resp = self.client.get(reverse("country_regulations_detail", kwargs={"country": "Kenya"}))
        self.assert_200(resp)
        data = resp.json()
        self.assertEqual(data["country"], "Kenya")
        self.assertIn("sections", data)
        self.assertIsInstance(data["sections"], list)

    def test_country_detail_authenticated_country_not_found_returns_404(self):
        self.authenticate()
        with patch("api.customs_spark_views.load_customs_regulations", return_value=CUSTOMS_REGULATIONS_MOCK_DATA):
            resp = self.client.get(reverse("country_regulations_detail", kwargs={"country": "NonExistent"}))
        self.assert_404(resp)
        data = resp.json()
        self.assertIn("detail", data)
        self.assertIn("Country not found", data["detail"])

    def test_country_detail_when_loader_fails_returns_500(self):
        self.authenticate()
        with patch("api.customs_spark_views.load_customs_regulations", side_effect=RuntimeError("Loader error")):
            resp = self.client.get(reverse("country_regulations_detail", kwargs={"country": "Kenya"}))
        self.assert_500(resp)
        data = resp.json()
        self.assertIn("detail", data)
        self.assertIn("Failed to load country regulations", data["detail"])


class CustomsUpdatesViewTest(APITestCase):
    """Integration tests for Customs AI updates endpoints."""

    def test_list_unauthenticated_returns_401(self):
        resp = self.client.get(reverse("customs_updates_list"))
        self.assert_401(resp)

    def test_list_authenticated_returns_200_and_results(self):
        self.authenticate()
        resp = self.client.get(reverse("customs_updates_list"))
        self.assert_200(resp)
        data = resp.json()
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)

    def test_list_authenticated_with_snapshot_returns_snapshot_in_results(self):
        self.authenticate()
        CountryCustomsSnapshot.objects.create(
            country_name="Kenya",
            is_current=True,
            summary_text="Test summary",
        )
        resp = self.client.get(reverse("customs_updates_list"))
        self.assert_200(resp)
        data = resp.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["country_name"], "Kenya")
        self.assertIn("generated_at", data["results"][0])

    def test_list_when_exception_returns_500(self):
        self.authenticate()
        with patch(
            "api.customs_spark_views.CountryCustomsSnapshot.objects.filter",
            side_effect=RuntimeError("DB error"),
        ):
            resp = self.client.get(reverse("customs_updates_list"))
        self.assert_500(resp)
        data = resp.json()
        self.assertIn("detail", data)
        self.assertIn("Failed to load customs updates", data["detail"])

    def test_country_detail_unauthenticated_returns_401(self):
        resp = self.client.get(reverse("customs_updates_detail", kwargs={"country": "Kenya"}))
        self.assert_401(resp)

    def test_country_detail_authenticated_snapshot_exists_returns_200(self):
        self.authenticate()
        CountryCustomsSnapshot.objects.create(
            country_name="Kenya",
            is_current=True,
            summary_text="Test summary",
        )
        resp = self.client.get(reverse("customs_updates_detail", kwargs={"country": "Kenya"}))
        self.assert_200(resp)
        data = resp.json()
        self.assertEqual(data["country_name"], "Kenya")
        self.assertIn("summary_text", data)
        self.assertIn("generated_at", data)

    def test_country_detail_authenticated_country_invalid_returns_400(self):
        self.authenticate()
        with patch(
            "api.customs_spark_views.CustomsAIService.validate_country_name",
            return_value=(False, "Not a recognized country"),
        ):
            resp = self.client.get(reverse("customs_updates_detail", kwargs={"country": "InvalidCountry"}))
        self.assert_400(resp)
        data = resp.json()
        self.assertIn("detail", data)

    def test_country_detail_when_exception_returns_error_response(self):
        self.authenticate()
        with patch(
            "api.customs_spark_views.CountryCustomsSnapshot.objects.filter",
            side_effect=RuntimeError("Unexpected error"),
        ):
            resp = self.client.get(reverse("customs_updates_detail", kwargs={"country": "Kenya"}))
        data = resp.json()
        self.assertIn("detail", data)
        self.assertIn("An error occurred while processing customs update", data["detail"])

    def test_list_orders_results_by_country_name(self):
        self.authenticate()
        CountryCustomsSnapshot.objects.create(country_name="Zimbabwe", is_current=True, summary_text="S1")
        CountryCustomsSnapshot.objects.create(country_name="Albania", is_current=True, summary_text="S2")

        resp = self.client.get(reverse("customs_updates_list"))
        self.assert_200(resp)
        names = [row["country_name"] for row in resp.json()["results"]]
        self.assertEqual(names, sorted(names))

    def test_country_detail_creates_snapshot_when_missing(self):
        self.authenticate()
        generated_snapshot = CountryCustomsSnapshot(
            country_name="Kenya",
            is_current=True,
            summary_text="Generated summary",
        )

        with (
            patch("api.customs_spark_views.CustomsAIService.validate_country_name", return_value=(True, None)),
            patch("api.customs_spark_views.CustomsAIService.generate_customs_snapshot", return_value=generated_snapshot),
        ):
            resp = self.client.get(reverse("customs_updates_detail", kwargs={"country": "Kenya"}))

        self.assert_201(resp)
        data = resp.json()
        self.assertEqual(data["country_name"], "Kenya")

    def test_country_detail_delete_deactivates_current_snapshot(self):
        self.authenticate()
        snapshot = CountryCustomsSnapshot.objects.create(
            country_name="Kenya",
            is_current=True,
            summary_text="To deactivate",
        )

        resp = self.client.delete(reverse("customs_updates_detail", kwargs={"country": "Kenya"}))
        self.assert_200(resp)

        snapshot.refresh_from_db()
        self.assertFalse(snapshot.is_current)
