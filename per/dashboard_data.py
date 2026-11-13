from collections import defaultdict
from typing import Any

from django.db.models import Prefetch

from .dashboard_utils import AREA_NAMES
from .models import (
    AreaResponse,
    FormComponentResponse,
    FormPrioritization,
    FormPrioritizationComponent,
    Overview,
    PerAssessment,
)


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


def _assessment_sort_key(assessment: PerAssessment) -> tuple[int, int]:
    overview = assessment.overview
    return (overview.id if overview is not None else -1, assessment.id)


def _load_overviews() -> list[Overview]:
    return list(Overview.objects.select_related("country").order_by("id"))


def _load_assessments(overview_ids: list[int]) -> dict[int, list[PerAssessment]]:
    if not overview_ids:
        return {}

    component_response_queryset = FormComponentResponse.objects.select_related(
        "component",
        "component__area",
        "rating",
    ).defer(
        "urban_considerations",
        "epi_considerations",
        "climate_environmental_considerations",
        "migration_considerations",
        "notes",
    )
    assessment_queryset = (
        PerAssessment.objects.filter(overview_id__in=overview_ids)
        .select_related("overview", "overview__country")
        .order_by("overview_id", "-id")
        .prefetch_related(
            Prefetch(
                "area_responses",
                queryset=AreaResponse.objects.select_related("area").prefetch_related(
                    Prefetch("component_response", queryset=component_response_queryset)
                ),
            )
        )
    )
    assessments_by_overview: dict[int, list[PerAssessment]] = defaultdict(list)
    for assessment in assessment_queryset:
        if assessment.overview_id is not None:
            assessments_by_overview[assessment.overview_id].append(assessment)
    return dict(assessments_by_overview)


def _load_latest_prioritizations(overview_ids: list[int]) -> dict[int, FormPrioritization]:
    if not overview_ids:
        return {}

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
    return prioritization_by_overview


def _serialize_prioritized_components(prioritization: FormPrioritization | None) -> list[dict[str, Any]]:
    if prioritization is None:
        return []

    components: list[dict[str, Any]] = []
    for prioritized_component in prioritization.prioritized_action_responses.all():
        component = prioritized_component.component
        if (
            component is None
            # NOTE: The parent of component 14 is not a component of its own, only its sub-components are.
            or component.is_parent
            # Historic prioritization rows use NULL to mean that the component
            # is selected by its membership in this relation.  Only an explicit
            # False value means that it must not appear in the public summary.
            or prioritized_component.is_prioritized is False
        ):
            continue

        area = component.area
        components.append(
            {
                "componentId": component.id,
                "componentTitle": component.title or component.description,
                "areaTitle": _area_name(area),
                "areaNum": area.area_num if area is not None else None,
                "description": component.description,
            }
        )
    return components


def _base_process_data(overview: Overview) -> dict[str, Any]:
    country = overview.country
    return {
        "id": overview.id,
        "assessment_number": overview.assessment_number,
        "date_of_assessment": overview.date_of_assessment,
        "created_at": overview.created_at,
        "updated_at": overview.updated_at,
        "country_id": overview.country_id,
        "country_name": country.name if country is not None else None,
        "national_society_name": country.society_name if country is not None else None,
        "country_iso3": country.iso3 if country is not None else None,
        "region_id": country.region_id if country is not None else None,
        "latitude": _coordinate(country, "y"),
        "longitude": _coordinate(country, "x"),
        "phase": overview.phase,
        "type_of_assessment": overview.type_of_assessment_id,
        "assessment_method": overview.assessment_method,
    }


def _serialize_process(overview: Overview, prioritization: FormPrioritization | None) -> dict[str, Any]:
    return {
        **_base_process_data(overview),
        "prioritized_components": _serialize_prioritized_components(prioritization),
        "epi_considerations": overview.assess_preparedness_of_country,
        "climate_environmental_considerations": overview.assess_climate_environment_of_country,
        "urban_considerations": overview.assess_urban_aspect_of_country,
        "migration_considerations": overview.assess_migration_aspect_of_country,
    }


def get_per_map_data() -> dict[str, list[dict[str, Any]]]:
    overviews = _load_overviews()
    prioritization_by_overview = _load_latest_prioritizations([overview.id for overview in overviews])
    return {
        "processes": [_serialize_process(overview, prioritization_by_overview.get(overview.id)) for overview in overviews],
    }


def _component_assessment_metadata(assessment: PerAssessment) -> dict[str, Any]:
    overview = assessment.overview
    country = overview.country if overview is not None else None
    return {
        "assessment_id": assessment.id,
        "process_id": overview.id if overview is not None else None,
        "assessment_number": overview.assessment_number if overview is not None else None,
        "country_id": overview.country_id if overview is not None else None,
        "country_name": country.name if country is not None else None,
        "country_iso3": country.iso3 if country is not None else None,
        "region_id": country.region_id if country is not None else None,
        "date_of_assessment": overview.date_of_assessment if overview is not None else None,
        "type_of_assessment": overview.type_of_assessment_id if overview is not None else None,
        "assessment_method": overview.assessment_method if overview is not None else None,
        "updated_at": overview.updated_at if overview is not None else None,
    }


def _country_assessment_entry(
    overview: Overview,
    assessment: PerAssessment | None,
) -> dict[str, Any]:
    base = _base_process_data(overview)
    return {
        "assessment_id": assessment.id if assessment is not None else None,
        "process_id": base["id"],
        "assessment_number": base["assessment_number"],
        "country_id": base["country_id"],
        "country_name": base["country_name"],
        "country_iso3": base["country_iso3"],
        "region_id": base["region_id"],
        "date_of_assessment": base["date_of_assessment"],
        "type_of_assessment": base["type_of_assessment"],
        "assessment_method": base["assessment_method"],
        "updated_at": base["updated_at"],
        "date": base["date_of_assessment"],
        "phase": base["phase"],
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
        "component_letter": component.component_letter,
        "is_parent": bool(component.is_parent),
        "area_id": area.id if area is not None else None,
        "area_num": area.area_num if area is not None else None,
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
    assessments_by_overview = _load_assessments([overview.id for overview in overviews])
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
                    "component_letter": component["component_letter"],
                    "is_parent": component["is_parent"],
                    "component_name": component["component_name"],
                    "area_id": component["area_id"],
                    "area_num": component["area_num"],
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

    for overview in overviews:
        country = overview.country
        if country is None:
            continue
        overview_assessments = assessments_by_overview.get(overview.id, [])
        latest_assessment = overview_assessments[0] if overview_assessments else None
        country_assessments[country.name].append(_country_assessment_entry(overview, latest_assessment))

    items = sorted(
        component_map.values(),
        key=lambda item: (
            item["area_num"] or 0,
            item["component_num"] or 0,
            item["component_letter"] or "",
            item["component_id"] or 0,
        ),
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
