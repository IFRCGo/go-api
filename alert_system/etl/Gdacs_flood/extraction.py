from alert_system.etl.base.extraction import BaseExtractionClass
from alert_system.etl.base.transform import BaseTransformerClass
from alert_system.etl.base.loader import BaseLoaderClass
import logging
from .transform import GdacsTransformer
from .loader import GdacsLoader
from .config import gdacs_flood_config

logger = logging.getLogger(__name__)

class GdacsFloodExtraction(BaseExtractionClass):
    event_endpoint = gdacs_flood_config.event_endpoint
    hazard_endpoint = getattr(gdacs_flood_config, "hazard_endpoint", None)
    impact_endpoint = getattr(gdacs_flood_config, "impact_endpoint", None)
    
    def get_transformer_class(self) -> type[BaseTransformerClass]:
        return GdacsTransformer
    
    def get_loader_class(self) -> type[BaseLoaderClass]:
        return GdacsLoader

