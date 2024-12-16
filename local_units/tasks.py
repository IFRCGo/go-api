from celery import shared_task
from django.template.loader import render_to_string

from local_units.models import LocalUnit
from notifications.notification import send_notification

from .utils import get_email_context


@shared_task
def send_local_unit_email(local_unit_id, users_emails, new_or_updated=""):
    if not local_unit_id or not users_emails:
        return None

    instance = LocalUnit.objects.get(id=local_unit_id)
    email_context = get_email_context(instance)
    email_subject = f"Action Required: {new_or_updated} Local Unit Pending Validation"
    email_body = render_to_string("email/local_units/local_unit.html", email_context)
    email_type = f"{new_or_updated} Local Unit"

    send_notification(email_subject, users_emails, email_body, email_type)
    return email_context
