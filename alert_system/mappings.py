from dataclasses import dataclass

from alert_system.etl.Gdacs_flood.extraction import GdacsFloodExtraction
from alert_system.models import Connector


# NOTE: Store all the mappings here.
@dataclass
class ConnectorClasses:
    extractor: type


CONNECTOR_REGISTRY = {
    Connector.ConnectorType.GDACS_FLOOD: ConnectorClasses(extractor=GdacsFloodExtraction),
}
