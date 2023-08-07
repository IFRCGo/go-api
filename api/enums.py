from . import models

enum_register = {
    'region_name': models.RegionName,
    'country_type': models.CountryType,
    'visibility_choices': models.VisibilityChoices,
    'visibility_char_choices': models.VisibilityCharChoices,
    'position_type': models.PositionType,
    'tab_number': models.TabNumber,
    'alert_level': models.AlertLevel,
    'appeal_type': models.AppealType,
    'appeal_status': models.AppealStatus,
    'request_choices': models.RequestChoices,
    'episource_choices': models.EPISourceChoices,
    'field_report_status': models.FieldReport.Status,
    'field_report_recent_affected': models.FieldReport.RecentAffected,
    'field_report_bulletin': models.RequestChoices,
    'action_org': models.ActionOrg,
    'action_type': models.ActionType,
    'action_category': models.ActionCategory,
    'profile_org_types': models.Profile.OrgTypes,
}
