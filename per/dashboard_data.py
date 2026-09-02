from collections import defaultdict
from typing import Any

from django.db.models import Prefetch

from .models import (
    AreaResponse,
    FormComponentResponse,
    FormPrioritization,
    FormPrioritizationComponent,
    Overview,
    PerAssessment,
)

AREA_NAMES = {
    1: "Policy Strategy and Standards",
    2: "Analysis and planning",
    3: "Operational capacity",
    4: "Coordination",
    5: "Operations support",
}

AFFIRMATIVE_WORDS = {
    "yes",
    "si",
    "sí",
    "oui",
    "da",
    "ja",
    "sim",
    "aye",
    "yep",
    "igen",
    "hai",
    "evet",
    "是",
    "はい",
    "예",
    "نعم",
}


def _contains_affirmative(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False

    normalized = value.casefold()
    return any(word in normalized for word in AFFIRMATIVE_WORDS)


def _phase_display(phase: int | None) -> str | None:
    try:
        display = Overview.Phase(phase).label
    except (TypeError, ValueError):
        return None

    if display == "Action And Accountability":
        return "Action & accountability"
    if display == "WorkPlan":
        return "Workplan"
    return display


def _area_name(area: Any) -> str | None:
    if area is None:
        return None

    area_number = getattr(area, "area_num", None)
    if isinstance(area_number, int):
        return AREA_NAMES.get(area_number, getattr(area, "title", None))
    return getattr(area, "title", None) or getattr(area, "name", None)


def _coordinate(country: Any, coordinate: str) -> float | None:
    if country is None:
        return None

    centroid = getattr(country, "centroid", None)
    if centroid is not None:
        value = getattr(centroid, coordinate, None)
    else:
        fallback_coordinate = {"x": "longitude", "y": "latitude"}[coordinate]
        value = getattr(country, fallback_coordinate, None)

    return round(value, 5) if value is not None else None


def _date_sort_key(value: Any) -> int:
    return value.toordinal() if value is not None else -1


def _datetime_sort_key(value: Any) -> float:
    if value is None:
        return 0.0

    try:
        return value.timestamp()
    except (AttributeError, OSError, OverflowError, ValueError):
        return 0.0


def _overview_sort_key(overview: Overview) -> tuple[int, int, float, int]:
    return (
        overview.assessment_number if overview.assessment_number is not None else -1,
        _date_sort_key(overview.date_of_assessment),
        _datetime_sort_key(overview.updated_at),
        overview.id,
    )


def _assessment_sort_key(assessment: PerAssessment) -> tuple[int, int]:
    overview = assessment.overview
    return (overview.id if overview is not None else -1, assessment.id)


def _load_overviews() -> list[Overview]:
    return list(
        Overview.objects.select_related(
            "country",
            "country__region",
            "type_of_assessment",
        ).order_by("id")
    )


def _load_related_data(
    overview_ids: list[int],
    *,
    latest_assessment_only: bool = False,
    include_prioritization: bool = True,
    include_component_details: bool = True,
) -> tuple[dict[int, list[PerAssessment]], dict[int, FormPrioritization]]:
    if not overview_ids:
        return {}, {}

    component_response_queryset = FormComponentResponse.objects.select_related(
        "component",
        "component__area",
        "rating",
    )
    if not include_component_details:
        component_response_queryset = component_response_queryset.defer(
            "urban_considerations",
            "epi_considerations",
            "climate_environmental_considerations",
            "migration_considerations",
            "notes",
        )

    assessment_queryset = PerAssessment.objects.filter(overview_id__in=overview_ids).select_related(
        "overview", "overview__country", "overview__country__region", "overview__type_of_assessment"
    )
    if latest_assessment_only:
        assessment_queryset = assessment_queryset.order_by("overview_id", "-id").distinct("overview_id")
    else:
        assessment_queryset = assessment_queryset.order_by("overview_id", "-id")
    assessment_queryset = assessment_queryset.prefetch_related(
        Prefetch(
            "area_responses",
            queryset=AreaResponse.objects.select_related("area").prefetch_related(
                Prefetch("component_response", queryset=component_response_queryset)
            ),
        )
    )
    assessments_by_overview: dict[int, list[PerAssessment]] = defaultdict(list)
    for assessment in assessment_queryset:
        if assessment.overview_id is not None:
            assessments_by_overview[assessment.overview_id].append(assessment)

    if not include_prioritization:
        return dict(assessments_by_overview), {}

    prioritization_queryset = (
        FormPrioritization.objects.filter(overview_id__in=overview_ids)
        .order_by("overview_id", "-id")
        .prefetch_related(
            Prefetch(
                "prioritized_action_responses",
                queryset=FormPrioritizationComponent.objects.select_related("component", "component__area"),
            )
        )
    )
    prioritization_by_overview: dict[int, FormPrioritization] = {}
    for prioritization in prioritization_queryset:
        prioritization_by_overview.setdefault(prioritization.overview_id, prioritization)

    return dict(assessments_by_overview), prioritization_by_overview


def _serialize_component_response(response: FormComponentResponse) -> dict[str, Any] | None:
    component = response.component
    if component is None:
        return None

    area = component.area
    rating = response.rating
    return {
        "response_id": response.id,
        "component_id": component.id,
        "component_name": component.title or component.description,
        "component_num": component.component_num,
        "area_id": area.id if area is not None else None,
        "area_name": _area_name(area),
        "rating_id": rating.id if rating is not None else None,
        "rating_value": rating.value if rating is not None else None,
        "rating_title": rating.title if rating is not None else None,
        "urban_considerations": response.urban_considerations,
        "epi_considerations": response.epi_considerations,
        "climate_environmental_considerations": response.climate_environmental_considerations,
        "migration_considerations": response.migration_considerations,
        "notes": response.notes,
    }


def _serialize_assessment_components(assessment: PerAssessment | None) -> list[dict[str, Any]]:
    if assessment is None:
        return []

    components: list[dict[str, Any]] = []
    for area_response in assessment.area_responses.all():
        for component_response in area_response.component_response.all():
            serialized = _serialize_component_response(component_response)
            if serialized is not None:
                components.append(serialized)
    return components


def _serialize_prioritized_components(prioritization: FormPrioritization | None) -> list[dict[str, Any]]:
    if prioritization is None:
        return []

    components: list[dict[str, Any]] = []
    for prioritized_component in prioritization.prioritized_action_responses.all():
        component = prioritized_component.component
        if (
            component is None
            or component.id == 14
            # Historic prioritization rows use NULL to mean that the component
            # is selected by its membership in this relation.  Only an explicit
            # False value means that it must not appear in the public summary.
            or prioritized_component.is_prioritized is False
        ):
            continue

        components.append(
            {
                "componentId": component.id,
                "componentTitle": component.title or component.description,
                "areaTitle": _area_name(component.area),
                "description": component.description,
            }
        )
    return components


def _base_process_data(overview: Overview) -> dict[str, Any]:
    country = overview.country
    region = country.region if country is not None else None
    type_of_assessment = overview.type_of_assessment
    latitude = _coordinate(country, "y")
    longitude = _coordinate(country, "x")

    return {
        "id": overview.id,
        "assessment_number": overview.assessment_number,
        "date_of_assessment": overview.date_of_assessment,
        "assessment_date": overview.date_of_assessment,
        "created_at": overview.created_at,
        "updated_at": overview.updated_at,
        "country_id": overview.country_id,
        "country_name": country.name if country is not None else None,
        "country_iso3": country.iso3 if country is not None else None,
        "region_id": country.region_id if country is not None else None,
        "region_name": region.label if region is not None else None,
        "latitude": latitude,
        "longitude": longitude,
        "lat": latitude,
        "lon": longitude,
        "phase": overview.phase,
        "phase_display": _phase_display(overview.phase),
        "type_of_assessment": overview.type_of_assessment_id,
        "type_of_assessment_name": type_of_assessment.name if type_of_assessment is not None else None,
        "assessment_method": overview.assessment_method,
    }


def _serialize_process(
    overview: Overview,
    assessments: list[PerAssessment],
    prioritization: FormPrioritization | None,
) -> dict[str, Any]:
    latest_assessment = assessments[0] if assessments else None
    component_responses = _serialize_assessment_components(latest_assessment)
    derived_considerations = {
        "epi_considerations": any(_contains_affirmative(item["epi_considerations"]) for item in component_responses),
        "climate_environmental_considerations": any(
            _contains_affirmative(item["climate_environmental_considerations"]) for item in component_responses
        ),
        "urban_considerations": any(_contains_affirmative(item["urban_considerations"]) for item in component_responses),
        "migration_considerations": any(_contains_affirmative(item["migration_considerations"]) for item in component_responses),
    }

    return {
        **_base_process_data(overview),
        "prioritized_components": _serialize_prioritized_components(prioritization),
        "epi_considerations": overview.assess_preparedness_of_country,
        "climate_environmental_considerations": overview.assess_climate_environment_of_country,
        "urban_considerations": overview.assess_urban_aspect_of_country,
        "migration_considerations": overview.assess_migration_aspect_of_country,
        "epi_considerations_from_assessment": derived_considerations["epi_considerations"],
        "climate_environmental_considerations_from_assessment": derived_considerations["climate_environmental_considerations"],
        "urban_considerations_from_assessment": derived_considerations["urban_considerations"],
        "migration_considerations_from_assessment": derived_considerations["migration_considerations"],
        "components": component_responses,
    }


def get_per_map_data() -> dict[str, list[dict[str, Any]]]:
    overviews = _load_overviews()
    assessments_by_overview, prioritization_by_overview = _load_related_data(
        [overview.id for overview in overviews],
        latest_assessment_only=True,
    )
    processes = [
        _serialize_process(
            overview,
            assessments_by_overview.get(overview.id, []),
            prioritization_by_overview.get(overview.id),
        )
        for overview in overviews
    ]

    latest_overview_by_country: dict[int | None, Overview] = {}
    latest_process_by_country: dict[int | None, dict[str, Any]] = {}
    for overview, process in zip(overviews, processes):
        current = latest_overview_by_country.get(overview.country_id)
        if current is None or _overview_sort_key(overview) > _overview_sort_key(current):
            latest_overview_by_country[overview.country_id] = overview
            latest_process_by_country[overview.country_id] = process

    results = sorted(
        latest_process_by_country.values(),
        key=lambda process: (
            process["country_id"] is None,
            process["country_id"] if process["country_id"] is not None else 0,
        ),
    )

    return {
        "results": results,
        "processes": processes,
    }


def _component_assessment_metadata(assessment: PerAssessment) -> dict[str, Any]:
    overview = assessment.overview
    country = overview.country if overview is not None else None
    region = country.region if country is not None else None
    type_of_assessment = overview.type_of_assessment if overview is not None else None
    return {
        "assessment_id": assessment.id,
        "process_id": overview.id if overview is not None else None,
        "assessment_number": overview.assessment_number if overview is not None else None,
        "country_id": overview.country_id if overview is not None else None,
        "country_name": country.name if country is not None else None,
        "country_iso3": country.iso3 if country is not None else None,
        "region_id": country.region_id if country is not None else None,
        "region_name": region.label if region is not None else None,
        "date_of_assessment": overview.date_of_assessment if overview is not None else None,
        "type_of_assessment": overview.type_of_assessment_id if overview is not None else None,
        "type_of_assessment_name": type_of_assessment.name if type_of_assessment is not None else None,
        "assessment_method": overview.assessment_method if overview is not None else None,
        "updated_at": overview.updated_at if overview is not None else None,
    }


def _country_assessment_entry(assessment: PerAssessment) -> dict[str, Any]:
    overview = assessment.overview
    metadata = _component_assessment_metadata(assessment)
    return {
        **metadata,
        "date": metadata["date_of_assessment"],
        "phase": overview.phase if overview is not None else None,
        "phase_display": _phase_display(overview.phase) if overview is not None else None,
    }


def _serialize_performance_component_response(
    response: FormComponentResponse,
) -> dict[str, Any] | None:
    component = response.component
    if component is None:
        return None

    area = component.area
    rating = response.rating
    return {
        "component_id": component.id,
        "component_name": component.title or component.description,
        "component_num": component.component_num,
        "area_id": area.id if area is not None else None,
        "area_name": _area_name(area),
        "rating_value": rating.value if rating is not None else None,
        "rating_title": rating.title if rating is not None else None,
    }


def _serialize_performance_assessment_components(
    assessment: PerAssessment,
) -> list[dict[str, Any]]:
    components: list[dict[str, Any]] = []
    for area_response in assessment.area_responses.all():
        for component_response in area_response.component_response.all():
            serialized = _serialize_performance_component_response(component_response)
            if serialized is not None:
                components.append(serialized)
    return components


def get_per_dashboard_data() -> dict[str, Any]:
    overviews = _load_overviews()
    assessments_by_overview, _ = _load_related_data(
        [overview.id for overview in overviews],
        include_prioritization=False,
        include_component_details=False,
    )
    component_map: dict[int, dict[str, Any]] = {}
    country_assessments: dict[str, list[dict[str, Any]]] = defaultdict(list)

    assessments = sorted(
        [assessment for values in assessments_by_overview.values() for assessment in values],
        key=_assessment_sort_key,
    )
    for assessment in assessments:
        metadata = _component_assessment_metadata(assessment)
        components = _serialize_performance_assessment_components(assessment)
        for component in components:
            component_id = component["component_id"]
            component_map.setdefault(
                component_id,
                {
                    "component_id": component_id,
                    "component_num": component["component_num"],
                    "component_name": component["component_name"],
                    "area_id": component["area_id"],
                    "area_name": component["area_name"],
                    "assessments": [],
                },
            )["assessments"].append(
                {
                    **metadata,
                    "rating_value": component["rating_value"],
                    "rating_title": component["rating_title"],
                }
            )

        country_name = metadata["country_name"]
        if country_name:
            country_assessments[country_name].append(_country_assessment_entry(assessment))

    items = sorted(
        component_map.values(),
        key=lambda item: (item["area_id"] or 0, item["component_num"] or 0, item["component_id"] or 0),
    )
    for item in items:
        item["assessments"].sort(
            key=lambda assessment: (
                assessment["country_id"] if assessment["country_id"] is not None else -1,
                assessment["assessment_number"] if assessment["assessment_number"] is not None else -1,
                _date_sort_key(assessment["date_of_assessment"]),
                assessment["assessment_id"],
            )
        )

    return {
        "assessments": items,
        "countryAssessments": dict(country_assessments),
    }
