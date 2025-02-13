from celery import shared_task
from django.template.loader import render_to_string

from local_units.models import LocalUnit, LocalUnitChangeRequest

from .utils import get_email_context, get_local_admins

# from notifications.notification import send_notification


@shared_task
def send_local_unit_email(local_unit_id: int, new: bool = True):
    if not local_unit_id:
        return None

    instance = LocalUnit.objects.get(id=local_unit_id)
    users = get_local_admins(instance)
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
        email_context["validator_email"] = user.email
        email_context["full_name"] = user.get_full_name()
        email_body = render_to_string("email/local_units/local_unit.html", email_context)
        print(email_subject, user.email, email_body, email_type)  # send_notification disabling
    return email_context


@shared_task
def send_validate_success_email(local_unit_id: int, message: str = ""):
    if not local_unit_id:
        return None

    instance = LocalUnit.objects.get(id=local_unit_id)
    user = instance.created_by
    email_context = get_email_context(instance)
    email_context["full_name"] = user.get_full_name()
    email_context["validate_success"] = True
    email_subject = "Your Local Unit Addition Request: Approved"
    email_body = render_to_string("email/local_units/local_unit.html", email_context)
    email_type = f"{message} Local Unit"

    print(email_subject, user.email, email_body, email_type)  # send_notification disabling
    return email_context


@shared_task
def send_revert_email(local_unit_id: int, change_request_id: int):
    if not local_unit_id:
        return None

    instance = LocalUnit.objects.get(id=local_unit_id)
    change_request_instance = LocalUnitChangeRequest.objects.get(id=change_request_id)
    user = instance.created_by
    email_context = get_email_context(instance)
    email_context["full_name"] = user.get_full_name()
    email_context["revert_reason"] = change_request_instance.rejected_reason
    email_subject = "Your Local Unit Addition Request: Reverted"
    email_body = render_to_string("email/local_units/local_unit.html", email_context)
    email_type = "Revert Local Unit"

    print(email_subject, user.email, email_body, email_type)  # send_notification disabling
    return email_context


@shared_task
def send_deprecate_email(local_unit_id: int):
    if not local_unit_id:
        return None

    instance = LocalUnit.objects.get(id=local_unit_id)
    user = instance.created_by
    email_context = get_email_context(instance)
    email_context["full_name"] = user.get_full_name()
    email_context["deprecate_local_unit"] = True
    email_context["deprecate_reason"] = instance.deprecated_reason_overview
    email_subject = "Your Local Unit Addition Request: Deprecated"
    email_body = render_to_string("email/local_units/local_unit.html", email_context)
    email_type = "Deprecate Local Unit"

    print(email_subject, user.email, email_body, email_type)  # send_notification disabling
    return email_context
