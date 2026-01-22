# Helper functions to build search params.


def build_search_params(
    collections: str,
    cql_filters: list[str] | None = None,
    datetime_range: str | None = None,
    extra_params: dict | None = None,
) -> dict:
    params = {
        "collections": collections,
    }

    if cql_filters:
        combined_filter = " AND ".join(f"({f})" for f in cql_filters if f)
        params["filter-lang"] = "cql2-text"
        params["filter"] = combined_filter

    if datetime_range:
        params["datetime"] = datetime_range

    if extra_params:
        params.update(extra_params)

    return params


def build_correlation_filter(correlation_id: str | None) -> str | None:
    if correlation_id:
        return f"monty:corr_id = '{correlation_id}'"
    return None


def build_stac_search(
    collections: str,
    correlation_id: str | None = None,
    additional_filters: list[str] | None = None,
    datetime_range: str | None = None,
    extra_params: dict | None = None,
) -> dict:
    filters = additional_filters.copy() if additional_filters else []

    corr_filter = build_correlation_filter(correlation_id)
    if corr_filter:
        filters.append(corr_filter)

    return build_search_params(
        collections=collections,
        cql_filters=filters,
        datetime_range=datetime_range,
        extra_params=extra_params,
    )
