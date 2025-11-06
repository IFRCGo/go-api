from . import models

enum_register = {
    "eap_status": models.EAPStatus,
    "eap_type": models.EAPType,
    "sector": models.PlannedOperations.Sector,
    "timeframe": models.OperationActivity.TimeFrame,
}
