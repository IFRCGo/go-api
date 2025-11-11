from . import models

enum_register = {
    "eap_status": models.EAPStatus,
    "eap_type": models.EAPType,
    "sector": models.PlannedOperation.Sector,
    "timeframe": models.OperationActivity.TimeFrame,
    "approach": models.EnableApproach.Approach,
}
