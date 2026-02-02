from decimal import Decimal

import requests
from django.conf import settings
from django.db.models import Sum
from rest_framework import views
from rest_framework.response import Response

from api.models import (
    DimInventoryTransactionLine,
    DimProduct,
    DimProductCategory,
    DimWarehouse,
)
from api.esconnection import ES_CLIENT
from decimal import Decimal

import requests
from django.conf import settings
from django.db.models import Sum
from rest_framework import views
from rest_framework.response import Response

from api.models import (
    DimInventoryTransactionLine,
    DimProduct,
    DimProductCategory,
    DimWarehouse,
)
from api.esconnection import ES_CLIENT
from api.indexes import WAREHOUSE_INDEX_NAME

GOADMIN_COUNTRY_URL_DEFAULT = "https://goadmin.ifrc.org/api/v2/country/?limit=300"


def _safe_str(v):
    return "" if v is None else str(v)


def _fetch_goadmin_maps():
    url = getattr(settings, "GOADMIN_COUNTRY_URL", GOADMIN_COUNTRY_URL_DEFAULT)
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    data = resp.json()
    results = data.get("results", data) or []

    region_code_to_name = {}
    for r in results:
        if r.get("record_type_display") == "Region":
            code = r.get("region")
            name = r.get("name")
            if isinstance(code, int) and name:
                region_code_to_name[code] = str(name)

    iso2_to_iso3 = {}
    iso3_to_country_name = {}
    iso3_to_region_name = {}

    for r in results:
        if r.get("record_type_display") != "Country":
            continue

        iso2 = r.get("iso")
        iso3 = r.get("iso3")
        country_name = r.get("name")
        region_code = r.get("region")

        if iso2 and iso3:
            iso2_to_iso3[str(iso2).upper()] = str(iso3).upper()

        if iso3 and country_name:
            iso3_to_country_name[str(iso3).upper()] = str(country_name)

        if iso3 and isinstance(region_code, int):
            region_full = region_code_to_name.get(region_code)
            if region_full:
                iso3_to_region_name[str(iso3).upper()] = str(region_full).replace(" Region", "")

    return iso2_to_iso3, iso3_to_country_name, iso3_to_region_name


