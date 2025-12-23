import logging

from alert_system.etl.base.extraction import BaseExtractionClass

from .config import gdacs_flood_config
from .loader import GdacsLoader
from .transform import GdacsTransformer

logger = logging.getLogger(__name__)


class GdacsFloodExtraction(BaseExtractionClass):
    config = gdacs_flood_config
    transformer_class = GdacsTransformer
    loader_class = GdacsLoader
