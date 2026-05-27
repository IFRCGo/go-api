import logging
from typing import Optional

from alert_system.etl.base.transform import BaseTransformerClass
from alert_system.models import ImpactDetailsEnum

logger = logging.getLogger(__name__)


class GdacsCycloneTransformer(BaseTransformerClass):
    """
    Transformer for GDACS STAC impacts.
    Extracts and normalizes impact fields, computes derived values, and stores metadata.
    """

    def compute_people_exposed(self, metadata_list) -> Optional[int]:
        for data in metadata_list:
            if data["category"] == ImpactDetailsEnum.Category.PEOPLE and data["type"] == ImpactDetailsEnum.Type.AFFECTED_TOTAL:
                return data["value"]
        return None

    def compute_buildings_exposed(self, metadata_list) -> Optional[int]:
        """
        Compute the 'buildings_exposed' field.
        """
        for data in metadata_list:
            if data["category"] == ImpactDetailsEnum.Category.BUILDINGS and data["type"] == ImpactDetailsEnum.Type.AFFECTED_TOTAL:
                return data["value"]
        return None

    def process_impact(self, impact_items) -> BaseTransformerClass.ImpactType:
        latest_episode = -1
        metadata = []

        for item in impact_items:
            properties = item.resp_data.get("properties", {})
            impact_detail = properties.get("monty:impact_detail", {})

            if properties.get("forecasted"):
                continue

            episode_number = properties.get("monty:episode_number")

            if episode_number is None:
                logger.info("No episode number found.")
                continue

            category = impact_detail.get("category")
            type_ = impact_detail.get("type")

            if not (category and type_):
                logger.info("Skipping impact item: missing category or type ")
                continue

            if episode_number > latest_episode:
                latest_episode = episode_number

                metadata = [
                    {
                        "category": category,
                        "type": type_,
                        "value": impact_detail.get("value"),
                        "unit": impact_detail.get("unit", ""),
                        "estimate_type": impact_detail.get("estimate_type", ""),
                    }
                ]

        return {
            "people_exposed": self.compute_people_exposed(metadata),
            "buildings_exposed": self.compute_buildings_exposed(metadata),
            "impact_metadata": metadata,
        }

    def process_hazard(self, hazard_item) -> BaseTransformerClass.HazardType:
        if not hazard_item:
            return {
                "severity_unit": "",
                "severity_label": "",
                "severity_value": None,
            }

        properties = hazard_item.resp_data.get("properties", {})
        detail = properties.get("monty:hazard_detail", {})

        return {
            "severity_unit": detail.get("severity_unit", ""),
            "severity_label": detail.get("severity_label", ""),
            "severity_value": detail.get("severity_value"),
        }

    def process_event(self, event_item) -> BaseTransformerClass.EventType:
        properties = event_item.resp_data.get("properties", {})
        urls = event_item.resp_data.get("links")
        return {
            "title": properties.get("title", ""),
            "description": properties.get("description", ""),
            "country": properties.get("monty:country_codes", ""),
            "start_datetime": properties.get("start_datetime"),
            "end_datetime": properties.get("end_datetime"),
            "episode_number": properties.get("monty:episode_number"),
            "event_url": next(item["href"] for item in urls if item["rel"] == "self"),
        }
