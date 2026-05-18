# Helper functions to build search params.
from typing import Dict, Generator, Optional

import httpx


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
    response = httpx.get(url=url, params=payload, timeout=timeout)
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
