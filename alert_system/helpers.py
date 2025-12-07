from django.utils import timezone

from alert_system.models import Connector


def set_connector_status(connector, status):
    connector.status = status
    if status == Connector.Status.SUCCESS:
        connector.last_success_run = timezone.now()
    connector.save(update_fields=["status", "last_success_run"] if status == Connector.Status.SUCCESS else ["status"])


def get_connector_processor(connector_id: int):
    """
    Returns (processor_instance, connector) for a given connector ID
    """
    from .mappings import CONNECTOR_REGISTRY

    connector = Connector.objects.get(id=connector_id)
    processor = CONNECTOR_REGISTRY[connector.type].extractor(connector)
    return processor, connector


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
