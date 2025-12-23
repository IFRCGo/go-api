# NOTE: Store Config files here. Might need to refactor if source supports filtering with hazards.
class GdacsFloodConfig:
    def __init__(self):
        self.event_collection_type = "gdacs-events"
        self.hazard_collection_type = "gdacs-hazards"
        self.impact_collection_type = "gdacs-impacts"
        self.people_exposed_threshold = 500
        self.filter_event = {"hazard_codes": ["FL", "MH0600", "nat-hyd-flo-flo"]}


gdacs_flood_config = GdacsFloodConfig()
