from alert_system.extraction.base_extraction import BaseExtractionClass

class USGSEarthquakeExtraction(BaseExtractionClass):
    event_endpoint = "/usgs-events/items"
    hazard_endpoint = "/usgs-hazards/items"
    impact_endpoint = "/usgs-impacts/items"
