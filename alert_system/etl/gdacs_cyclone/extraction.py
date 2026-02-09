import logging

from alert_system.etl.base.extraction import BaseExtractionClass

from .config import gdacs_cyclone_config
from .loader import GdacsCycloneLoader
from .transform import GdacsCycloneTransformer

logger = logging.getLogger(__name__)


class GdacsCycloneExtraction(BaseExtractionClass):
    config = gdacs_cyclone_config
    transformer_class = GdacsCycloneTransformer
    loader_class = GdacsCycloneLoader