class WarehouseStocksView(views.APIView):
    permission_classes = []

    def get(self, request):
        only_available = request.query_params.get("only_available", "1") == "1"
        q = request.query_params.get("q", "").strip()
        region_q = request.query_params.get("region", "").strip()
        country_iso3 = (request.query_params.get("country_iso3") or "").upper()
        warehouse_name_q = request.query_params.get("warehouse_name", "").strip()
        item_group_q = request.query_params.get("item_group", "").strip()
        sort_field = request.query_params.get("sort", "")
        sort_order = request.query_params.get("order", "desc")
        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except Exception:
            page = 1
        try:
            page_size = int(request.query_params.get("page_size", 50))
        except Exception:
            page_size = 50
        page_size = min(max(page_size, 1), 1000)

        try:
            iso2_to_iso3, iso3_to_country_name, iso3_to_region_name = _fetch_goadmin_maps()
        except Exception:
            iso2_to_iso3, iso3_to_country_name, iso3_to_region_name = {}, {}, {}

        results = []
        total_hits = None

        if ES_CLIENT is not None:
            must = []
            filters = []

            if q:
                must.append(
                    {
                        "multi_match": {
                            "query": q,
                            "fields": ["item_name^3", "item_number", "item_group", "warehouse_name"],
                            "type": "best_fields",
                            "operator": "and",
                        }
                    }
                )

            if country_iso3:
                filters.append({"term": {"country_iso3": country_iso3}})

            if region_q:
                filters.append({"term": {"region": region_q}})

            if warehouse_name_q:
                filters.append({"match_phrase": {"warehouse_name": warehouse_name_q}})

            if item_group_q:
                filters.append({"term": {"item_group": item_group_q}})

            if must:
                query = {"bool": {"must": must, "filter": filters}} if filters else {"bool": {"must": must}}
            else:
                query = {"bool": {"filter": filters}} if filters else {"match_all": {}}

            if request.query_params.get("distinct", "0") == "1":
                aggs = {
                    "regions": {"terms": {"field": "region", "size": 1000}},
                    "countries": {"terms": {"field": "country_name.raw", "size": 1000}},
                    "item_groups": {"terms": {"field": "item_group", "size": 1000}},
                    "item_names": {"terms": {"field": "item_name.raw", "size": 1000}},
                }
                try:
                    resp = ES_CLIENT.search(index=WAREHOUSE_INDEX_NAME, body={"size": 0, "aggs": aggs})
                    aggregations = resp.get("aggregations", {}) or {}
                    regions = [b["key"] for b in aggregations.get("regions", {}).get("buckets", [])]
                    countries = [b["key"] for b in aggregations.get("countries", {}).get("buckets", [])]
                    item_groups = [b["key"] for b in aggregations.get("item_groups", {}).get("buckets", [])]
                    item_names = [b["key"] for b in aggregations.get("item_names", {}).get("buckets", [])]
                    return Response({
                        "regions": regions,
                        "countries": countries,
                        "item_groups": item_groups,
                        "item_names": item_names,
                    })
                except Exception:
                    pass

            body = {"from": (page - 1) * page_size, "size": page_size, "query": query}

            if sort_field:
                allowed_sorts = {
                    "quantity": "quantity",
                    "item_name": "item_name.raw",
                    "warehouse_name": "warehouse_name.raw",
                }
                sf = allowed_sorts.get(sort_field)
                if sf:
                    order = "asc" if sort_order.lower() == "asc" else "desc"
                    body["sort"] = [{sf: {"order": order}}]

            try:
                resp = ES_CLIENT.search(index=WAREHOUSE_INDEX_NAME, body=body)
                hits = resp.get("hits", {}).get("hits", []) or []
                total = resp.get("hits", {}).get("total") or {}
                if isinstance(total, dict):
                    total_hits = total.get("value", 0)
                elif isinstance(total, int):
                    total_hits = total
                else:
                    total_hits = None

                for h in hits:
                    src = h.get("_source", {})

                    country_iso3_src = (src.get("country_iso3") or "").upper()
                    country_name = iso3_to_country_name.get(country_iso3_src, "") if country_iso3_src else ""
                    region_name = iso3_to_region_name.get(country_iso3_src, "") if country_iso3_src else ""

                    qty = src.get("quantity")
                    if qty is None:
                        qty_out = None
                    else:
                        try:
                            qty_out = str(qty)
                        except Exception:
                            qty_out = None

                    results.append({
                        "id": src.get("id") or f"{src.get('warehouse_id','')}__{src.get('product_id','')}",
                        "region": region_name,
                        "country": country_name,
                        "country_iso3": country_iso3_src,
                        "warehouse_name": src.get("warehouse_name", ""),
                        "item_group": src.get("item_group", ""),
                        "item_name": src.get("item_name", ""),
                        "item_number": src.get("item_number", ""),
                        "unit": src.get("unit", ""),
                        "quantity": qty_out,
                    })
            except Exception:
                results = []

        if not results:
            warehouses = DimWarehouse.objects.all().values("id", "name", "country")
            wh_by_id = {
                str(w["id"]): {
                    "warehouse_name": _safe_str(w.get("name")),
                    "country_iso3": _safe_str(w.get("country")).upper(),
                }
                for w in warehouses
            }

            products = DimProduct.objects.all().values(
                "id",
                "name",
                "unit_of_measure",
                "product_category",
            )
            prod_by_id = {
                str(p["id"]): {
                    "item_number": _safe_str(p.get("id")),
                    "item_name": _safe_str(p.get("name")),
                    "unit": _safe_str(p.get("unit_of_measure")),
                    "product_category_code": _safe_str(p.get("product_category")),
                }
                for p in products
            }

            categories = DimProductCategory.objects.all().values("category_code", "name")
            cat_by_code = {str(c["category_code"]): _safe_str(c.get("name")) for c in categories}

            qset = DimInventoryTransactionLine.objects.all()
            if only_available:
                qset = qset.filter(item_status_name="Available")

            agg = qset.values("warehouse", "product").annotate(quantity=Sum("quantity"))

            for row in agg.iterator():
                warehouse_id = _safe_str(row.get("warehouse"))
                product_id = _safe_str(row.get("product"))

                wh = wh_by_id.get(warehouse_id)
                prod = prod_by_id.get(product_id)
                if not wh or not prod:
                    continue

                country_iso3 = (wh.get("country_iso3") or "").upper()
                if not country_iso3 and warehouse_id:
                    iso2 = warehouse_id[:2].upper()
                    country_iso3 = iso2_to_iso3.get(iso2, "")

                country_name = iso3_to_country_name.get(country_iso3, "") if country_iso3 else ""
                region_name = iso3_to_region_name.get(country_iso3, "") if country_iso3 else ""

                # apply region filter for DB fallback
                if region_q and region_name and region_name.lower() != region_q.lower():
                    continue

                item_group = cat_by_code.get(prod.get("product_category_code", ""), "")

                qty = row.get("quantity")
                if qty is None:
                    qty_out = None
                elif isinstance(qty, Decimal):
                    qty_out = format(qty, "f")
                else:
                    qty_out = str(qty)

                results.append(
                    {
                        "id": f"{warehouse_id}__{product_id}",
                        "region": region_name,
                        "country": country_name,
                        "country_iso3": country_iso3,
                        "warehouse_name": wh["warehouse_name"],
                        "item_group": item_group,
                        "item_name": prod.get("item_name", ""),
                        "item_number": prod.get("item_number", ""),
                        "unit": prod.get("unit", ""),
                        "quantity": qty_out,
                    }
                )

        resp_payload = {"results": results}
        if total_hits is not None:
            resp_payload.update({"total": total_hits, "page": page, "page_size": page_size})

        return Response(resp_payload)


