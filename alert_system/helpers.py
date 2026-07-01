# Helper functions to build search params.
from typing import Dict, Generator, Optional
from urllib.parse import urlsplit, urlunsplit

import httpx
from django.conf import settings


def _remap_stac_url(url: str) -> str:
    """
    Rewrite a STAC URL to point at the internal cluster service.
    """
    external_base = getattr(settings, "EOAPI_STAC_EXTERNAL_URL", None)
    internal_base = getattr(settings, "EOAPI_STAC_INTERNAL_URL", None)
    if not external_base or not internal_base:
        return url

    ext = urlsplit(external_base.rstrip("/"))
    internal = urlsplit(internal_base.rstrip("/"))
    parsed = urlsplit(url)

    if parsed.netloc not in (ext.netloc, internal.netloc):
        return url

    path = parsed.path
    if ext.path and path.startswith(ext.path):
        path = path[len(ext.path) :]

    return urlunsplit((internal.scheme, internal.netloc, internal.path + path, parsed.query, parsed.fragment))


def build_search_params(
    collections: str,
    cql_filters: list[str] | None = None,
    extra_params: dict | None = None,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
) -> dict:
    params = {
        "collections": collections,
    }

    if cql_filters:
        combined_filter = " AND ".join(f"({f})" for f in cql_filters if f)
        params["filter-lang"] = "cql2-text"
        params["filter"] = combined_filter

    if start_datetime and end_datetime:
        params["datetime"] = f"{start_datetime}/{end_datetime}"

    if extra_params:
        params.update(extra_params)

    return params


def build_hazard_filter(hazard_codes: list) -> str:
    hazard_cql = " OR ".join(f"a_contains(monty:hazard_codes, '{hc}')" for hc in hazard_codes)
    return hazard_cql


def build_stac_search(
    collections: str,
    additional_filters: list[str] | None = None,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
    extra_params: dict | None = None,
    hazard_codes: list | None = None,
) -> dict:
    filters = additional_filters.copy() if additional_filters else []

    if hazard_codes:
        filters.append(f"({build_hazard_filter(hazard_codes=hazard_codes)})")

    return build_search_params(
        collections=collections,
        cql_filters=filters,
        extra_params=extra_params,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
    )


def fetch_stac_data(url: str, payload: dict | None = None, timeout: int | None = 60):
    response = httpx.get(url=_remap_stac_url(url), params=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def fetch_paginated_stac_data(url: str, filters: Optional[Dict] = None, timeout: int | None = 60) -> Generator[Dict, None, None]:
    """
    Fetch STAC data with pagination support.

    """
    current_url = url
    current_payload = filters.copy() if filters else None

    while current_url:
        data = fetch_stac_data(current_url, current_payload)

        yield from data.get("features", [])

        # Find next page link
        current_url = next((link["href"] for link in data.get("links", []) if link.get("rel") == "next"), None)
        current_payload = None  # Only use params on first request
