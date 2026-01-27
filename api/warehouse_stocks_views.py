import requests
from decimal import Decimal

from django.conf import settings
from django.db.models import Sum
from rest_framework import views
from rest_framework.response import Response

from api.models import (
    DimInventoryTransactionLine,
    DimWarehouse,
    DimProduct,
    DimProductCategory,
)

GOADMIN_COUNTRY_URL_DEFAULT = "https://goadmin.ifrc.org/api/v2/country/?limit=300"

def _safe_str(v):
    return "" if v is None else str(v)

def _fetch_goadmin_maps():
    """
    Returns:
      iso2_to_iso3: {"YE": "YEM", ...}
      iso3_to_country_name: {"PAN": "Panama", ...}
      iso3_to_region_name: {"PAN": "Americas", ...}
    """
    url = getattr(settings, "GOADMIN_COUNTRY_URL", GOADMIN_COUNTRY_URL_DEFAULT)
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    data = resp.json()
    results = data.get("results", data) or []

    # Region objects: region code is in r["region"], name is r["name"]
    # Country objects: region code is in r["region"]
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

        # GO Admin maps
        try:
            iso2_to_iso3, iso3_to_country_name, iso3_to_region_name = _fetch_goadmin_maps()
        except Exception:
            iso2_to_iso3, iso3_to_country_name, iso3_to_region_name = {}, {}, {}

        # Lookups
        warehouses = DimWarehouse.objects.all().values("id", "name", "country")
        wh_by_id = {
            str(w["id"]): {
                "warehouse_name": _safe_str(w.get("name")),
                "country_iso3": _safe_str(w.get("country")).upper(),  # may be blank
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

        q = DimInventoryTransactionLine.objects.all()
        if only_available:
            q = q.filter(item_status_name="Available")

        agg = q.values("warehouse", "product").annotate(quantity=Sum("quantity"))

        results = []
        for row in agg.iterator():
            warehouse_id = _safe_str(row.get("warehouse"))
            product_id = _safe_str(row.get("product"))

            wh = wh_by_id.get(warehouse_id)
            prod = prod_by_id.get(product_id)
            if not wh or not prod:
                continue

            # ISO3: prefer warehouse.country, else derive from first 2 chars (ISO2 -> ISO3)
            country_iso3 = (wh.get("country_iso3") or "").upper()
            if not country_iso3 and warehouse_id:
                iso2 = warehouse_id[:2].upper()
                country_iso3 = iso2_to_iso3.get(iso2, "")

            # Display names
            country_name = iso3_to_country_name.get(country_iso3, "") if country_iso3 else ""
            region_name = iso3_to_region_name.get(country_iso3, "") if country_iso3 else ""

            item_group = cat_by_code.get(prod.get("product_category_code", ""), "")

            qty = row.get("quantity")
            if qty is None:
                qty_out = None
            elif isinstance(qty, Decimal):
                qty_out = format(qty, "f")
            else:
                qty_out = str(qty)

            results.append({
                "id": f"{warehouse_id}__{product_id}",
                "region": region_name,              # e.g. "Americas"
                "country": country_name,            # e.g. "Panama"  
                "country_iso3": country_iso3,       # e.g. "PAN"
                "warehouse_name": wh["warehouse_name"],
                "item_group": item_group,
                "item_name": prod.get("item_name", ""),
                "item_number": prod.get("item_number", ""),
                "unit": prod.get("unit", ""),
                "quantity": qty_out,
            })

        return Response({"results": results})