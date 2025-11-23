from dataclasses import dataclass

from alert_system.extraction.gdacs_cyclone import GdacsCycloneExtraction
from alert_system.extraction.gdacs_flood import GdacsFloodExtraction
from alert_system.extraction.usgs_earthquake import USGSEarthquakeExtraction
from alert_system.filters.gdacs_cyclone import GdacsCycloneFilter
from alert_system.filters.gdacs_flood import GdacsFloodFilter
from alert_system.filters.usgs_earthquake import USGSEarthquakeFilter
from alert_system.models import Connector


@dataclass
class ConnectorClasses:
    extractor: type
    filter: type


CONNECTOR_REGISTRY = {
    Connector.ConnectorType.GDACS_FLOOD: ConnectorClasses(extractor=GdacsFloodExtraction, filter=GdacsFloodFilter),
    Connector.ConnectorType.GDACS_CYCLONE: ConnectorClasses(extractor=GdacsCycloneExtraction, filter=GdacsCycloneFilter),
    Connector.ConnectorType.USGS_EARTHQUAKE: ConnectorClasses(extractor=USGSEarthquakeExtraction, filter=USGSEarthquakeFilter),
}
