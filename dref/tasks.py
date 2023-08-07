from celery import shared_task
from django.template.loader import render_to_string
from notifications.notification import send_notification
from .models import Dref
from .utils import get_email_context


@shared_task
def send_dref_email(dref_id, users_emails, new_or_updated=""):
    if not dref_id or not users_emails:
        return None

    instance = Dref.objects.get(id=dref_id)
    email_context = get_email_context(instance)
    email_subject = f"{new_or_updated} DREF: {instance.title}"
    email_body = render_to_string("email/dref/dref.html", email_context)
    email_type = f"{new_or_updated} DREF"

    send_notification(email_subject, users_emails, email_body, email_type)
    return email_context
