from alert_system.etl.base.loader import BaseLoaderClass

from .config import usgs_earthquake_config


class USGSLoader(BaseLoaderClass):
    people_exposed_threshold = usgs_earthquake_config.people_exposed_threshold

    # NOTE: Add additional changes to the filter here. This is example only.
    def filter_eligible_items(self, load_obj):
        if load_obj.get("people_exposed") > USGSLoader.people_exposed_threshold:
            return True
        return False
