import logging

from alert_system.etl.base.extraction import BaseExtractionClass

from .config import gdacs_flood_config
from .loader import GdacsLoader
from .transform import GdacsTransformer

logger = logging.getLogger(__name__)


class GdacsFloodExtraction(BaseExtractionClass):
    event_collection_type = gdacs_flood_config.event_collection_type
    hazard_collection_type = getattr(gdacs_flood_config, "hazard_collection_type", None)
    impact_collection_type = getattr(gdacs_flood_config, "impact_collection_type", None)
    filter_event = getattr(gdacs_flood_config, "filter_event", None)
    transformer_class = GdacsTransformer
    loader_class = GdacsLoader
