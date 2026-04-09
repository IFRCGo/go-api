import logging
from typing import Optional

from alert_system.etl.base.transform import BaseTransformerClass
from alert_system.models import ImpactDetailsEnum

logger = logging.getLogger(__name__)


class GdacsTransformer(BaseTransformerClass):
    """
    Transformer for GDACS STAC impacts.
    Extracts and normalizes impact fields, computes derived values, and stores metadata.
    """

    # NOTE: This logic might change in future. Currently only creating a function for future use.
    def compute_people_exposed(self, metadata_list) -> Optional[int]:
        for data in metadata_list:
            if data["category"] == ImpactDetailsEnum.Category.PEOPLE and data["type"] == ImpactDetailsEnum.Type.AFFECTED_TOTAL:
                return data["value"]
        return None

    # NOTE: This logic might change in future. Currently only creating a function for future use.
    def compute_buildings_exposed(self, metadata_list) -> Optional[int]:
        """
        Compute the 'buildings_exposed' field.
        """
        for data in metadata_list:
            if data["category"] == ImpactDetailsEnum.Category.BUILDINGS and data["type"] == ImpactDetailsEnum.Type.AFFECTED_TOTAL:
                return data["value"]
        return None

    def process_impact(self, impact_items) -> BaseTransformerClass.ImpactType:
        meta_hash_map = {}

        for item in impact_items:
            properties = item.resp_data.get("properties", {})
            detail = properties.get("monty:impact_detail", {})

            category = detail.get("category")
            type_ = detail.get("type")
            value = detail.get("value")
            if value in (None, -1):
                value = 0
            key = (category, type_)
            meta_hash_map[key] = meta_hash_map.get(key, 0) + value

        metadata = [
            {
                "category": category,
                "type": type_,
                "value": value,
            }
            for (category, type_), value in meta_hash_map.items()
            if category == ImpactDetailsEnum.Category.PEOPLE
        ]

        return {
            "people_exposed": meta_hash_map.get(
                (ImpactDetailsEnum.Category.PEOPLE, ImpactDetailsEnum.Type.AFFECTED_TOTAL)  # Taking only people exposed.
            ),
            "buildings_exposed": meta_hash_map.get((ImpactDetailsEnum.Category.BUILDINGS, ImpactDetailsEnum.Type.DAMAGED)),
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
        return {
            "title": properties.get("title", ""),
            "description": properties.get("description", ""),
            "country": properties.get("monty:country_codes", ""),
            "start_datetime": properties.get("start_datetime"),
            "end_datetime": properties.get("end_datetime"),
        }
