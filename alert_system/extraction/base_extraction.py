import logging
from datetime import datetime, timedelta, timezone
from token import OP
from typing import Dict, Generator, Optional

import httpx
from django.db import transaction

from alert_system.models import Connector, StacItems

logger = logging.getLogger(__name__)


class BaseExtractionClass:
    """Base class for extracting STAC data from various disaster monitoring sources."""

    event_endpoint: str
    hazard_endpoint: Optional[str] = None
    impact_endpoint: Optional[str] = None

    def __init__(self, connector: Connector):
        if not self.event_endpoint:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define event_endpoint, "
            )
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

    def build_impact_defaults(self, feature: Dict) -> Dict:
        """Build default values for ImpactItems creation/update."""
        defaults = self._build_base_defaults(feature)

        impact = feature.get("properties", {}).get("monty:impact_detail", {})
        defaults.update(
            {
                "collection": StacItems.CollectionType.IMPACT,
                "category": impact.get("category"),
                "type": impact.get("type"),
                "value": impact.get("value"),
            }
        )

        return defaults

    def build_hazard_defaults(self, feature: Dict) -> Dict:
        """Build default values for HazardItems creation/update."""
        defaults = self._build_base_defaults(feature)

        detail = feature.get("properties", {}).get("monty:hazard_detail", {})
        defaults.update(
            {
                "collection": StacItems.CollectionType.HAZARD,
                "cluster": detail.get("cluster"),
                "estimate_type": detail.get("estimate_type"),
                "severity_unit": detail.get("severity_unit"),
                "severity_label": detail.get("severity_label"),
                "severity_value": detail.get("severity_value"),
            }
        )

        return defaults

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

    def _save_stac_item(self, stac_id: str, defaults: Dict, item_type: str) -> Optional[StacItems]:
        """
        Generic method to save or update STAC items.

        """
        try:
            obj, created = StacItems.objects.update_or_create(stac_id=stac_id, defaults=defaults)
            action = "Created" if created else "Updated"
            logger.info(f"{action} {item_type} {stac_id}")
            return obj
        except Exception as e:
            logger.error(f"Failed to save {item_type} {stac_id}: {e}", exc_info=True)
            return None

    def process_impact_items(self, stac_obj: StacItems) -> None:
        """Process impact items related to a STAC event object."""
        try:
            impact_features = self._fetch_items(self.impact_endpoint, "filter_impact", stac_obj.correlation_id)
        except Exception as e:
            logger.error(f"Failed to fetch impacts for event {stac_obj.stac_id}: {e}")
            return

        for feature in impact_features:
            impact_id = feature.get("id", None)
            if not impact_id:
                logger.error(f"Impact feature missing 'id': {feature}")
                continue

            defaults = self.build_impact_defaults(feature)
            self._save_stac_item(impact_id, defaults, "impact")

    def process_hazard_items(self, stac_obj: StacItems) -> None:
        """Process hazard items related to a STAC event object."""
        if not self.hazard_endpoint:
            return
        try:
            hazard_features = self._fetch_items(self.hazard_endpoint,"filter_hazard", stac_obj.correlation_id)
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

        defaults = self.build_hazard_defaults(hazard_feature)
        self._save_stac_item(hazard_id, defaults, "hazard")

    def process_event_items(self) -> None:
        """Process all event items from the connector source."""
        event_url = f"{self.base_url}{self.event_endpoint}"
        event_filter = (self.connector.filter_event or {}).copy()
        event_filter["datetime"] = self.get_datetime_filter()

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
            defaults.update({"collection": StacItems.CollectionType.EVENT})

            try:
                with transaction.atomic():
                    event_obj = self._save_stac_item(event_id, defaults, "event")
                    if event_obj:
                        self.process_hazard_items(event_obj)
                        self.process_impact_items(event_obj)
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
