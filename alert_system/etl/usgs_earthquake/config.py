from alert_system.etl.base.config import ExtractionConfig

usgs_earthquake_config: ExtractionConfig = {
    "event_collection_type": "usgs-events",
    "hazard_collection_type": "usgs-hazards",
    "impact_collection_type": "usgs-impacts",
    "filter_event": {"hazard_codes": ["EQ", "GH0101", "nat-geo-ear-gro"]},
    "filter_hazard": None,
    "filter_impact": None,
    "people_exposed_threshold": 500,
}
