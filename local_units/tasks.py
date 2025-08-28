import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

from local_units.bulk_upload import BaseBulkUploadLocalUnit, BulkUploadHealthData
from local_units.models import LocalUnit, LocalUnitBulkUpload, LocalUnitChangeRequest
from notifications.notification import send_notification

from .utils import (
    get_email_context,
    get_local_unit_country_validators,
    get_local_unit_global_validators,
    get_local_unit_region_validators,
)

User = get_user_model()

logger = logging.getLogger(__name__)


@shared_task
def send_local_unit_email(local_unit_id: int, new: bool = True):
    if not local_unit_id:
        return None
    instance = LocalUnit.objects.get(id=local_unit_id)
    users = (
        get_local_unit_country_validators(instance)
        or get_local_unit_region_validators(instance)
        or get_local_unit_global_validators(instance)
        or User.objects.filter(is_superuser=True)
    )

    email_context = get_email_context(instance)
    email_context["new_local_unit"] = True
    email_subject = "Action Required: New Local Unit Pending Validation"
    email_type = "New Local Unit"
    # NOTE: Update case for the local unit
    if not new:
        email_context.pop("new_local_unit")
        email_context["update_local_unit"] = True
        email_subject = "Action Required: Local Unit Pending Validation"
        email_type = "Update Local Unit"

    for user in users:
        # NOTE: Adding the validator email to the context
        if not user.email:
            logger.warning(f"Email address not found for validator: {user.get_full_name()}.")
            return None
        email_context["validator_email"] = user.email
        email_context["full_name"] = user.get_full_name()
        email_body = render_to_string("email/local_units/local_unit.html", email_context)
        send_notification(email_subject, user.email, email_body, email_type)


@shared_task
def send_validate_success_email(local_unit_id: int, message: str = ""):
    if not local_unit_id:
        return None

    instance = LocalUnit.objects.get(id=local_unit_id)
    user = instance.created_by
    if not user:
        logger.warning(f"Email not sent for Local Unit:{local_unit_id} because creator is unknown.")
        return None
    elif not user.email:
        logger.warning(
            f"Email not sent for Local Unit:{local_unit_id} because creator: {user.get_full_name()} has no email address."
        )
        return None
    email_context = get_email_context(instance)
    email_context["full_name"] = user.get_full_name()
    email_context["validate_success"] = True
    email_subject = "Your Local Unit Addition Request: Approved"
    email_body = render_to_string("email/local_units/local_unit.html", email_context)
    email_type = f"{message} Local Unit"
    send_notification(email_subject, user.email, email_body, email_type)
    return email_context


@shared_task
def send_revert_email(local_unit_id: int, change_request_id: int):
    if not local_unit_id:
        return None

    instance = LocalUnit.objects.get(id=local_unit_id)
    change_request_instance = LocalUnitChangeRequest.objects.get(id=change_request_id)
    user = instance.created_by
    if not user:
        logger.warning(f"Email not sent for Local Unit:{local_unit_id} because creator is unknown.")
        return None
    elif not user.email:
        logger.warning(
            f"Email not sent for Local Unit:{local_unit_id} because creator: {user.get_full_name()} has no email address."
        )
        return None
    email_context = get_email_context(instance)
    email_context["full_name"] = user.get_full_name()
    email_context["revert_reason"] = change_request_instance.rejected_reason
    email_subject = "Your Local Unit Addition Request: Reverted"
    email_body = render_to_string("email/local_units/local_unit.html", email_context)
    email_type = "Revert Local Unit"

    send_notification(email_subject, user.email, email_body, email_type)
    return email_context


@shared_task
def send_deprecate_email(local_unit_id: int):
    if not local_unit_id:
        return None

    instance = LocalUnit.objects.get(id=local_unit_id)
    user = instance.created_by
    if not user:
        logger.warning(f"Email not sent for Local Unit:{local_unit_id} because creator is unknown.")
        return None
    elif not user.email:
        logger.warning(
            f"Email not sent for Local Unit:{local_unit_id} because creator: {user.get_full_name()} has no email address."
        )
        return None

    email_context = get_email_context(instance)
    email_context["full_name"] = user.get_full_name()
    email_context["deprecate_local_unit"] = True
    email_context["deprecate_reason"] = instance.deprecated_reason_overview
    email_subject = "Your Local Unit Addition Request: Deprecated"
    email_body = render_to_string("email/local_units/local_unit.html", email_context)
    email_type = "Deprecate Local Unit"
    send_notification(email_subject, user.email, email_body, email_type)
    return email_context


@shared_task
def process_bulk_upload_local_unit(bulk_upload_id: int) -> None:
    bulk_upload: LocalUnitBulkUpload | None = LocalUnitBulkUpload.objects.filter(id=bulk_upload_id).first()

    if not bulk_upload:
        logger.warning(f"BulkUploadLocalUnit:'{bulk_upload_id}' Not found.", exc_info=True)
        return
    try:
        if (
            bulk_upload.local_unit_type.name.lower() == "health care"
        ):  # FIXME(@sudip-khanal): add enum after the LocalUnitTypeEnum implementation
            BulkUploadHealthData(bulk_upload).run()
        else:
            BaseBulkUploadLocalUnit(bulk_upload).run()

    except Exception as exc:
        logger.warning(f"BulkUploadLocalUnit:'{bulk_upload_id}' Failed with exception: {exc}", exc_info=True)
        bulk_upload.update_status(LocalUnitBulkUpload.Status.FAILED)
        raise exc
