from . import models

enum_register = {
    "eap_status": models.EAPStatus,
    "eap_type": models.EAPType,
    "sector": models.PlannedOperation.Sector,
    "timeframe": models.TimeFrame,
    "years_timeframe_value": models.YearsTimeFrameChoices,
    "months_timeframe_value": models.MonthsTimeFrameChoices,
    "days_timeframe_value": models.DaysTimeFrameChoices,
    "hours_timeframe_value": models.HoursTimeFrameChoices,
    "approach": models.EnableApproach.Approach,
}
