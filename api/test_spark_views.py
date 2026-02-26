"""
Integration tests for SPARK-related API endpoints (Stock inventory, etc.).
"""
from unittest.mock import patch

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
            "api.warehouse_stocks_views._fetch_goadmin_maps",
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
