from abc import ABC
from typing import Dict

from alert_system.models import StacItems


class BaseFilter(ABC):

    hazard_threshold: Dict
    impact_threshold: Dict

    def __init__(self, stac_obj: StacItems):
        self.item = stac_obj

    def is_hazard_eligible(self) -> bool:
        """Return True if hazard passes filters."""
        return (
            self.item.severity_value > self.hazard_threshold["severity_value"]
            and self.item.severity_label == self.hazard_threshold["severity_label"]
        )

    def is_impact_eligible(self) -> bool:
        """Return True if impact passes filters."""
        key = (self.item.category, self.item.type)
        threshold = self.impact_threshold.get(key)
        if threshold is None:
            return False
        return self.item.value >= threshold

    def is_eligible(self) -> bool:
        if self.item.collection == StacItems.CollectionType.IMPACT:
            return self.is_impact_eligible()
        elif self.item.collection == StacItems.CollectionType.HAZARD:
            return self.is_hazard_eligible()
        return True
