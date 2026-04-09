# Helper functions to build search params.


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


def build_guid_filter(guid: str) -> str:
    return f"monty:guid = '{guid}'"


def build_stac_search(
    collections: str,
    guid: str | None = None,
    additional_filters: list[str] | None = None,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
    extra_params: dict | None = None,
) -> dict:
    filters = additional_filters.copy() if additional_filters else []

    if guid:
        filters.append(build_guid_filter(guid))

    return build_search_params(
        collections=collections,
        cql_filters=filters,
        extra_params=extra_params,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
    )