class AggregatedWarehouseStocksView(views.APIView):
    """Return aggregated warehouse stock totals by country (and region).

    Response format:
    {
      "results": [
         {"country_iso3": "XXX", "country": "Name", "region": "Region", "total_quantity": "123.45", "warehouse_count": 10},
         ...
      ]
    }
    """

    permission_classes = []

    def get(self, request):
        only_available = request.query_params.get("only_available", "1") == "1"
        q = request.query_params.get("q", "").strip()
        region_q = request.query_params.get("region", "").strip()
        country_iso3 = (request.query_params.get("country_iso3") or "").upper()
        warehouse_name_q = request.query_params.get("warehouse_name", "").strip()
        item_group_q = request.query_params.get("item_group", "").strip()

        try:
            iso2_to_iso3, iso3_to_country_name, iso3_to_region_name = _fetch_goadmin_maps()
        except Exception:
            iso2_to_iso3, iso3_to_country_name, iso3_to_region_name = {}, {}, {}

        results = []

        if ES_CLIENT is not None:
            must = []
            filters = []

            if q:
                must.append(
                    {
                        "multi_match": {
                            "query": q,
                            "fields": ["item_name^3", "item_number", "item_group", "warehouse_name"],
                            "type": "best_fields",
                            "operator": "and",
                        }
                    }
                )

            if country_iso3:
                filters.append({"term": {"country_iso3": country_iso3}})

            if region_q:
                filters.append({"term": {"region": region_q}})

            if warehouse_name_q:
                filters.append({"match_phrase": {"warehouse_name": warehouse_name_q}})

            if item_group_q:
                filters.append({"term": {"item_group": item_group_q}})

            if must:
                query = {"bool": {"must": must, "filter": filters}} if filters else {"bool": {"must": must}}
            else:
                query = {"bool": {"filter": filters}} if filters else {"match_all": {}}

            aggs = {
                "by_country": {
                    "terms": {"field": "country_iso3", "size": 10000},
                    "aggs": {
                        "total_quantity": {"sum": {"field": "quantity"}},
                        "warehouse_count": {"cardinality": {"field": "warehouse_id"}},
                    },
                }
            }

            try:
                resp = ES_CLIENT.search(index=WAREHOUSE_INDEX_NAME, body={"size": 0, "query": query, "aggs": aggs})
                aggregations = resp.get("aggregations", {}) or {}
                buckets = aggregations.get("by_country", {}).get("buckets", [])
                for b in buckets:
                    iso3 = (b.get("key") or "").upper()
                    total_val = None
                    tq = b.get("total_quantity", {}).get("value")
                    if tq is not None:
                        try:
                            # convert to string to keep consistency with other endpoints
                            total_val = str(Decimal(tq))
                        except Exception:
                            try:
                                total_val = str(tq)
                            except Exception:
                                total_val = None

                    warehouse_count = b.get("warehouse_count", {}).get("value")

                    results.append(
                        {
                            "country_iso3": iso3,
                            "country": iso3_to_country_name.get(iso3, ""),
                            "region": iso3_to_region_name.get(iso3, ""),
                            "total_quantity": total_val,
                            "warehouse_count": int(warehouse_count) if warehouse_count is not None else None,
                        }
                    )
            except Exception:
                results = []

        if not results:
            # Fallback to DB aggregation
            warehouses = DimWarehouse.objects.all().values("id", "name", "country")
            wh_by_id = {
                str(w["id"]): {"warehouse_name": _safe_str(w.get("name")), "country_iso3": _safe_str(w.get("country")).upper()}
                for w in warehouses
            }

            qset = DimInventoryTransactionLine.objects.all()
            if only_available:
                qset = qset.filter(item_status_name="Available")

            # Aggregate per warehouse first, then roll up to country
            agg = qset.values("warehouse").annotate(quantity=Sum("quantity"))

            totals_by_country = {}
            counts_by_country = {}

            for row in agg.iterator():
                warehouse_id = _safe_str(row.get("warehouse"))
                wh = wh_by_id.get(warehouse_id)
                if not wh:
                    continue

                country_iso3 = (wh.get("country_iso3") or "").upper()
                if not country_iso3 and warehouse_id:
                    iso2 = warehouse_id[:2].upper()
                    country_iso3 = iso2_to_iso3.get(iso2, "")

                qty = row.get("quantity")
                if qty is None:
                    continue

                try:
                    qty_val = Decimal(qty)
                except Exception:
                    try:
                        qty_val = Decimal(str(qty))
                    except Exception:
                        continue

                totals_by_country[country_iso3] = totals_by_country.get(country_iso3, Decimal(0)) + qty_val
                counts_by_country[country_iso3] = counts_by_country.get(country_iso3, 0) + 1

            for iso3, total in totals_by_country.items():
                region_name = iso3_to_region_name.get(iso3, "")
                # apply region filter for DB fallback
                if region_q and region_name and region_name.lower() != region_q.lower():
                    continue

                results.append(
                    {
                        "country_iso3": iso3,
                        "country": iso3_to_country_name.get(iso3, ""),
                        "region": region_name,
                        "total_quantity": format(total, "f"),
                        "warehouse_count": counts_by_country.get(iso3, 0),
                    }
                )

        return Response({"results": results})
