import logging

from alert_system.etl.base.extraction import BaseExtractionClass

from .config import usgs_earthquake_config
from .loader import USGSLoader
from .transform import USGSTransformer

logger = logging.getLogger(__name__)


class USGSEarthquakeExtraction(BaseExtractionClass):
    config = usgs_earthquake_config
    transformer_class = USGSTransformer
    loader_class = USGSLoader
