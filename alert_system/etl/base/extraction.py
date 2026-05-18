import logging
import math
from abc import ABC
from datetime import timedelta
from typing import Dict, List, Optional, Type

from django.db import transaction
from django.utils import timezone

from alert_system.helpers import (
    build_stac_search,
    fetch_paginated_stac_data,
    fetch_stac_data,
)
from alert_system.models import Connector, ExtractionItem, ImpactDetailsEnum, LoadItem

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

    def _build_base_defaults(self, item_dict: Dict, run_id: str, collection_type: ExtractionItem.CollectionType) -> Dict:
        """Build common default fields for all STAC items."""
        return {
            "resp_data": item_dict,
            "connector": self.connector,
            "extraction_run_id": run_id,
            "collection": collection_type,
        }

    def get_start_datetime(self) -> str:
        """
        Generate datetime filter string for STAC queries.

        Returns:
            ISO 8601 datetime range string
        """

        now = timezone.now()

        start_datetime = self.connector.last_success_run or self.connector.polling_start_datetime or (now - timedelta(days=1))
        return f"{start_datetime.isoformat()}"

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

    def _extract_related_url(self, links, collection_type) -> list[str]:
        return [link["href"] for link in links if collection_type in link.get("roles", [])]

    # Extraction methods
    def _extract_impact_items(self, stac_obj: ExtractionItem, run_id: str) -> List[ExtractionItem]:
        """Process impact items related to a STAC event object."""
        if not self.impact_collection_type:
            logger.info("No impact endpoint defined.")
            return []
        impact_objects: List[ExtractionItem] = []
        links = stac_obj.resp_data["links"]
        impact_urls = self._extract_related_url(links=links, collection_type=ExtractionItem.CollectionType.IMPACT)

        for impact_url in impact_urls:
            try:
                impact_item = fetch_stac_data(
                    impact_url,
                )
            except Exception as e:
                logger.warning(f"Failed to fetch impacts for event {stac_obj.stac_id}: {e}")
                return []

            if not impact_item:
                logger.info("No impact features found — skipping impact processing.")
                continue

            impact_id = impact_item.get("id", None)
            if not impact_id:
                logger.warning(f"No impact id found for {impact_item}")
                continue

            defaults = self._build_base_defaults(impact_item, run_id=run_id, collection_type=ExtractionItem.CollectionType.IMPACT)
            impact_object = self._save_stac_item(impact_id, defaults)
            if impact_object:
                impact_objects.append(impact_object)

        return impact_objects

    def _extract_hazard_items(self, stac_obj: ExtractionItem, run_id: str) -> ExtractionItem | None:
        """Process hazard items related to a STAC event object."""
        if not self.hazard_collection_type:
            logger.info("Source does not contain hazard.")
            return
        links = stac_obj.resp_data["links"]
        hazard_url = self._extract_related_url(links=links, collection_type=ExtractionItem.CollectionType.HAZARD)
        if len(hazard_url) > 1:
            logger.info("Event item contains multiple hazards")
            return
        try:
            hazard_item = fetch_stac_data(
                hazard_url[0],
            )
        except Exception as e:
            logger.warning(f"Failed to fetch hazards for event {stac_obj.stac_id}: {e}")
            raise
        if not hazard_item:
            logger.info("No hazard features found — skipping hazard processing.")
            return

        hazard_id = hazard_item.get("id", None)
        if not hazard_id:
            logger.warning(f"No hazard id found for {hazard_item}")
            return

        defaults = self._build_base_defaults(hazard_item, run_id=run_id, collection_type=ExtractionItem.CollectionType.HAZARD)
        hazard_obj = self._save_stac_item(hazard_id, defaults)
        return hazard_obj

    # TODO: Add pydantic validators here.
    def process_event_item(self, event_item: Dict, extraction_run_id: str, is_past_event: bool):
        loader = self.loader_class()
        event_id = event_item.get("id", None)
        if not event_id:
            logger.warning(f"No event id found for {event_item}")
            return
        defaults = self._build_base_defaults(
            item_dict=event_item, run_id=extraction_run_id, collection_type=ExtractionItem.CollectionType.EVENT
        )

        try:
            with transaction.atomic():
                event_obj = self._save_stac_item(event_id, defaults)
                if not event_obj:
                    logger.info("No event item extracted")
                    return
                hazard_obj = self._extract_hazard_items(event_obj, run_id=extraction_run_id)
                impact_obj = self._extract_impact_items(event_obj, run_id=extraction_run_id)

                transformer = self.transformer_class(
                    event_obj=event_obj,
                    hazard_obj=hazard_obj,
                    impact_obj=impact_obj,
                )
                transformed_data = transformer.transform_stac_item()

                load_obj = loader.load(transformed_data, self.connector, is_past_event=is_past_event, run_id=extraction_run_id)

                logger.info(f"Successfully processed event {event_id}")

                return load_obj

        except Exception as e:
            logger.warning(f"Failed to process event {event_id}: {e}", exc_info=True)
            raise

    def _extract_event_items(self, extraction_run_id: str, is_past_event: bool = False) -> None:
        """Process all event items from the connector source."""
        filters = []

        try:
            event_items = fetch_paginated_stac_data(
                self.base_url,
                build_stac_search(
                    collections=self.event_collection_type,
                    additional_filters=filters,
                    start_datetime=None if is_past_event else self.get_start_datetime(),
                    end_datetime=None if is_past_event else f"{timezone.now().isoformat()}",
                    hazard_codes=self.filter_event.get("hazard_codes") if self.filter_event else None,
                ),
            )
        except Exception as e:
            logger.warning(f"Failed to fetch events: {e}")
            raise

        first_event_item = next(event_items, None)
        if not first_event_item:
            msg = f"No event items found for extraction_run_id={extraction_run_id}"
            logger.warning(msg)
            raise ValueError(msg)

        for event_item in event_items:
            self.process_event_item(event_item=event_item, extraction_run_id=extraction_run_id, is_past_event=is_past_event)

    def process_event_from_url(self, event_url: str, extraction_run_id: str, is_past_event: bool) -> LoadItem | None:
        try:
            event_item = fetch_stac_data(event_url)
            if not event_item:
                return

            return self.process_event_item(event_item, extraction_run_id, is_past_event)

        except Exception as e:
            logger.warning(f"Failed to process event from URL {event_url}: {e}", exc_info=True)
            raise

    def run(self, extraction_run_id: str, url: str | None = None, is_past_event: bool = False) -> None:
        """Main entry point for running the connector."""
        if url:
            self.process_event_from_url(event_url=url, extraction_run_id=extraction_run_id, is_past_event=True)
        else:
            self._extract_event_items(extraction_run_id, is_past_event)


