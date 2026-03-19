# NOTE: Store Config files here. Might need to refactor if source supports filtering with hazards.
from alert_system.etl.base.config import ExtractionConfig

gdacs_cyclone_config: ExtractionConfig = {
    "event_collection_type": "gdacs-events",
    "hazard_collection_type": "gdacs-hazards",
    "impact_collection_type": "gdacs-impacts",
    "filter_event": {"hazard_codes": ["MH0309", "TC", "nat-met-sto-tro"]},
    "filter_hazard": None,
    "filter_impact": None,
    "people_exposed_threshold": 500,
}
