from dataclasses import dataclass

from alert_system.etl.base.extraction import BaseExtractionClass
from alert_system.etl.gdacs_flood.extraction import GdacsFloodExtraction
from alert_system.etl.usgs_earthquake.extraction import USGSEarthquakeExtraction
from alert_system.models import Connector


# NOTE: Store all the mappings here.
@dataclass
class ConnectorClasses:
    extractor: type[BaseExtractionClass]


CONNECTOR_REGISTRY = {
    Connector.ConnectorType.GDACS_FLOOD: ConnectorClasses(extractor=GdacsFloodExtraction),
    Connector.ConnectorType.USGS_EARTHQUAKE: ConnectorClasses(extractor=USGSEarthquakeExtraction),
}
