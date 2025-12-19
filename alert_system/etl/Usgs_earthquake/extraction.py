import logging

from alert_system.etl.base.extraction import BaseExtractionClass

from .config import usgs_earthquake_config
from .loader import USGSLoader
from .transform import USGSTransformer

logger = logging.getLogger(__name__)


class USGSEarthquakeExtraction(BaseExtractionClass):
    event_collection_type = usgs_earthquake_config.event_collection_type
    hazard_collection_type = getattr(usgs_earthquake_config, "hazard_collection_type", None)
    impact_collection_type = getattr(usgs_earthquake_config, "impact_collection_type", None)
    filter_event = getattr(usgs_earthquake_config, "filter_event", None)
    transformer_class = USGSTransformer
    loader_class = USGSLoader
