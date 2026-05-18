import logging
from abc import ABC, abstractmethod
from typing import Dict

from alert_system.models import Connector, LoadItem

logger = logging.getLogger(__name__)


class BaseLoaderClass(ABC):
    """Loads transformed data into DisasterEvent table."""

    @abstractmethod
    def filter_eligible_items(self, load_obj):
        raise NotImplementedError()

    def extract_event_id_without_episode(self, event_id: str) -> str:
        parts = event_id.split("-")
        return "-".join(parts[0 : len(parts) - 1])

    def load(self, transformed_data: Dict, connector: Connector, run_id: str, is_past_event: bool = False) -> LoadItem:
        """
        Save aggregated event.

        Args:
            transformed_data: Output from transformer.transform()
            connector: The connector this data came from

        Returns:
            Created LoadItem object
        """
        event_id = transformed_data["event_id"]
        parent_event_id = self.extract_event_id_without_episode(event_id)
        is_item_eligible = self.filter_eligible_items(transformed_data)

        load_obj, created = LoadItem.objects.update_or_create(
            event_id=event_id,
            defaults={
                "connector": connector,
                "parent_event_id": parent_event_id,
                "event_title": transformed_data.get("title"),
                "event_description": transformed_data.get("description"),
                "country_codes": transformed_data.get("country"),
                "severity_value": transformed_data.get("severity_value"),
                "severity_label": transformed_data.get("severity_label"),
                "severity_unit": transformed_data.get("severity_unit"),
                "total_people_exposed": transformed_data.get("people_exposed"),
                "total_buildings_exposed": transformed_data.get("buildings_exposed"),
                "impact_metadata": transformed_data.get("impact_metadata"),
                "start_datetime": transformed_data.get("start_datetime"),
                "end_datetime": transformed_data.get("end_datetime"),
                "item_eligible": is_item_eligible,
                "is_past_event": is_past_event,
                "extraction_run_id": run_id,
                "episode_number": transformed_data.get("episode_number"),
                "event_url": transformed_data.get("event_url"),
            },
        )

        action = "Created" if created else "Updated"
        logger.info(f"{action} Event for {event_id=}")

        return load_obj
