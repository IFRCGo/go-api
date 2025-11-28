from abc import abstractmethod, ABC
import logging
from typing import TypedDict, Optional, List
from alert_system.models import ExtractionItem

logger = logging.getLogger(__name__)

class BaseTransformerClass(ABC):

    class ImpactType(TypedDict):
        people_exposed: int
        buildings_exposed: int
        impact_metadata: dict[str, dict]

    class HazardType(TypedDict):
        severity_unit: str
        severity_label: Optional[str]
        severity_value: int

    class EventType(TypedDict):
        title: str
        description: str
        country: str

    def __init__(self, event_obj: ExtractionItem, hazard_obj: Optional[ExtractionItem] = None, impact_obj: List[ExtractionItem] = []):
        self.event_obj = event_obj
        self.hazard_obj = hazard_obj
        self.impact_obj = impact_obj
        self.correlation_id = event_obj.correlation_id

    @abstractmethod
    def process_hazard(self, hazard_item: ExtractionItem | None) -> HazardType:
        pass

    @abstractmethod
    def process_impact(self, impact_items: List[ExtractionItem]) -> ImpactType:
        pass

    @abstractmethod
    def process_event(self, event_item: ExtractionItem) -> EventType:
        pass

    def transform_stac_item(self):
        """
        Transform STAC items for a given extraction object.

        Fetches event, hazard and impact items separately, processes them, 
        and returns processed data if available.
        """
        logger.info(f"Starting transformer for correlation_id={self.correlation_id}")
        # Process event, hazard and impact.

        event_result = self.process_event(self.event_obj)
        hazard_result = self.process_hazard(self.hazard_obj)
        impact_result = self.process_impact(self.impact_obj)

        return {
            'correlation_id': self.correlation_id,
            **event_result,
            **hazard_result,
            **impact_result,
        }

    

    