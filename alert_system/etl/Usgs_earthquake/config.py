class USGSEarthquakeConfig:
    def __init__(self):
        self.event_collection_type = "usgs-events"
        self.hazard_collection_type = "usgs-hazards"
        self.impact_collection_type = "usgs-impacts"
        self.people_exposed_threshold = 50
        self.filter_event = {"hazard_codes": ["EQ", "GH0101", "nat-geo-ear-gro"]}


usgs_earthquake_config = USGSEarthquakeConfig()
