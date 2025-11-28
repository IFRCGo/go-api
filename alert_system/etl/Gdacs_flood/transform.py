import logging
from typing import Dict, Tuple

from alert_system.etl.base.transform import BaseTransformerClass

logger = logging.getLogger(__name__)


class GdacsTransformer(BaseTransformerClass):
    """
    Transformer for GDACS STAC impacts.
    Extracts and normalizes impact fields, computes derived values, and stores metadata.
    """

    # Mapping of (category, type) → flattened key
    IMPACT_MAP: Dict[Tuple[str, str], str] = {
        ("people", "potentially_affected"): "people.potentially_affected",
        ("people", "death"): "people.death",
        ("people", "affected_total"): "people.affected_total",
        ("people", "affected_direct"): "people.affected_direct",
        ("people", "affected_indirect"): "people.affected_indirect",
        ("people", "highest_risk"): "people.highest_risk",
        ("buildings", "destroyed"): "buildings.destroyed",
    }

    # NOTE: This logic might change in future
    def compute_people_exposed(self, impacts: dict) -> int:
        value = next(
            (
                impacts.get(key)
                for key in ["people.affected_total", "people.potentially_affected", "people.affected_direct"]
                if impacts.get(key)
            ),
            0,
        )
        if not isinstance(value, int):
            logger.warning(f"people_exposed value is not int: {value}")
            return 0
        return value

    # NOTE: This logic might change in future
    def compute_buildings_exposed(self, impacts: dict) -> int:
        """
        Compute the 'buildings_exposed' field.
        """
        return impacts.get("buildings.destroyed") or 0

    def process_impact(self, impact_items) -> BaseTransformerClass.ImpactType:
        raw_impacts, metadata = {}, {}
        for item in impact_items:
            properties = item.resp_data.get("properties", {})
            impact_detail = properties.get("monty:impact_detail", {})
            category = impact_detail.get("category")
            type_ = impact_detail.get("type")
            value = impact_detail.get("value")
            if category and type_:
                field = self.IMPACT_MAP.get((category, type_)) or f"{category}.{type_}"
                raw_impacts[field] = value
                metadata[field] = impact_detail

        return {
            "people_exposed": self.compute_people_exposed(raw_impacts),
            "buildings_exposed": self.compute_buildings_exposed(raw_impacts),
            "impact_metadata": metadata,
        }

    def process_hazard(self, hazard_item) -> BaseTransformerClass.HazardType:
        if not hazard_item:
            return {
                "severity_unit": "",
                "severity_label": "",
                "severity_value": 0,
            }

        properties = hazard_item.resp_data.get("properties", {})
        detail = properties.get("monty:hazard_detail", {})

        return {
            "severity_unit": detail.get("severity_unit", ""),
            "severity_label": detail.get("severity_label", ""),
            "severity_value": detail.get("severity_value", 0),
        }

    def process_event(self, event_item) -> BaseTransformerClass.EventType:
        properties = event_item.resp_data.get("properties", {})
        return {
            "title": properties.get("title", ""),
            "description": properties.get("description", ""),
            "country": properties.get("monty:country_codes", ""),
        }
