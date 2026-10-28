import logging
from typing import Optional

from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from django.db import models
from django.utils import timezone

from api.models import Appeal, AppealType, Event
from dref.models import Dref, DrefFinalReport, DrefOperationalUpdate

logger = logging.getLogger(__name__)


def get_email_context(instance):
    from dref.serializers import DrefSerializer

    dref_data = DrefSerializer(instance).data
    email_context = {
        "id": dref_data["id"],
        "title": dref_data["title"],
        "frontend_url": settings.GO_WEB_URL,
    }
    return email_context


def get_final_report_alert_email_context(dref: Dref) -> dict:
    return {
        "mdr_code": dref.appeal_code,
        "operation_name": dref.title,
        "operation_end_date": get_final_report_operation_end_date(dref),
        "due_date": dref.final_report_due_date,
        "frontend_url": settings.GO_WEB_URL,
    }


def get_latest_approved_operational_update(dref: Dref) -> Optional[DrefOperationalUpdate]:
    """Return the latest approved DrefOperationalUpdate sharing the same appeal_code as the given Dref.

    "Approved" here is determined by date_of_approval being set, since date_of_approval is only ever
    set when an Operational Update transitions to Dref.Status.APPROVED (see
    DrefOperationalUpdateViewSet.get_approved). Matching is done via appeal_code rather than the
    Operational Update's dref FK, since appeal_code is the shared business identifier across DREF stages.
    """
    if not dref.appeal_code:
        return None

    return (
        DrefOperationalUpdate.objects.filter(
            appeal_code=dref.appeal_code,
            date_of_approval__isnull=False,
        )
        .order_by("-date_of_approval", "-operational_update_number", "-pk")
        .first()
    )


def get_final_report_operation_end_date(dref: Dref):
    """Use the latest approved update's end date, falling back to the application."""
    latest_operational_update = get_latest_approved_operational_update(dref)
    if latest_operational_update and latest_operational_update.new_operational_end_date:
        return latest_operational_update.new_operational_end_date
    return dref.end_date


def get_final_report_alert_recipients(dref: Dref) -> tuple[list, list]:
    """Recipients are sourced from the DREF Application contact fields, with each field overridden
    (where non-empty) by the latest approved Operational Update's corresponding contact, since the
    Operational Update may hold more up-to-date contact information than the original Application."""
    latest_operational_update = get_latest_approved_operational_update(dref)

    def get_contact(field_name: str) -> str:
        if latest_operational_update is not None:
            value = getattr(latest_operational_update, field_name)
            if value:
                return value
        return getattr(dref, field_name)

    to_emails = [
        get_contact("ifrc_appeal_manager_email"),
        get_contact("ifrc_project_manager_email"),
        get_contact("national_society_contact_email"),
    ]
    cc_emails = [get_contact("regional_focal_point_email")]
    return to_emails, cc_emails


def get_dref_users():
    dref_users_qs = Dref.objects.annotate(
        created_user_list=ArrayAgg("created_by", filter=models.Q(created_by__isnull=False)),
        users_list=ArrayAgg("users", filter=models.Q(users__isnull=False)),
        op_users=models.Subquery(
            DrefOperationalUpdate.objects.filter(dref=models.OuterRef("id"))
            .order_by()
            .values("dref")
            .annotate(c=ArrayAgg("users", filter=models.Q(users__isnull=False)))
            .values("c")[:1]
        ),
        fr_users=models.Subquery(
            DrefFinalReport.objects.filter(dref=models.OuterRef("id"))
            .order_by()
            .values("dref")
            .annotate(c=ArrayAgg("users", filter=models.Q(users__isnull=False)))
            .values("c")[:1],
        ),
    ).values("id", "created_user_list", "users_list", "op_users", "fr_users")
    dref_users_list = []
    for dref in dref_users_qs:
        if dref["created_user_list"] is None:
            dref["created_user_list"] = []
        if dref["users_list"] is None:
            dref["users_list"] = []
        if dref["op_users"] is None:
            dref["op_users"] = []
        if dref["fr_users"] is None:
            dref["fr_users"] = []
        dref_users_list.append(
            dict(
                id=dref["id"],
                users=set(list(dref["created_user_list"] + dref["users_list"] + dref["op_users"] + dref["fr_users"])),
            )
        )
    return dref_users_list


def create_event_from_dref(dref: Dref) -> Event:
    create_kwargs = dict(
        name=dref.title,
        dtype=dref.disaster_type,
        summary=dref.event_description or dref.event_scope or "",
        disaster_start_date=dref.event_date or dref.hazard_date,
        glide=dref.glide_codes[0] if dref.glide_codes else "",
        auto_generated=True,
        source=Event.EventSource.DREF,
    )

    # Dref.DisasterCategory and api.AlertLevel share the same 0/1/2 indices, so
    # the value maps directly with no remap.
    if dref.disaster_category is not None:
        create_kwargs["ifrc_severity_level"] = dref.disaster_category
        create_kwargs["ifrc_severity_level_update_date"] = dref.date_of_approval or timezone.now()

    event = Event.objects.create(**create_kwargs)

    country = getattr(dref, "country", None)
    if country:
        event.countries.add(dref.country)

    event.districts.add(*dref.district.all())
    region = getattr(country, "region", None)
    if region:
        event.regions.add(region)

    link_appeal_to_event(dref.appeal_code, event)
    return event


def link_appeal_to_event(appeal_code: str | None, event: Event) -> None:
    """Link the DREF Appeal matched by appeal_code to the given event.

    If the Appeal is already linked to a different event, leave it alone and log
    for manual review instead of overwriting an existing link.
    """
    if not appeal_code:
        return

    logger.info("Linking DREF Appeal code=%s to event id=%s", appeal_code, event.id)

    appeal = Appeal.objects.filter(code=appeal_code, atype=AppealType.DREF).first()
    if appeal is None:
        return

    if appeal.event_id is None:
        appeal.event = event
        appeal.save(update_fields=["event"])
    elif appeal.event_id != event.id:
        logger.warning(
            "Appeal id=%s (code=%s) is already linked to event id=%s; not relinking to event id=%s.",
            appeal.id,
            appeal_code,
            appeal.event_id,
            event.id,
        )


def sync_event_from_dref(instance: DrefOperationalUpdate | DrefFinalReport) -> None:
    """Propagate an ops-update/final-report's glide code back to its event,
    and link a matching DREF Appeal to the event."""
    event = instance.dref.event
    if not event:
        return
    primary_glide_code = instance.glide_codes[0] if instance.glide_codes else ""
    if primary_glide_code and event.glide != primary_glide_code:
        event.glide = primary_glide_code
        event.save(update_fields=["glide"])
    link_appeal_to_event(instance.appeal_code, event)
