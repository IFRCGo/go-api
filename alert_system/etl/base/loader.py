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

    def extract_parent_guid(self, guid: str) -> str:
        parts = guid.split("-")

        BASE_PART_COUNT = 7

        if len(parts) > BASE_PART_COUNT:
            return "-".join(parts[:BASE_PART_COUNT])

        return guid

    def load(self, transformed_data: Dict, connector: Connector, run_id: str, is_past_event: bool = False) -> LoadItem:
        """
        Save aggregated event.

        Args:
            transformed_data: Output from transformer.transform()
            connector: The connector this data came from

        Returns:
            Created LoadItem object
        """
        guid = transformed_data["guid"]
        parent_guid = self.extract_parent_guid(guid)
        is_item_eligible = self.filter_eligible_items(transformed_data)

        load_obj, created = LoadItem.objects.update_or_create(
            guid=guid,
            defaults={
                "connector": connector,
                "parent_guid": parent_guid,
                "correlation_id": transformed_data.get("correlation_id"),
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
            },
        )

        action = "Created" if created else "Updated"
        logger.info(f"{action} Event for {guid=}")

        return load_obj
