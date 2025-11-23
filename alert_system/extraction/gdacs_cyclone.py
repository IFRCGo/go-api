from alert_system.extraction.base_extraction import BaseExtractionClass

class GdacsCycloneExtraction(BaseExtractionClass):
    event_endpoint = "/gdacs-events/items"
    hazard_endpoint = "/gdacs-hazards/items"
    impact_endpoint = "/gdacs-impacts/items"
