import logging

from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower, Trim
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.permissions import DenyGuestUserPermission

from .esconnection import ES_CLIENT
from .filter_set import CleanedFrameworkAgreementFilter
from .indexes import CLEANED_FRAMEWORK_AGREEMENTS_INDEX_NAME
from .models import CleanedFrameworkAgreement, Country
from .serializers import FabricCleanedFrameworkAgreementSerializer

logger = logging.getLogger(__name__)


class CleanedFrameworkAgreementPagination(PageNumberPagination):
    """Page-number pagination for CleanedFrameworkAgreement listings."""

    page_size = 100
    page_size_query_param = "pageSize"
    max_page_size = 500


class CleanedFrameworkAgreementViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only, paginated API for CleanedFrameworkAgreement (Spark FA data).

    Exposed at /api/v2/fabric/cleaned-framework-agreements/ via the DRF router.
    Supports server-side filtering and ordering using camelCase query params.
    """

    serializer_class = FabricCleanedFrameworkAgreementSerializer
    permission_classes = [IsAuthenticated, DenyGuestUserPermission]
    filterset_class = CleanedFrameworkAgreementFilter
    pagination_class = CleanedFrameworkAgreementPagination
    ordering_fields = (
        "region_countries_covered",
        "item_category",
        "vendor_country",
        "agreement_id",
    )
    ordering = ("region_countries_covered",)

    @staticmethod
    def _split_csv(value):
        if not value:
            return []
        return [v.strip() for v in value.split(",") if v.strip()]

    @staticmethod
    def _map_es_doc(src):
        return {
            "id": src.get("id"),
            "agreementId": src.get("agreement_id"),
            "classification": src.get("classification"),
            "defaultAgreementLineEffectiveDate": src.get("default_agreement_line_effective_date"),
            "defaultAgreementLineExpirationDate": src.get("default_agreement_line_expiration_date"),
            "workflowStatus": src.get("workflow_status"),
            "status": src.get("status"),
            "pricePerUnit": src.get("price_per_unit"),
            "paLineProcurementCategory": src.get("pa_line_procurement_category"),
            "vendorName": src.get("vendor_name"),
            "vendorValidFrom": src.get("vendor_valid_from"),
            "vendorValidTo": src.get("vendor_valid_to"),
            "vendorCountry": src.get("vendor_country"),
            "regionCountriesCovered": src.get("region_countries_covered"),
            "itemType": src.get("item_type"),
            "itemCategory": src.get("item_category"),
            "itemServiceShortDescription": src.get("item_service_short_description"),
            "owner": src.get("owner"),
            "createdAt": src.get("created_at"),
            "updatedAt": src.get("updated_at"),
        }

    @staticmethod
    def _build_page_link(request, page_number):
        params = request.query_params.copy()
        params["page"] = page_number
        base_url = request.build_absolute_uri(request.path)
        query = params.urlencode()
        return f"{base_url}?{query}" if query else base_url

    def _es_list(self, request):
        if ES_CLIENT is None:
            return None

        try:
            page_size = self.pagination_class().get_page_size(request) or 100
        except Exception:
            page_size = 100

        try:
            page_number = int(request.query_params.get("page", 1))
        except Exception:
            page_number = 1
        page_number = max(page_number, 1)

        region_values = self._split_csv(request.query_params.get("regionCountriesCovered"))
        item_category_values = self._split_csv(request.query_params.get("itemCategory"))
        vendor_country_values = self._split_csv(request.query_params.get("vendorCountry"))

        filters = []
        if region_values:
            filters.append({"terms": {"region_countries_covered": region_values}})
        if item_category_values:
            filters.append({"terms": {"item_category": item_category_values}})
        if vendor_country_values:
            filters.append({"terms": {"vendor_country": vendor_country_values}})

        query = {"bool": {"filter": filters}} if filters else {"match_all": {}}

        sort_param = (request.query_params.get("sort") or "").strip()
        sort_map = {
            "regionCountriesCovered": "region_countries_covered",
            "itemCategory": "item_category",
            "vendorCountry": "vendor_country",
            "agreementId": "agreement_id",
        }

        sort_field = "region_countries_covered"
        sort_order = "asc"
        if sort_param:
            sort_order = "desc" if sort_param.startswith("-") else "asc"
            sort_key = sort_param[1:] if sort_param.startswith("-") else sort_param
            sort_field = sort_map.get(sort_key, sort_field)

        body = {
            "from": (page_number - 1) * page_size,
            "size": page_size,
            "query": query,
            "track_total_hits": True,
            "sort": [{sort_field: {"order": sort_order, "missing": "_last"}}],
        }

        try:
            resp = ES_CLIENT.search(index=CLEANED_FRAMEWORK_AGREEMENTS_INDEX_NAME, body=body)
        except Exception as exc:
            logger.warning("ES search failed for cleaned framework agreements: %s", str(exc)[:256])
            return None

        hits = resp.get("hits", {}).get("hits", []) or []
        total = resp.get("hits", {}).get("total") or {}
        if isinstance(total, dict):
            total_count = total.get("value", 0)
        elif isinstance(total, int):
            total_count = total
        else:
            total_count = 0

        results = [self._map_es_doc(h.get("_source", {}) or {}) for h in hits]

        next_link = None
        prev_link = None
        if total_count:
            if page_number * page_size < total_count:
                next_link = self._build_page_link(request, page_number + 1)
            if page_number > 1:
                prev_link = self._build_page_link(request, page_number - 1)

        return Response(
            {
                "count": total_count,
                "next": next_link,
                "previous": prev_link,
                "results": results,
            }
        )

    def list(self, request, *args, **kwargs):
        es_response = self._es_list(request)
        if es_response is not None:
            return es_response
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return CleanedFrameworkAgreement.objects.all()


class CleanedFrameworkAgreementItemCategoryOptionsView(APIView):
    """List distinct item categories for Spark framework agreements."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, DenyGuestUserPermission]

    @staticmethod
    def _es_item_categories():
        if ES_CLIENT is None:
            return None
        body = {
            "size": 0,
            "aggs": {
                "categories": {
                    "terms": {"field": "item_category", "size": 500, "order": {"_key": "asc"}},
                }
            },
        }
        try:
            resp = ES_CLIENT.search(index=CLEANED_FRAMEWORK_AGREEMENTS_INDEX_NAME, body=body)
        except Exception:
            return None
        buckets = resp.get("aggregations", {}).get("categories", {}).get("buckets", [])
        return Response({"results": [b["key"] for b in buckets]})

    def get(self, _request):
        es_response = self._es_item_categories()
        if es_response is not None:
            return es_response
        categories = (
            CleanedFrameworkAgreement.objects.exclude(item_category__isnull=True)
            .exclude(item_category__exact="")
            .values_list("item_category", flat=True)
            .distinct()
            .order_by("item_category")
        )
        return Response({"results": list(categories)})


