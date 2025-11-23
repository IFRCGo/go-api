from .base_filter import BaseFilter


class USGSEarthquakeFilter(BaseFilter):
    impact_threshold = {
        ("people", "death"): 1,
        ("people", "injured"): 10,
        ("people", "missing"): 1,
    }

    hazard_threshold = {
        "severity_value": 5,
        "severity_label": "Green",
    }
