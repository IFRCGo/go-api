import logging
from abc import ABC
from datetime import timedelta
from typing import Dict, Generator, List, Optional, Type

import httpx
from django.db import transaction
from django.utils import timezone

from alert_system.helpers import build_stac_search
from alert_system.models import Connector, ExtractionItem, LoadItem

from .config import ExtractionConfig
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
    transformer_class: Type[BaseTransformerClass]
    loader_class: Type[BaseLoaderClass]

    hazard_collection_type: Optional[str] = None
    impact_collection_type: Optional[str] = None

    filter_event: Optional[Dict] = None
    filter_hazard: Optional[Dict] = None
    filter_impact: Optional[Dict] = None

    config: ExtractionConfig

    def __init__(self, connector: Connector):
        self.connector = connector
        self.base_url = connector.source_url.rstrip("/")
        self.load_config()
        self._validate_required_attributes()

    def load_config(self):
        for key, value in self.config.items():
            setattr(self, key, value)

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

        now = timezone.now()
        last_run = self.connector.last_success_run

        start_time = last_run if last_run else (now - timedelta(days=30))  # NOTE: Arbitrary value for failure case.
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
            logger.warning(f"Failed to fetch events: {e}")
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
                logger.warning(f"Failed to process event {event_id}: {e}", exc_info=True)
                raise

    def run(self, extraction_run_id: str, correlation_id: str | None = None, is_past_event: bool = False) -> None:
        """Main entry point for running the connector."""
        try:
            self.process_event_items(extraction_run_id, correlation_id, is_past_event)
        except Exception as e:
            logger.warning(f"Connector run failed: {e}", exc_info=True)
            raise


class PastEventExtractionClass:
    LOOKBACK_WEEKS = 520

    def __init__(self, extractor: BaseExtractionClass):
        self.extractor = extractor
        self.base_url = extractor.base_url

    def _impact_filter(self, impact_metadata: list[dict]) -> str:
        filters = []

        for data in impact_metadata or []:
            if data.get("category") and data.get("type") and data.get("value") is not None:
                filters.append(
                    f"monty:impact_detail.category = '{data['category']}' AND "
                    f"monty:impact_detail.type = '{data['type']}' AND "
                    f"monty:impact_detail.value >= {data['value']}"
                )

        return " OR ".join(f"({filter})" for filter in filters)

    def _country_filter(self, country_codes) -> list[str]:
        filters = []
        if country_codes:
            country_cql = " OR ".join(f"a_contains(monty:country_codes, '{code}')" for code in country_codes)
            filters.append(f"({country_cql})")
        return filters

    def _hazard_filter(self, unit: str, value: int) -> str:
        return f"monty:hazard_detail.severity_unit = '{unit}' AND " f"monty:hazard_detail.severity_value >= {value}"

    def _collect_corr_ids(self, features, exclude: str) -> set[str]:
        corr_ids = set()
        for feature in features or []:
            corr_id = self.extractor._get_correlation_id(feature)
            if corr_id and corr_id != exclude:
                corr_ids.add(corr_id)
        return corr_ids

    def find_related_corr_ids(self, load_obj: LoadItem) -> set[str]:
        start = timezone.now() - timedelta(weeks=self.LOOKBACK_WEEKS)
        end = timezone.now()

        corr_ids = set()

        if self.extractor.impact_collection_type:
            impact_filter = self._impact_filter(load_obj.impact_metadata)
            country_filters = self._country_filter(load_obj.country_codes)

            additional_filters = []

            if impact_filter:
                additional_filters.append(impact_filter)

            additional_filters.extend(country_filters)

            features = self.extractor.fetch_stac_data(
                self.base_url,
                build_stac_search(
                    collections=self.extractor.impact_collection_type,
                    additional_filters=additional_filters,
                    datetime_range=f"{start.isoformat()}/{end.isoformat()}",
                ),
            )

            corr_ids |= self._collect_corr_ids(features, load_obj.correlation_id)

        # NOTE: Returns too many correlation_ids.
        # if self.extractor.hazard_collection_type:
        #     hazard_filter = self._hazard_filter(
        #         load_obj.severity_unit,
        #         load_obj.severity_value,
        #     )
        #     features = self.extractor.fetch_stac_data(
        #         self.base_url,
        #         build_stac_search(
        #             collections=self.extractor.hazard_collection_type,
        #             additional_filters=[hazard_filter],
        #             datetime_range=f"{start.isoformat()}/{end.isoformat()}",
        #         ),
        #     )
        #     corr_ids |= self._collect_corr_ids(features, load_obj.correlation_id)

        return corr_ids

    def extract_past_events(self, load_obj: LoadItem) -> None:
        corr_ids = self.find_related_corr_ids(load_obj)

        if not corr_ids:
            return

        existing_items = LoadItem.objects.filter(correlation_id__in=corr_ids)
        existing_map = {i.correlation_id: i for i in existing_items}

        related_ids = []

        for corr_id in corr_ids:
            item = existing_map.get(corr_id)

            if not item:
                self.extractor.run(
                    extraction_run_id=load_obj.extraction_run_id,
                    correlation_id=corr_id,
                    is_past_event=True,
                )
                item = LoadItem.objects.filter(correlation_id=corr_id).first()

            if item:
                related_ids.append(item.id)
                item.related_montandon_events.add(load_obj.id)

        if related_ids:
            load_obj.related_montandon_events.set(related_ids)
