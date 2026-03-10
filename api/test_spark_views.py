"""
Integration tests for SPARK-related API endpoints (Stock inventory, Framework agreements, etc.).
"""

from unittest.mock import patch

from django.urls import reverse

from api.models import CountryCustomsSnapshot
from main.test_case import APITestCase

# Fixed maps returned by mocked _fetch_goadmin_maps (no network calls in tests).
GOADMIN_MAPS = (
    {"XX": "XXX"},  # iso2_to_iso3
    {"XXX": "Test Country"},  # iso3_to_country_name
    {"XXX": "Test Region"},  # iso3_to_region_name
)


class WarehouseStocksViewTest(APITestCase):
    """Integration tests for Stock inventory (warehouse stocks) endpoints."""

    def setUp(self):
        super().setUp()
        self._goadmin_patcher = patch(
            "api.warehouse_stocks_views.fetch_goadmin_maps",
            return_value=GOADMIN_MAPS,
        )
        self._goadmin_patcher.start()

    def tearDown(self):
        self._goadmin_patcher.stop()
        super().tearDown()

    def test_list_returns_200_and_results(self):
        resp = self.client.get("/api/v1/warehouse-stocks/")
        self.assert_200(resp)
        data = resp.json()
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)

    def test_list_with_page_params_returns_200_and_results(self):
        resp = self.client.get("/api/v1/warehouse-stocks/?page=1&page_size=10")
        self.assert_200(resp)
        data = resp.json()
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)
        if "page" in data and "page_size" in data:
            self.assertEqual(data["page"], 1)
            self.assertEqual(data["page_size"], 10)

    def test_list_with_distinct_returns_filter_options(self):
        resp = self.client.get("/api/v1/warehouse-stocks/?distinct=1")
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
        resp = self.client.get("/api/v1/warehouse-stocks/aggregated/")
        self.assert_200(resp)
        data = resp.json()
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)

    def test_summary_returns_200_and_shape(self):
        resp = self.client.get("/api/v1/warehouse-stocks/summary/")
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
        resp = self.client.get("/api/v1/warehouse-stocks/summary/?low_stock_threshold=10")
        self.assert_200(resp)
        data = resp.json()
        self.assertEqual(data["low_stock"]["threshold"], 10)


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
