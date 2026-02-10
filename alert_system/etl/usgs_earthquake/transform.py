import logging
from typing import Optional

from alert_system.etl.base.transform import BaseTransformerClass
from alert_system.models import ImpactDetailsEnum

logger = logging.getLogger(__name__)


class USGSTransformer(BaseTransformerClass):
    """
    Transformer for USGS STAC impacts.
    Extracts and normalizes impact fields, computes derived values, and stores metadata.
    """

    # NOTE: This logic might change in future
    def compute_people_exposed(self, metadata_list) -> Optional[int]:
        for data in metadata_list:
            if data["category"] == ImpactDetailsEnum.Category.PEOPLE and data["type"] in [
                ImpactDetailsEnum.Type.DEATH,
                ImpactDetailsEnum.Type.POTENTIALLY_AFFECTED,
            ]:
                return data["value"]
        return None

    # NOTE: This logic might change in future
    def compute_buildings_exposed(self, metadata_list) -> Optional[int]:
        """
        Compute the 'buildings_exposed' field.
        """
        for data in metadata_list:
            if data["category"] == ImpactDetailsEnum.Category.BUILDINGS and data["type"] == ImpactDetailsEnum.Type.LOSS_COST:
                return data["value"]
        return None

    # NOTE: To be changed.
    def process_impact(self, impact_items) -> BaseTransformerClass.ImpactType:
        metadata = []
        values_metadata = {}
        for item in impact_items:
            properties = item.resp_data.get("properties", {})
            impact_detail = properties.get("monty:impact_detail", {})
            category = impact_detail.get("category")
            type_ = impact_detail.get("type")
            value = impact_detail.get("value")
            if category and type_:
                values_metadata = {
                    "category": category,
                    "type": type_,
                    "value": value,
                    "unit": impact_detail.get("unit", ""),
                    "estimate_type": impact_detail.get("estimate_type", ""),
                }
            metadata.append(values_metadata)
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
        return {
            "title": properties.get("title", ""),
            "description": properties.get("description", ""),
            "country": properties.get("monty:country_codes", ""),
            "start_datetime": properties.get("datetime"),
            "end_datetime": properties.get("end_datetime"),
        }
