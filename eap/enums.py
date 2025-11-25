from . import models

enum_register = {
    "eap_status": models.EAPStatus,
    "eap_type": models.EAPType,
    "sector": models.PlannedOperation.Sector,
    "timeframe": models.OperationActivity.TimeFrame,
    "years_timeframe_value": models.OperationActivity.YearsTimeFrameChoices,
    "months_timeframe_value": models.OperationActivity.MonthsTimeFrameChoices,
    "days_timeframe_value": models.OperationActivity.DaysTimeFrameChoices,
    "hours_timeframe_value": models.OperationActivity.HoursTimeFrameChoices,
    "approach": models.EnableApproach.Approach,
}
