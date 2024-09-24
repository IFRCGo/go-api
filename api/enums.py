import strawberry
import typing
from utils.strawberry.enums import get_enum_name_from_django_field

from . import models

# -- DREF
enum_register = {
    "region_name": models.RegionName,
    "country_type": models.CountryType,
    "visibility_choices": models.VisibilityChoices,
    "visibility_char_choices": models.VisibilityCharChoices,
    "position_type": models.PositionType,
    "tab_number": models.TabNumber,
    "alert_level": models.AlertLevel,
    "appeal_type": models.AppealType,
    "appeal_status": models.AppealStatus,
    "request_choices": models.RequestChoices,
    "episource_choices": models.EPISourceChoices,
    "field_report_status": models.FieldReport.Status,
    "field_report_recent_affected": models.FieldReport.RecentAffected,
    "field_report_bulletin": models.RequestChoices,
    "action_org": models.ActionOrg,
    "action_type": models.ActionType,
    "action_category": models.ActionCategory,
    "profile_org_types": models.Profile.OrgTypes,
    "supporting_type": models.CountrySupportingPartner.SupportingPartnerType,
}


# -- GraphQl
AppealTypeEnum = typing.Annotated[models.AppealType, strawberry.enum(models.AppealType, name="AppealTypeEnum")]
AppealStatusEnum = typing.Annotated[models.AppealStatus, strawberry.enum(models.AppealStatus, name="AppealStatusEnum")]
CountryTypeEnum = typing.Annotated[models.CountryType, strawberry.enum(models.CountryType, name="CountryTypeEnum")]

enum_map = {
    get_enum_name_from_django_field(field): enum
    for field, enum in (
        (models.Appeal.atype, AppealTypeEnum),
        (models.Appeal.status, AppealStatusEnum),
        (models.Country.record_type, CountryTypeEnum),
    )
}
