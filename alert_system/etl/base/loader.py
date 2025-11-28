import logging
from abc import ABC, abstractmethod
from typing import Dict

from alert_system.models import Connector, LoadItems

logger = logging.getLogger(__name__)


class BaseLoaderClass(ABC):
    """Loads transformed data into DisasterEvent table."""

    @abstractmethod
    def filter_eligible_items(self, load_obj):
        raise NotImplementedError()

    def load(self, transformed_data: Dict, connector: Connector) -> LoadItems:
        """
        Save aggregated event.

        Args:
            transformed_data: Output from transformer.transform()
            connector: The connector this data came from

        Returns:
            Created DisasterEvent object
        """
        correlation_id = transformed_data["correlation_id"]
        is_item_eligible = self.filter_eligible_items(transformed_data)

        load_obj, created = LoadItems.objects.update_or_create(
            correlation_id=correlation_id,
            defaults={
                "connector": connector,
                "event_title": transformed_data.get("title"),
                "event_description": transformed_data.get("description"),
                "country": transformed_data.get("country"),
                "severity_value": transformed_data.get("severity_value"),
                "severity_label": transformed_data.get("severity_label"),
                "severity_unit": transformed_data.get("severity_unit"),
                "total_people_exposed": transformed_data.get("people_exposed"),
                "total_buildings_exposed": transformed_data.get("buildings_exposed"),
                "impact_metadata": transformed_data.get("impact_metadata"),
                "item_eligible": is_item_eligible,
            },
        )

        action = "Created" if created else "Updated"
        logger.info(f"{action} Event for correlation_id={correlation_id}")

        return load_obj
