# Helper functions to build search params.


def build_search_params(
    collections: str,
    cql_filters: list[str] | None = None,
    extra_params: dict | None = None,
) -> dict:
    params = {
        "collections": collections,
    }

    if cql_filters:
        combined_filter = " AND ".join(f"({f})" for f in cql_filters if f)
        params["filter-lang"] = "cql2-text"
        params["filter"] = combined_filter

    if extra_params:
        params.update(extra_params)

    return params


def build_guid_filter(guid: str) -> str:
    return f"monty:guid = '{guid}'"


def build_forecasted_filter(forecasted: bool):
    return f"forecasted = {forecasted}"


def build_datetime_filter(start_date: str, end_date: str) -> str:
    return f"datetime >= '{start_date}' AND datetime < '{end_date}'"


def build_stac_search(
    collections: str,
    guid: str | None = None,
    additional_filters: list[str] | None = None,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
    extra_params: dict | None = None,
    forecasted_data: bool | None = False,
) -> dict:
    filters = additional_filters.copy() if additional_filters else []

    if forecasted_data:
        filters.append(build_forecasted_filter(forecasted_data))
    if guid:
        filters.append(build_guid_filter(guid))
    if start_datetime and end_datetime:
        filters.append(build_datetime_filter(start_datetime, end_datetime))

    return build_search_params(
        collections=collections,
        cql_filters=filters,
        extra_params=extra_params,
    )
