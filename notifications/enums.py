from . import models

enum_register = {
    "surge_alert_status": models.SurgeAlertStatus,
    "alert_source": models.AlertSubscription.AlertSource,
    "hazard_type": models.HazardType.Type,
    "alert_per_day": models.AlertSubscription.AlertPerDay,
}