class PastEventExtractionClass:
    def __init__(self, extractor: BaseExtractionClass):
        self.extractor = extractor
        self.base_url = extractor.base_url

    def _impact_filter(self, impact_metadata: list[dict]) -> str:
        filters = []

        for data in impact_metadata or []:
            if (
                data.get("category") == ImpactDetailsEnum.Category.PEOPLE
                and data.get("type") == ImpactDetailsEnum.Type.AFFECTED_TOTAL  # TODO: Add other possible types here.
                and data.get("value") is not None
            ):
                value = data["value"]
                lower_bound = 10 ** (math.floor(math.log10(value)) - 1)
                upper_bound = 10 ** (math.floor(math.log10(value)) + 1)

                filters.append(
                    f"monty:impact_detail.category = '{data['category']}' AND "
                    f"monty:impact_detail.type = '{data['type']}' AND "
                    f"monty:impact_detail.value >= {lower_bound} AND "
                    f"monty:impact_detail.value <= {upper_bound}"
                )

        return " OR ".join(f"({filter})" for filter in filters)

    def _country_filter(self, country_codes) -> list[str]:
        filters = []
        if country_codes:
            country_cql = " OR ".join(f"a_contains(monty:country_codes, '{code}')" for code in country_codes)
            filters.append(f"({country_cql})")
        return filters

    def find_related_events(self, load_obj: LoadItem, extraction_run_id: str) -> set[LoadItem]:
        start_datetime = timezone.now() - timedelta(weeks=self.extractor.connector.lookback_weeks)
        end_datetime = timezone.now()
        events = set()

        if self.extractor.impact_collection_type:
            impact_filter = self._impact_filter(load_obj.impact_metadata)
            country_filters = self._country_filter(load_obj.country_codes)

            additional_filters = []

            if impact_filter:
                additional_filters.append(impact_filter)

            additional_filters.extend(country_filters)

            past_impact_data = fetch_paginated_stac_data(
                self.base_url,
                build_stac_search(
                    collections=self.extractor.impact_collection_type,
                    additional_filters=additional_filters,
                    start_datetime=f"{start_datetime.isoformat()}",
                    end_datetime=f"{end_datetime.isoformat()}",
                    hazard_codes=self.extractor.filter_event.get("hazard_codes") if self.extractor.filter_event else None,
                ),
            )

            existing_events = LoadItem.objects.all()
            event_map = {e.event_url: e for e in existing_events}

            for data in past_impact_data:
                links = data.get("links")
                event_url = self.extractor._extract_related_url(links=links, collection_type=ExtractionItem.CollectionType.EVENT)

                if len(event_url) != 1:
                    raise ValueError(f"Expected 1 EVENT url, got: {event_url}")

                event_url = event_url[0]

                event = event_map.get(event_url)

                if not event:
                    event = self.extractor.process_event_from_url(
                        event_url=event_url, extraction_run_id=extraction_run_id, is_past_event=True
                    )
                    if event:
                        event_map[event_url] = event

                events.add(event)
        return events

    # Need to make changes here if event_id is implemented.
    # Collect all the events, find the latest of all the event ids.
    # Attach only the value of the latest episode in impact fields.

    def extract_past_events(
        self,
        load_obj: LoadItem,
        extraction_run_id: str,
    ) -> None:

        past_events = self.find_related_events(
            load_obj=load_obj,
            extraction_run_id=extraction_run_id,
        )

        valid_events = [event for event in past_events if event.event_id and event.event_id != load_obj.event_id]

        if not valid_events:
            return

        related_ids = [event.id for event in valid_events]

        for event in valid_events:
            event.related_montandon_events.add(load_obj)

        load_obj.related_montandon_events.set(related_ids)
