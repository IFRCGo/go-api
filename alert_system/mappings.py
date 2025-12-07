from dataclasses import dataclass

from alert_system.etl.base.extraction import BaseExtractionClass
from alert_system.etl.base.loader import BaseLoaderClass
from alert_system.etl.base.transform import BaseTransformerClass
from alert_system.etl.Gdacs_flood.extraction import GdacsFloodExtraction
from alert_system.etl.Gdacs_flood.loader import GdacsLoader
from alert_system.etl.Gdacs_flood.transform import GdacsTransformer
from alert_system.models import Connector


# NOTE: Store all the mappings here.
@dataclass
class ConnectorClasses:
    extractor: type[BaseExtractionClass]
    transfomer: type[BaseTransformerClass]
    loader: type[BaseLoaderClass]


CONNECTOR_REGISTRY = {
    Connector.ConnectorType.GDACS_FLOOD: ConnectorClasses(
        extractor=GdacsFloodExtraction, transfomer=GdacsTransformer, loader=GdacsLoader
    ),
}
