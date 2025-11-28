# NOTE: Store Config files here. Might need to refactor if source supports filtering with hazards.
class GdacsFloodConfig:
    def __init__(self):
        self.event_endpoint = "/gdacs-events/items"
        self.hazard_endpoint = "/gdacs-hazards/items"
        self.impact_endpoint = "/gdacs-impacts/items"
        self.people_exposed_threshold = 5

gdacs_flood_config = GdacsFloodConfig()
