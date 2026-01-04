from . import models

enum_register = {
    "surge_alert_status": models.SurgeAlertStatus,
    "alert_source": models.AlertSubscription.AlertSource,
    "alert_per_day": models.AlertSubscription.AlertPerDay,
}