class CleanedFrameworkAgreementSummaryView(APIView):
    """Summary statistics for Spark framework agreements."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, DenyGuestUserPermission]

    @staticmethod
    def _split_covered_countries(values):
        country_names = set()
        for value in values:
            for raw in value.replace(";", ",").split(","):
                normalized = raw.strip().lower()
                if normalized:
                    country_names.add(normalized)
        return country_names

    def _es_summary(self):
        if ES_CLIENT is None:
            return None

        body = {
            "size": 0,
            "aggs": {
                "agreement_count": {"cardinality": {"field": "agreement_id"}},
                "supplier_count": {"cardinality": {"field": "vendor_name.raw"}},
                "non_ifrc": {
                    "filter": {
                        "bool": {
                            "must_not": [
                                {"terms": {"owner": ["IFRC", "ifrc"]}},
                            ]
                        }
                    },
                    "aggs": {
                        "agreement_count": {"cardinality": {"field": "agreement_id"}},
                        "supplier_count": {"cardinality": {"field": "vendor_name.raw"}},
                    },
                },
                "item_categories": {
                    "terms": {
                        "field": "item_category",
                        "size": 10000,
                    }
                },
                "covered_countries": {
                    "terms": {
                        "field": "region_countries_covered",
                        "size": 10000,
                    }
                },
            },
        }

        try:
            resp = ES_CLIENT.search(index=CLEANED_FRAMEWORK_AGREEMENTS_INDEX_NAME, body=body)
        except Exception as exc:
            logger.warning("ES summary failed for cleaned framework agreements: %s", str(exc)[:256])
            return None

        aggs = resp.get("aggregations") or {}

        agreement_count = aggs.get("agreement_count", {}).get("value") or 0
        supplier_count = aggs.get("supplier_count", {}).get("value") or 0

        non_ifrc = aggs.get("non_ifrc", {})
        other_agreements = non_ifrc.get("agreement_count", {}).get("value") or 0
        other_suppliers = non_ifrc.get("supplier_count", {}).get("value") or 0

        item_category_buckets = aggs.get("item_categories", {}).get("buckets") or []
        normalized_categories = {
            str(bucket.get("key", "")).strip().lower() for bucket in item_category_buckets if str(bucket.get("key", "")).strip()
        }

        covered_buckets = aggs.get("covered_countries", {}).get("buckets") or []
        covered_values = [str(bucket.get("key", "")) for bucket in covered_buckets if bucket.get("key")]
        covered_names = self._split_covered_countries(covered_values)

        if any(name == "global" for name in covered_names):
            countries_covered = Country.objects.filter(is_deprecated=False, independent=True).count()
        else:
            country_name_map = {
                name.lower(): cid
                for name, cid in Country.objects.filter(is_deprecated=False, independent=True).values_list("name", "id")
            }
            covered_country_ids = {country_name_map[name] for name in covered_names if name in country_name_map}
            countries_covered = len(covered_country_ids)

        return {
            "ifrcFrameworkAgreements": agreement_count,
            "suppliers": supplier_count,
            "otherFrameworkAgreements": other_agreements,
            "otherSuppliers": other_suppliers,
            "countriesCovered": countries_covered,
            "itemCategoriesCovered": len(normalized_categories),
        }

    def get(self, _request):
        es_summary = self._es_summary()
        if es_summary is not None:
            return Response(es_summary)

        base_qs = CleanedFrameworkAgreement.objects.all()

        total_framework_agreements = (
            base_qs.exclude(agreement_id__isnull=True)
            .exclude(agreement_id__exact="")
            .values_list("agreement_id", flat=True)
            .distinct()
            .count()
        )

        total_suppliers = (
            base_qs.exclude(vendor_name__isnull=True)
            .exclude(vendor_name__exact="")
            .values_list("vendor_name", flat=True)
            .distinct()
            .count()
        )

        non_ifrc_qs = base_qs.exclude(owner__iexact="IFRC")

        other_framework_agreements = (
            non_ifrc_qs.exclude(agreement_id__isnull=True)
            .exclude(agreement_id__exact="")
            .values_list("agreement_id", flat=True)
            .distinct()
            .count()
        )

        other_suppliers = (
            non_ifrc_qs.exclude(vendor_name__isnull=True)
            .exclude(vendor_name__exact="")
            .values_list("vendor_name", flat=True)
            .distinct()
            .count()
        )

        item_categories_covered = (
            base_qs.exclude(item_category__isnull=True)
            .annotate(normalized=Lower(Trim("item_category")))
            .exclude(normalized__exact="")
            .values_list("normalized", flat=True)
            .distinct()
            .count()
        )

        if base_qs.filter(region_countries_covered__icontains="global").exists():
            countries_covered = Country.objects.filter(is_deprecated=False, independent=True).count()
        else:
            country_name_map = {
                name.lower(): cid
                for name, cid in Country.objects.filter(is_deprecated=False, independent=True).values_list("name", "id")
            }
            covered_country_ids = set()
            for value in (
                base_qs.exclude(region_countries_covered__isnull=True)
                .exclude(region_countries_covered__exact="")
                .values_list("region_countries_covered", flat=True)
            ):
                for normalized in self._split_covered_countries([value]):
                    match_id = country_name_map.get(normalized)
                    if match_id:
                        covered_country_ids.add(match_id)
            countries_covered = len(covered_country_ids)

        return Response(
            {
                "ifrcFrameworkAgreements": total_framework_agreements,
                "suppliers": total_suppliers,
                "otherFrameworkAgreements": other_framework_agreements,
                "otherSuppliers": other_suppliers,
                "countriesCovered": countries_covered,
                "itemCategoriesCovered": item_categories_covered,
            }
        )


class CleanedFrameworkAgreementMapStatsView(APIView):
    """Per-country stats for Spark framework agreements used in the map."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, DenyGuestUserPermission]

    @staticmethod
    def _normalize_country_name(value):
        if not value:
            return None
        return value.strip().lower() or None

    def _build_country_maps(self):
        country_values = Country.objects.filter(
            is_deprecated=False,
            independent=True,
        ).values_list("name", "iso3")
        name_to_iso3 = {}
        iso3_to_name = {}
        for name, iso3 in country_values:
            if not iso3:
                continue
            name_to_iso3[name.lower()] = iso3
            iso3_to_name[iso3] = name
        return name_to_iso3, iso3_to_name

    def _es_map_stats(self):
        if ES_CLIENT is None:
            return None

        body = {
            "size": 0,
            "aggs": {
                "by_country": {
                    "terms": {
                        "field": "region_countries_covered",
                        "size": 10000,
                    },
                    "aggs": {
                        "agreement_count": {"cardinality": {"field": "agreement_id"}},
                        "ifrc": {
                            "filter": {"term": {"owner": "IFRC"}},
                            "aggs": {
                                "agreement_count": {"cardinality": {"field": "agreement_id"}},
                            },
                        },
                        "other": {
                            "filter": {"bool": {"must_not": [{"term": {"owner": "IFRC"}}]}},
                            "aggs": {
                                "agreement_count": {"cardinality": {"field": "agreement_id"}},
                            },
                        },
                    },
                },
                "vendor_country": {
                    "terms": {
                        "field": "vendor_country",
                        "size": 10000,
                    },
                    "aggs": {
                        "agreement_count": {"cardinality": {"field": "agreement_id"}},
                    },
                },
            },
        }

        try:
            resp = ES_CLIENT.search(index=CLEANED_FRAMEWORK_AGREEMENTS_INDEX_NAME, body=body)
        except Exception as exc:
            logger.warning("ES map stats failed for cleaned framework agreements: %s", str(exc)[:256])
            return None

        return resp.get("aggregations") or {}

    def get(self, _request):
        name_to_iso3, iso3_to_name = self._build_country_maps()

        results = {}

        es_aggs = self._es_map_stats()
        if es_aggs is not None:
            country_buckets = es_aggs.get("by_country", {}).get("buckets") or []
            for bucket in country_buckets:
                raw_name = bucket.get("key")
                normalized = self._normalize_country_name(raw_name)
                if not normalized or normalized == "global":
                    continue
                if "," in normalized or ";" in normalized:
                    continue
                iso3 = name_to_iso3.get(normalized)
                if not iso3:
                    continue
                results[iso3] = {
                    "iso3": iso3,
                    "countryName": iso3_to_name.get(iso3),
                    "exclusiveFrameworkAgreements": bucket.get("agreement_count", {}).get("value", 0) or 0,
                    "exclusiveIfrcAgreements": bucket.get("ifrc", {}).get("agreement_count", {}).get("value", 0) or 0,
                    "exclusiveOtherAgreements": bucket.get("other", {}).get("agreement_count", {}).get("value", 0) or 0,
                    "vendorCountryAgreements": 0,
                }

            vendor_buckets = es_aggs.get("vendor_country", {}).get("buckets") or []
            for bucket in vendor_buckets:
                iso3 = bucket.get("key")
                if not iso3:
                    continue
                entry = results.get(iso3)
                if entry is None:
                    entry = {
                        "iso3": iso3,
                        "countryName": iso3_to_name.get(iso3),
                        "exclusiveFrameworkAgreements": 0,
                        "exclusiveIfrcAgreements": 0,
                        "exclusiveOtherAgreements": 0,
                        "vendorCountryAgreements": 0,
                    }
                    results[iso3] = entry
                entry["vendorCountryAgreements"] = bucket.get("agreement_count", {}).get("value", 0) or 0

            return Response({"results": list(results.values())})

        base_qs = CleanedFrameworkAgreement.objects.all()

        country_stats = (
            base_qs.exclude(region_countries_covered__isnull=True)
            .exclude(region_countries_covered__exact="")
            .exclude(region_countries_covered__iexact="global")
            .values("region_countries_covered")
            .annotate(
                agreement_count=models.Count("agreement_id", distinct=True),
                ifrc_count=models.Count("agreement_id", distinct=True, filter=Q(owner__iexact="IFRC")),
                other_count=models.Count("agreement_id", distinct=True, filter=~Q(owner__iexact="IFRC")),
            )
        )

        for row in country_stats:
            normalized = self._normalize_country_name(row.get("region_countries_covered"))
            if not normalized or "," in normalized or ";" in normalized:
                continue
            iso3 = name_to_iso3.get(normalized)
            if not iso3:
                continue
            results[iso3] = {
                "iso3": iso3,
                "countryName": iso3_to_name.get(iso3),
                "exclusiveFrameworkAgreements": row.get("agreement_count", 0),
                "exclusiveIfrcAgreements": row.get("ifrc_count", 0),
                "exclusiveOtherAgreements": row.get("other_count", 0),
                "vendorCountryAgreements": 0,
            }

        vendor_stats = (
            base_qs.exclude(vendor_country__isnull=True)
            .exclude(vendor_country__exact="")
            .values("vendor_country")
            .annotate(agreement_count=models.Count("agreement_id", distinct=True))
        )

        for row in vendor_stats:
            iso3 = row.get("vendor_country")
            if not iso3:
                continue
            entry = results.get(iso3)
            if entry is None:
                entry = {
                    "iso3": iso3,
                    "countryName": iso3_to_name.get(iso3),
                    "exclusiveFrameworkAgreements": 0,
                    "exclusiveIfrcAgreements": 0,
                    "exclusiveOtherAgreements": 0,
                    "vendorCountryAgreements": 0,
                }
                results[iso3] = entry
            entry["vendorCountryAgreements"] = row.get("agreement_count", 0)

        return Response({"results": list(results.values())})
