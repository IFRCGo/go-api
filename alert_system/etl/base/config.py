from typing import Dict, TypedDict


class ExtractionConfig(TypedDict):
    event_collection_type: str
    hazard_collection_type: str | None
    impact_collection_type: str | None

    filter_event: Dict | None
    filter_hazard: Dict | None
    filter_impact: Dict | None

    people_exposed_threshold: int
