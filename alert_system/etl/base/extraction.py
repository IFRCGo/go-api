import abc
import logging
from abc import ABC
from datetime import datetime, timedelta, timezone
from typing import Dict, Generator, List, Optional

import httpx
from django.db import transaction

from alert_system.models import Connector, ExtractionItem

from .loader import BaseLoaderClass
from .transform import BaseTransformerClass

logger = logging.getLogger(__name__)


class BaseExtractionClass(ABC):
    """Base class for extracting STAC data from various disaster monitoring sources."""

    event_endpoint: str
    hazard_endpoint: str | None
    impact_endpoint: str | None
    filter_event: Optional[Dict] = {}
    filter_hazard: Optional[Dict] = {}
    filter_impact: Optional[Dict] = {}

    def __init__(self, connector: Connector):
        if not self.event_endpoint:
            raise NotImplementedError(f"{self.__class__.__name__} must define event_endpoint, ")
        self.connector = connector
        self.base_url = connector.source_url.rstrip("/")

    def fetch_stac_data(self, url: str, filters: Optional[Dict] = None) -> Generator[Dict, None, None]:
        """
        Fetch STAC data with pagination support.

        """
        current_url = url
        current_payload = filters.copy() if filters else None

        while current_url:
            response = httpx.get(current_url, params=current_payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            yield from data.get("features", [])

            # Find next page link
            current_url = next((link["href"] for link in data.get("links", []) if link.get("rel") == "next"), None)
            current_payload = None  # Only use params on first request

    @abc.abstractmethod
    def get_transformer_class(self) -> type[BaseTransformerClass]:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_loader_class(self) -> type[BaseLoaderClass]:
        raise NotImplementedError()

    def _get_correlation_id(self, feature: Dict) -> str:
        """Extract correlation ID from feature properties."""
        return feature.get("properties", {}).get("monty:corr_id")

    def _build_base_defaults(self, feature: Dict) -> Dict:
        """Build common default fields for all STAC items."""
        return {
            "correlation_id": self._get_correlation_id(feature),
            "resp_data": feature,
            "connector": self.connector,
        }

    def get_datetime_filter(self) -> str:
        """
        Generate datetime filter string for STAC queries.

        Returns:
            ISO 8601 datetime range string
        """
        now = datetime.now(timezone.utc)
        last_run = self.connector.last_success_run

        start_time = last_run if last_run else (now - timedelta(days=15))
        return f"{start_time.isoformat()}/{now.isoformat()}"

    def _build_filter(self, base_filter: Optional[Dict], correlation_id: str) -> Dict:
        """Build filter dict with correlation ID."""
        filters = base_filter.copy() if base_filter else {}
        filters["filter"] = f"monty:corr_id = '{correlation_id}'"
        return filters

    def _fetch_items(self, endpoint: str | None, filter_attr: str, correlation_id: str) -> Generator[Dict, None, None]:
        """
        Generic method to fetch items with correlation ID filtering.

        """
        url = f"{self.base_url}{endpoint}"
        base_filter = getattr(self.connector, filter_attr, None)
        filters = self._build_filter(base_filter, correlation_id)

        return self.fetch_stac_data(url, filters)

    def _save_stac_item(self, stac_id: str, defaults: Dict, item_type: str) -> Optional[ExtractionItem]:
        """
        Generic method to save or update STAC items.

        """
        try:
            obj, created = ExtractionItem.objects.update_or_create(stac_id=stac_id, defaults=defaults)
            action = "Created" if created else "Updated"
            logger.info(f"{action} {item_type} {stac_id}")
            return obj
        except Exception as e:
            logger.error(f"Failed to save {item_type} {stac_id}: {e}", exc_info=True)
            return None

    def _extract_impact_items(self, stac_obj: ExtractionItem) -> List[ExtractionItem]:
        """Process impact items related to a STAC event object."""
        if not self.impact_endpoint:
            logger.info("No impact endpoint defined.")
            return []
        impact_objects: List[ExtractionItem] = []
        try:
            impact_features = self._fetch_items(self.impact_endpoint, "filter_impact", stac_obj.correlation_id)
        except Exception as e:
            logger.error(f"Failed to fetch impacts for event {stac_obj.stac_id}: {e}")
            return []

        for feature in impact_features:
            impact_id = feature.get("id", None)
            if not impact_id:
                logger.error(f"Impact feature missing 'id': {feature}")
                continue

            defaults = self._build_base_defaults(feature)
            defaults.update({"collection": ExtractionItem.CollectionType.IMPACT})
            impact_object = self._save_stac_item(impact_id, defaults, "impact")
            if impact_object:
                impact_objects.append(impact_object)
        return impact_objects

    def _extract_hazard_items(self, stac_obj: ExtractionItem) -> ExtractionItem | None:
        """Process hazard items related to a STAC event object."""
        if not self.hazard_endpoint:
            logger.info("No hazard endpoint defined")
            return
        try:
            hazard_features = self._fetch_items(self.hazard_endpoint, "filter_hazard", stac_obj.correlation_id)
        except Exception as e:
            logger.error(f"Failed to fetch hazards for event {stac_obj.stac_id}: {e}")
            raise

        hazard_feature = next(hazard_features, None)
        if not hazard_feature:
            logger.info("No hazard features found — skipping hazard processing.")
            return

        hazard_id = hazard_feature.get("id", None)
        if not hazard_id:
            logger.error(f"No hazard id found for {hazard_feature}")
            return

        defaults = self._build_base_defaults(hazard_feature)
        defaults.update({"collection": ExtractionItem.CollectionType.HAZARD})
        hazard_obj = self._save_stac_item(hazard_id, defaults, "hazard")
        return hazard_obj

    def process_event_items(self) -> None:
        """Process all event items from the connector source."""
        event_url = f"{self.base_url}{self.event_endpoint}"
        event_filter = (self.filter_event or {}).copy()
        event_filter["datetime"] = self.get_datetime_filter()

        transformer_class = self.get_transformer_class()
        loader_class = self.get_loader_class()
        loader = loader_class()

        try:
            event_items = self.fetch_stac_data(event_url, event_filter)
        except Exception as e:
            logger.error(f"Failed to fetch events: {e}")
            raise

        for feature in event_items:
            event_id = feature.get("id", None)
            if not event_id:
                logger.error(f"No event id found for {feature}")
                continue
            defaults = self._build_base_defaults(feature=feature)
            defaults.update({"collection": ExtractionItem.CollectionType.EVENT})

            try:
                with transaction.atomic():
                    event_obj = self._save_stac_item(event_id, defaults, "event")
                    if not event_obj:
                        logger.info("No event item extracted")
                        continue
                    hazard_obj = self._extract_hazard_items(event_obj)
                    impact_obj = self._extract_impact_items(event_obj)

                    transformer = transformer_class(
                        event_obj=event_obj,
                        hazard_obj=hazard_obj,
                        impact_obj=impact_obj,
                    )
                    transformed_data = transformer.transform_stac_item()

                loader.load(transformed_data, self.connector)

                logger.info(f"Successfully processed event {event_id}")

            except Exception as e:
                logger.error(f"Failed to process event {event_id}: {e}", exc_info=True)
                raise

    def run(self) -> None:
        """Main entry point for running the connector."""
        logger.info(f"Starting connector run for {self.connector}")

        try:
            self.process_event_items()
            logger.info("Connector run completed successfully")
        except Exception as e:
            logger.error(f"Connector run failed: {e}", exc_info=True)
            raise
