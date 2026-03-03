"""
Views for warehouse suggestion API.
Suggests top warehouses based on distance and export regulations.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List

from django.conf import settings
from django.db.models import Sum
from rest_framework import views
from rest_framework.response import Response

from api.country_distance import (
    get_distance_between_countries,
    get_distance_score,
    is_same_country,
    normalize_country_to_iso3,
)
from api.esconnection import ES_CLIENT
from api.export_ai_service import ExportAIService
from api.indexes import WAREHOUSE_INDEX_NAME
from api.models import DimInventoryTransactionLine, DimProduct, DimWarehouse

logger = logging.getLogger(__name__)


def _safe_str(v):
    return "" if v is None else str(v)


def get_stock_quantity_score(quantity: float, max_quantity: float) -> int:
    """
    Score stock quantity (0-50 points).
    Higher stock relative to max = higher score.

    Scoring based on percentile of max quantity:
    - Top 20% (80-100%): 50 points
    - 60-80%: 40 points
    - 40-60%: 30 points
    - 20-40%: 20 points
    - Bottom 20% (0-20%): 10 points
    """
    if max_quantity <= 0:
        return 25  # Default middle score if no max

    ratio = quantity / max_quantity

    if ratio >= 0.8:
        return 50
    elif ratio >= 0.6:
        return 40
    elif ratio >= 0.4:
        return 30
    elif ratio >= 0.2:
        return 20
    else:
        return 10


def get_export_penalty(export_confidence: str) -> int:
    """
    Get export regulation penalty (0 to -30 points).
    Only penalize countries with actual restrictions.

    - High confidence (easy exports): 0 penalty
    - Medium confidence (some bureaucracy): -10 penalty
    - Low confidence (difficult/restrictions): -20 penalty
    - Failed/unavailable (could indicate sanctions): -30 penalty
    """
    penalties = {
        "High": 0,
        "Medium": -10,
        "Low": -20,
    }
    return penalties.get(export_confidence, -30)


class WarehouseSuggestionView(views.APIView):
    """
    Suggest top 3 warehouses for a given receiving country and item.

    GET /api/v1/warehouse-suggestions/?receiving_country=<country>&item_name=<item>

    Response:
    {
        "suggestions": [
            {
                "warehouse_id": "BE01",
                "warehouse_name": "Belgium Hub",
                "country": "Belgium",
                "country_iso3": "BEL",
                "distance_km": 2450.5,
                "distance_score": 40,
                "export_regulation_score": 90,
                "stock_quantity": 1500,
                "total_score": 130,
                "is_domestic": false
            },
            ...
        ],
        "receiving_country": "Ukraine",
        "receiving_country_iso3": "UKR",
        "item_name": "Emergency Shelter Kit"
    }
    """

    permission_classes = []

    def get(self, request):
        receiving_country = request.query_params.get("receiving_country", "").strip()
        item_name = request.query_params.get("item_name", "").strip()

        if not receiving_country:
            return Response({"error": "receiving_country parameter is required"}, status=400)

        if not item_name:
            return Response({"error": "item_name parameter is required"}, status=400)

        receiving_iso3 = normalize_country_to_iso3(receiving_country)
        if not receiving_iso3:
            return Response({"error": f"Could not identify country: {receiving_country}"}, status=400)

        # Get all warehouses with the specified item in stock
        warehouses_with_stock = self._get_warehouses_with_item(item_name)

        logger.info(f"Found {len(warehouses_with_stock)} warehouses with item '{item_name}'")

        if not warehouses_with_stock:
            return Response(
                {
                    "suggestions": [],
                    "receiving_country": receiving_country,
                    "receiving_country_iso3": receiving_iso3,
                    "item_name": item_name,
                    "message": "No warehouses found with this item in stock",
                }
            )

        # Find max stock quantity for scoring normalization
        max_stock_qty = max((float(wh.get("stock_quantity") or 0) for wh in warehouses_with_stock), default=0)

        # OPTIMIZATION: If 3 or fewer warehouses have stock, return them directly
        # without expensive AI-based export regulation scoring
        if len(warehouses_with_stock) <= 3:
            logger.info(f"Only {len(warehouses_with_stock)} warehouses with stock - " "skipping AI scoring, returning all")
            suggestions = []
            for wh in warehouses_with_stock:
                wh_country = wh.get("country") or wh.get("country_iso3") or ""
                is_domestic = is_same_country(wh_country, receiving_country)
                stock_qty = float(wh.get("stock_quantity") or 0)

                if is_domestic:
                    wh["is_domestic"] = True
                    wh["distance_km"] = 0
                    wh["distance_score"] = 100  # Maximum for domestic
                    wh["export_penalty"] = 0  # No penalty for domestic
                    wh["export_summary"] = "No export clearance required for domestic shipments."
                else:
                    wh["is_domestic"] = False
                    wh_country_iso3 = wh.get("country_iso3") or ""
                    distance = get_distance_between_countries(wh_country_iso3 or wh_country, receiving_iso3)
                    wh["distance_km"] = round(distance, 1) if distance else None
                    wh["distance_score"] = get_distance_score(distance)
                    # Default no penalty when skipping AI
                    wh["export_penalty"] = 0
                    wh["export_summary"] = "Export regulation details not yet analyzed."

                # Add stock score
                wh["stock_score"] = get_stock_quantity_score(stock_qty, max_stock_qty)
                # Total = distance + stock + penalty (penalty is 0 or negative)
                wh["total_score"] = wh["distance_score"] + wh["stock_score"] + wh["export_penalty"]
                suggestions.append(wh)

            # Sort by total score
            suggestions.sort(key=lambda x: x.get("total_score", 0), reverse=True)

            return Response(
                {
                    "suggestions": suggestions,
                    "receiving_country": receiving_country,
                    "receiving_country_iso3": receiving_iso3,
                    "item_name": item_name,
                    "message": f"Returning all {len(suggestions)} available warehouses (AI scoring skipped)",
                }
            )

        # Separate domestic vs foreign warehouses
        domestic_warehouses = []
        foreign_warehouses = []

        for wh in warehouses_with_stock:
            wh_country = wh.get("country") or wh.get("country_iso3") or ""
            if is_same_country(wh_country, receiving_country):
                wh["is_domestic"] = True
                wh["distance_km"] = 0
                wh["distance_score"] = 100  # Maximum score for domestic
                domestic_warehouses.append(wh)
            else:
                wh["is_domestic"] = False
                foreign_warehouses.append(wh)

        # If we have 3+ domestic warehouses, return top 3 by stock quantity
        if len(domestic_warehouses) >= 3:
            domestic_sorted = sorted(domestic_warehouses, key=lambda x: float(x.get("stock_quantity") or 0), reverse=True)
            suggestions = domestic_sorted[:3]

            # Add placeholder scores for domestic
            for s in suggestions:
                stock_qty = float(s.get("stock_quantity") or 0)
                s["export_penalty"] = 0  # No penalty for domestic
                s["export_summary"] = "No export clearance required for domestic shipments."
                s["stock_score"] = get_stock_quantity_score(stock_qty, max_stock_qty)
                s["total_score"] = s["distance_score"] + s["stock_score"] + s["export_penalty"]

            return Response(
                {
                    "suggestions": suggestions,
                    "receiving_country": receiving_country,
                    "receiving_country_iso3": receiving_iso3,
                    "item_name": item_name,
                    "message": "Domestic warehouses available",
                }
            )

        # Score foreign warehouses
        # First, calculate distance for ALL foreign warehouses (cheap operation)
        for wh in foreign_warehouses:
            wh_country = wh.get("country") or ""
            wh_country_iso3 = wh.get("country_iso3") or ""
            distance = get_distance_between_countries(wh_country_iso3 or wh_country, receiving_iso3)
            wh["distance_km"] = round(distance, 1) if distance else None
            wh["distance_score"] = get_distance_score(distance)
            wh["stock_quantity_float"] = float(wh.get("stock_quantity") or 0)

        # Determine which warehouses are "candidates" for export generation
        # If >= 10 foreign warehouses, only process top 50% by stock OR top 50% by distance
        candidate_indices = set()
        if len(foreign_warehouses) >= 10:
            half_count = len(foreign_warehouses) // 2
            logger.info(
                f"Filtering {len(foreign_warehouses)} foreign warehouses "
                f"to top 50% candidates ({half_count} each by stock/distance)"
            )

            # Top 50% by stock (highest stock first)
            by_stock = sorted(enumerate(foreign_warehouses), key=lambda x: x[1]["stock_quantity_float"], reverse=True)
            for i in range(half_count):
                candidate_indices.add(by_stock[i][0])

            # Top 50% by distance (closest first, so ascending)
            by_distance = sorted(
                enumerate(foreign_warehouses),
                key=lambda x: x[1]["distance_km"] if x[1]["distance_km"] is not None else float("inf"),
            )
            for i in range(half_count):
                candidate_indices.add(by_distance[i][0])

            logger.info(f"Total unique candidates after union: {len(candidate_indices)}")
        else:
            # Less than 10 warehouses - all are candidates
            candidate_indices = set(range(len(foreign_warehouses)))

        # Now process export data only for candidates
        for idx, wh in enumerate(foreign_warehouses):
            wh_country = wh.get("country") or ""
            wh_country_iso3 = wh.get("country_iso3") or ""
            export_lookup_country = wh_country or wh_country_iso3
            stock_qty = wh["stock_quantity_float"]

            logger.info(
                f"Processing foreign warehouse: {wh.get('warehouse_id')} "
                f"in {export_lookup_country}, stock={stock_qty}, "
                f"is_candidate={idx in candidate_indices}"
            )

            # Skip export generation for non-candidates
            if idx not in candidate_indices:
                logger.info(
                    f"Skipping export generation for {export_lookup_country} "
                    "- not a candidate (outside top 50% by stock and distance)"
                )
                wh["export_penalty"] = 0
                wh["export_summary"] = "Export data not analyzed (warehouse not in top candidates)."
            # Skip export generation for warehouses with 0 stock
            elif stock_qty <= 0:
                logger.info(f"Skipping export generation for {export_lookup_country} - warehouse has 0 stock")
                wh["export_penalty"] = 0
                wh["export_summary"] = "Export data not generated (warehouse has no stock)."
            else:
                # Get export regulation penalty and summary (this may trigger AI generation if not cached)
                try:
                    export_data = ExportAIService.get_export_regulation_data(export_lookup_country)
                    wh["export_penalty"] = export_data["penalty"]
                    wh["export_summary"] = export_data["summary"]
                    logger.info(
                        f"Export data for {export_lookup_country}: "
                        f"penalty={export_data['penalty']}, "
                        f"summary={export_data['summary'][:50]}..."
                    )
                except Exception as e:
                    logger.warning(f"Failed to get export data for {export_lookup_country}: {e}")
                    wh["export_penalty"] = -30  # Worst penalty if unknown
                    wh["export_summary"] = "Export regulation data unavailable."

            # Calculate stock score
            wh["stock_score"] = get_stock_quantity_score(stock_qty, max_stock_qty)

            # Calculate total score: distance + stock + penalty (penalty is 0 or negative)
            wh["total_score"] = wh["distance_score"] + wh["stock_score"] + wh["export_penalty"]

        # Sort foreign warehouses by total score
        foreign_sorted = sorted(foreign_warehouses, key=lambda x: x.get("total_score", 0), reverse=True)

        # Combine: prioritize domestic, then top foreign
        # Add scores to domestic warehouses
        for dw in domestic_warehouses:
            stock_qty = float(dw.get("stock_quantity") or 0)
            dw["export_penalty"] = 0  # No penalty for domestic
            dw["export_summary"] = "No export clearance required for domestic shipments."
            dw["stock_score"] = get_stock_quantity_score(stock_qty, max_stock_qty)
            dw["total_score"] = dw["distance_score"] + dw["stock_score"] + dw["export_penalty"]

        domestic_sorted = sorted(domestic_warehouses, key=lambda x: float(x.get("stock_quantity") or 0), reverse=True)

        combined = domestic_sorted + foreign_sorted
        suggestions = combined[:3]

        return Response(
            {
                "suggestions": suggestions,
                "receiving_country": receiving_country,
                "receiving_country_iso3": receiving_iso3,
                "item_name": item_name,
            }
        )

    def _get_warehouses_with_item(self, item_name: str) -> List[Dict[str, Any]]:
        """
        Get all warehouses that have the specified item in stock.
        Returns list of warehouse info with stock quantities.
        """
        results = []

        # Try Elasticsearch first
        if ES_CLIENT is not None:
            try:
                results = self._get_warehouses_from_es(item_name)
                if results:
                    logger.info(f"Using ES results: {len(results)} warehouses")
                    return results
                else:
                    logger.info("ES returned 0 results, falling back to DB")
            except Exception as e:
                logger.warning(f"ES query failed, falling back to DB: {e}")
        else:
            logger.info("ES_CLIENT is None, using DB directly")

        # Fall back to database
        db_results = self._get_warehouses_from_db(item_name)
        logger.info(f"DB query returned {len(db_results)} warehouses")
        return db_results

    def _get_warehouses_from_es(self, item_name: str) -> List[Dict[str, Any]]:
        """Query Elasticsearch for warehouses with the item."""
        # Use match query with high minimum_should_match for flexible but accurate matching
        # match_phrase is too strict for product names with commas/special chars
        query = {
            "bool": {
                "must": [
                    {
                        "match": {
                            "item_name": {
                                "query": item_name,
                                "operator": "and",  # All terms must match
                                "fuzziness": "AUTO",  # Allow for minor typos
                            }
                        }
                    }
                ]
            }
        }

        # Aggregate by warehouse
        aggs = {
            "by_warehouse": {
                "terms": {"field": "warehouse_id.keyword", "size": 1000},
                "aggs": {
                    "total_quantity": {"sum": {"field": "quantity"}},
                    "warehouse_info": {
                        "top_hits": {
                            "size": 1,
                            "_source": ["warehouse_id", "warehouse_name", "country", "country_iso3", "region"],
                        }
                    },
                },
            }
        }

        resp = ES_CLIENT.search(index=WAREHOUSE_INDEX_NAME, body={"size": 0, "query": query, "aggs": aggs})

        results = []
        buckets = resp.get("aggregations", {}).get("by_warehouse", {}).get("buckets", [])

        for bucket in buckets:
            warehouse_id = bucket.get("key")
            total_qty = bucket.get("total_quantity", {}).get("value", 0)

            # Get warehouse info from top hit
            hits = bucket.get("warehouse_info", {}).get("hits", {}).get("hits", [])
            if hits:
                src = hits[0].get("_source", {})
                results.append(
                    {
                        "warehouse_id": warehouse_id,
                        "warehouse_name": src.get("warehouse_name", ""),
                        "country": src.get("country", ""),
                        "country_iso3": src.get("country_iso3", ""),
                        "region": src.get("region", ""),
                        "stock_quantity": total_qty,
                    }
                )

        logger.info(f"ES query returned {len(results)} warehouses for item query")
        return results

    def _get_warehouses_from_db(self, item_name: str) -> List[Dict[str, Any]]:
        """Query database for warehouses with the item."""
        # Build warehouse lookup
        warehouses = DimWarehouse.objects.all().values("id", "name", "country")
        wh_by_id = {
            str(w["id"]): {
                "warehouse_name": _safe_str(w.get("name")),
                "country_iso3": _safe_str(w.get("country")).upper(),
            }
            for w in warehouses
        }

        # Build product lookup
        products = DimProduct.objects.all().values("id", "name")
        product_ids_for_item = [str(p["id"]) for p in products if item_name.lower() in _safe_str(p.get("name")).lower()]

        if not product_ids_for_item:
            return []

        # Query inventory lines
        qset = (
            DimInventoryTransactionLine.objects.filter(item_status_name="Available", product__in=product_ids_for_item)
            .values("warehouse")
            .annotate(total_qty=Sum("quantity"))
        )

        # Fetch country mappings for region/country name resolution
        try:
            import requests

            url = getattr(settings, "GOADMIN_COUNTRY_URL", "https://goadmin.ifrc.org/api/v2/country/?limit=300")
            resp = requests.get(url, timeout=10)
            data = resp.json()
            country_results = data.get("results", data) or []

            iso3_to_country_name = {}
            iso3_to_region_name = {}
            region_code_to_name = {}

            for r in country_results:
                if r.get("record_type_display") == "Region":
                    code = r.get("region")
                    name = r.get("name")
                    if isinstance(code, int) and name:
                        region_code_to_name[code] = str(name)

            for r in country_results:
                if r.get("record_type_display") != "Country":
                    continue
                iso3 = r.get("iso3")
                country_name = r.get("name")
                region_code = r.get("region")

                if iso3 and country_name:
                    iso3_to_country_name[str(iso3).upper()] = str(country_name)

                if iso3 and isinstance(region_code, int):
                    region_full = region_code_to_name.get(region_code)
                    if region_full:
                        iso3_to_region_name[str(iso3).upper()] = str(region_full).replace(" Region", "")
        except Exception:
            iso3_to_country_name = {}
            iso3_to_region_name = {}

        results = []
        for row in qset:
            warehouse_id = _safe_str(row.get("warehouse"))
            wh = wh_by_id.get(warehouse_id)
            if not wh:
                continue

            country_iso3 = wh.get("country_iso3", "")
            country_name = iso3_to_country_name.get(country_iso3, "")
            region_name = iso3_to_region_name.get(country_iso3, "")

            qty = row.get("total_qty")
            if qty is None:
                qty_out = 0
            elif isinstance(qty, Decimal):
                qty_out = float(qty)
            else:
                qty_out = float(qty) if qty else 0

            results.append(
                {
                    "warehouse_id": warehouse_id,
                    "warehouse_name": wh.get("warehouse_name", ""),
                    "country": country_name,
                    "country_iso3": country_iso3,
                    "region": region_name,
                    "stock_quantity": qty_out,
                }
            )

        return results
