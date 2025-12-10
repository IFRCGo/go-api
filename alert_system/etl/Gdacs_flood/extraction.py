import logging

from alert_system.etl.base.extraction import BaseExtractionClass

from .config import gdacs_flood_config
from .loader import GdacsLoader
from .transform import GdacsTransformer

logger = logging.getLogger(__name__)


class GdacsFloodExtraction(BaseExtractionClass):
    event_endpoint = gdacs_flood_config.event_endpoint
    hazard_endpoint = getattr(gdacs_flood_config, "hazard_endpoint", None)
    impact_endpoint = getattr(gdacs_flood_config, "impact_endpoint", None)
    transformer_class = GdacsTransformer
    loader_class = GdacsLoader
