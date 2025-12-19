import logging
from abc import ABC
from datetime import datetime, timedelta, timezone
from typing import Dict, Generator, List, Optional

import httpx
from django.db import transaction

from alert_system.helpers import build_stac_search
from alert_system.models import Connector, ExtractionItem, LoadItem

from .loader import BaseLoaderClass
from .transform import BaseTransformerClass

logger = logging.getLogger(__name__)


class BaseExtractionClass(ABC):
    """
    Base class for extracting STAC data from various disaster monitoring sources.
    Subclasses MUST define:
      - event_collection_type
      - transformer_class
      - loader_class
    Subclasses MAY define:
      - hazard_collection_type
      - impact_collection_type
      - filter_* dictionaries
    """

    event_collection_type: str
    hazard_collection_type: str | None
    impact_collection_type: str | None
    filter_event: Optional[Dict] = None
    filter_hazard: Optional[Dict] = None
    filter_impact: Optional[Dict] = None
    transformer_class: type[BaseTransformerClass]
    loader_class: type[BaseLoaderClass]

    def __init__(self, connector: Connector):
        self.connector = connector
        self.base_url = connector.source_url.rstrip("/")
        self._validate_required_attributes()

    def _validate_required_attributes(self):
        missing_attr = []
        if not getattr(self, "event_collection_type", None):
            missing_attr.append("event_collection_type")
        if not getattr(self, "transformer_class", None):
            missing_attr.append("transformer_class")
        if not getattr(self, "loader_class", None):
            missing_attr.append("loader_class")

        if missing_attr:
            raise NotImplementedError(f"{self.__class__.__name__} must define: {', '.join(missing_attr)}")

    @staticmethod
    def fetch_stac_data(url: str, filters: Optional[Dict] = None) -> Generator[Dict, None, None]:
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

    def _build_base_defaults(self, feature: Dict, run_id: str, collection_type: ExtractionItem.CollectionType) -> Dict:
        """Build common default fields for all STAC items."""
        return {
            "correlation_id": self._get_correlation_id(feature),
            "resp_data": feature,
            "connector": self.connector,
            "extraction_run_id": run_id,
            "collection": collection_type,
        }

    def get_datetime_filter(self) -> str:
        """
        Generate datetime filter string for STAC queries.

        Returns:
            ISO 8601 datetime range string
        """

        now = datetime.now(timezone.utc)
        last_run = self.connector.last_success_run

        start_time = last_run if last_run else (now - timedelta(days=10))  # NOTE: Arbitrary value for failure case.
        return f"{start_time.isoformat()}/{now.isoformat()}"

    def _save_stac_item(self, stac_id: str, defaults: Dict) -> Optional[ExtractionItem]:
        """
        Generic method to save or update STAC items.

        """
        try:
            obj, created = ExtractionItem.objects.update_or_create(stac_id=stac_id, defaults=defaults)
            action = "Created" if created else "Updated"
            logger.info(f"{action} {stac_id}")
            return obj
        except Exception as e:
            logger.warning(f"Failed to save {stac_id}: {e}", exc_info=True)
            return None

    # Extraction methods
    def _extract_impact_items(self, stac_obj: ExtractionItem, run_id: str) -> List[ExtractionItem]:
        """Process impact items related to a STAC event object."""
        if not self.impact_collection_type:
            logger.info("No impact endpoint defined.")
            return []
        impact_objects: List[ExtractionItem] = []
        try:
            impact_features = self.fetch_stac_data(
                self.base_url,
                build_stac_search(
                    collections=self.impact_collection_type,
                    correlation_id=stac_obj.correlation_id,
                ),
            )
        except Exception as e:
            logger.warning(f"Failed to fetch impacts for event {stac_obj.stac_id}: {e}")
            return []

        for feature in impact_features:
            impact_id = feature.get("id", None)
            if not impact_id:
                logger.warning(f"Impact feature missing 'id': {feature}")
                continue

            defaults = self._build_base_defaults(feature, run_id=run_id, collection_type=ExtractionItem.CollectionType.IMPACT)
            impact_object = self._save_stac_item(impact_id, defaults)
            if impact_object:
                impact_objects.append(impact_object)
        return impact_objects

    def _extract_hazard_items(self, stac_obj: ExtractionItem, run_id: str) -> ExtractionItem | None:
        """Process hazard items related to a STAC event object."""
        if not self.hazard_collection_type:
            logger.info("Source does not contain hazard.")
            return

        try:
            hazard_features = self.fetch_stac_data(
                self.base_url,
                build_stac_search(
                    collections=self.hazard_collection_type,
                    correlation_id=stac_obj.correlation_id,
                ),
            )
        except Exception as e:
            logger.warning(f"Failed to fetch hazards for event {stac_obj.stac_id}: {e}")
            raise

        hazard_feature = next(hazard_features, None)
        if not hazard_feature:
            logger.info("No hazard features found — skipping hazard processing.")
            return

        hazard_id = hazard_feature.get("id", None)
        if not hazard_id:
            logger.warning(f"No hazard id found for {hazard_feature}")
            return

        defaults = self._build_base_defaults(hazard_feature, run_id=run_id, collection_type=ExtractionItem.CollectionType.HAZARD)
        hazard_obj = self._save_stac_item(hazard_id, defaults)
        return hazard_obj

    def process_event_items(self, extraction_run_id: str, correlation_id: str | None = None, is_past_event: bool = False) -> None:
        """Process all event items from the connector source."""
        filters = []
        if self.filter_event:
            hazard_codes = self.filter_event.get("hazard_codes", [])
            hazard_cql = " OR ".join(f"a_contains(monty:hazard_codes, '{hc}')" for hc in hazard_codes)
            filters.append(f"({hazard_cql})")

        loader = self.loader_class()

        try:
            event_items = self.fetch_stac_data(
                self.base_url,
                build_stac_search(
                    collections=self.event_collection_type,
                    additional_filters=filters,
                    correlation_id=correlation_id,
                    datetime_range=None if is_past_event else self.get_datetime_filter(),
                ),
            )
        except Exception as e:
            logger.error(f"Failed to fetch events: {e}")
            raise

        for feature in event_items:
            event_id = feature.get("id", None)
            if not event_id:
                logger.warning(f"No event id found for {feature}")
                continue
            defaults = self._build_base_defaults(
                feature=feature, run_id=extraction_run_id, collection_type=ExtractionItem.CollectionType.EVENT
            )

            try:
                with transaction.atomic():
                    event_obj = self._save_stac_item(event_id, defaults)
                    if not event_obj:
                        logger.info("No event item extracted")
                        continue
                    hazard_obj = self._extract_hazard_items(event_obj, run_id=extraction_run_id)
                    impact_obj = self._extract_impact_items(event_obj, run_id=extraction_run_id)

                    transformer = self.transformer_class(
                        event_obj=event_obj,
                        hazard_obj=hazard_obj,
                        impact_obj=impact_obj,
                    )
                    transformed_data = transformer.transform_stac_item()

                    loader.load(transformed_data, self.connector, is_past_event=is_past_event, run_id=extraction_run_id)

                    logger.info(f"Successfully processed event {event_id}")

            except Exception as e:
                logger.error(f"Failed to process event {event_id}: {e}", exc_info=True)
                raise

    def _construct_filter_for_past_events(self, impact_metadata: list[dict]) -> str:
        filters = []

        for detail in impact_metadata:
            category = detail.get("category")
            type_ = detail.get("type")
            value = detail.get("value")

            if category and type_ and value is not None:
                filters.append(
                    f"monty:impact_detail.category = '{category}' AND "
                    f"monty:impact_detail.type = '{type_}' AND "
                    f"monty:impact_detail.value >= {value}"
                )

        return " OR ".join(f"({f})" for f in filters) if filters else ""

    def fetch_past_events(self, load_obj):
        if not self.impact_collection_type:
            logger.warning(f"Impact does not exist for event {load_obj}")
            return
        start_time = datetime.now(timezone.utc) - timedelta(weeks=16)  # NOTE: Arbitrary value for lookback.
        filters = [self._construct_filter_for_past_events(load_obj.impact_metadata)]
        impact_data = self.fetch_stac_data(
            self.base_url,
            build_stac_search(
                collections=self.impact_collection_type,
                additional_filters=filters,
                datetime_range=f"{start_time.isoformat()}/{datetime.now(timezone.utc).isoformat()}",
            ),
        )
        load_obj_corr_id = load_obj.correlation_id
        related_ids = []
        logger.info(f"Fetching past event for event={load_obj.id}")
        corr_ids = set()
        for feature in impact_data:
            corr_id = self._get_correlation_id(feature)
            if corr_id and corr_id != load_obj_corr_id:
                corr_ids.add(corr_id)

        if not corr_ids:
            return

        existing_items = LoadItem.objects.filter(correlation_id__in=corr_ids)
        existing_map = {item.correlation_id: item for item in existing_items}

        for corr_id in corr_ids:
            item = existing_map.get(corr_id)
            if item:
                related_ids.append(item.id)
                item.related_montandon_events.add(load_obj.id)
            else:
                self.run(extraction_run_id=load_obj.extraction_run_id, correlation_id=corr_id, is_past_event=True)
                new_item = LoadItem.objects.filter(correlation_id=corr_id).first()
                if new_item:
                    related_ids.append(new_item.id)
                    new_item.related_montandon_events.add(load_obj.id)

        if related_ids:
            load_obj.related_montandon_events.set(related_ids)

    def run(self, extraction_run_id: str, correlation_id: str | None = None, is_past_event: bool = False) -> None:
        """Main entry point for running the connector."""
        logger.info(f"Starting connector run for {self.connector}")

        try:
            self.process_event_items(extraction_run_id, correlation_id, is_past_event)
            logger.info("Connector run completed successfully")
        except Exception as e:
            logger.error(f"Connector run failed: {e}", exc_info=True)
            raise
