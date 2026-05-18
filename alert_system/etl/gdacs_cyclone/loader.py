from alert_system.etl.base.loader import BaseLoaderClass

from .config import gdacs_cyclone_config


class GdacsCycloneLoader(BaseLoaderClass):

    def filter_eligible_items(self, load_obj):
        people_exposed = load_obj.get("people_exposed")
        if people_exposed is None:
            return False
        return people_exposed > gdacs_cyclone_config["people_exposed_threshold"]
