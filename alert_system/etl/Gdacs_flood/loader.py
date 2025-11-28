from alert_system.etl.base.loader import BaseLoaderClass
from .config import gdacs_flood_config

class GdacsLoader(BaseLoaderClass):
    people_exposed_threshold = gdacs_flood_config.people_exposed_threshold

    # NOTE: Add additional changes to the filter here. This is example only.
    def filter_eligible_items(self, load_obj):
        if load_obj.get("people_exposed") > GdacsLoader.people_exposed_threshold:
            return True
        return False
