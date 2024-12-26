from celery import shared_task
from django.template.loader import render_to_string

from local_units.models import LocalUnit
from notifications.notification import send_notification

from .utils import get_email_context


@shared_task
def send_local_unit_email(local_unit_id, users_emails, new=True):
    if not local_unit_id or not users_emails:
        return None

    instance = LocalUnit.objects.get(id=local_unit_id)
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

    for email in users_emails:
        # NOTE: Adding the validator email to the context
        email_context["validator_email"] = email
        email_body = render_to_string("email/local_units/local_unit.html", email_context)
        send_notification(email_subject, email, email_body, email_type)
    return email_context


@shared_task
def send_validate_success_email(local_unit_id, users_emails, new_or_updated=""):
    if not local_unit_id or not users_emails:
        return None

    instance = LocalUnit.objects.get(id=local_unit_id)
    email_context = get_email_context(instance)
    email_context["validator_email"] = users_emails
    email_context["validate_success"] = True
    email_subject = "Your Local Unit Addition Request: Approved"
    email_body = render_to_string("email/local_units/local_unit.html", email_context)
    email_type = f"{new_or_updated} Local Unit"

    send_notification(email_subject, users_emails, email_body, email_type)
    return email_context


@shared_task
def send_revert_email(local_unit_id, users_emails, reason):
    if not local_unit_id or not users_emails:
        return None

    instance = LocalUnit.objects.get(id=local_unit_id)
    email_context = get_email_context(instance)
    email_context["validator_email"] = users_emails
    email_context["revert_reason"] = reason
    email_subject = "Your Local Unit Addition Request: Reverted"
    email_body = render_to_string("email/local_units/local_unit.html", email_context)
    email_type = "Revert Local Unit"

    send_notification(email_subject, users_emails, email_body, email_type)
    return email_context


@shared_task
def send_deprecate_email(local_unit_id, users_emails, reason):
    if not local_unit_id or not users_emails:
        return None

    instance = LocalUnit.objects.get(id=local_unit_id)
    email_context = get_email_context(instance)
    email_context["validator_email"] = users_emails
    email_context["deprecate_local_unit"] = True
    email_context["deprecate_reason"] = reason
    email_subject = "Your Local Unit Addition Request: Deprecated"
    email_body = render_to_string("email/local_units/local_unit.html", email_context)
    email_type = "Deprecate Local Unit"

    send_notification(email_subject, users_emails, email_body, email_type)
    return email_context
