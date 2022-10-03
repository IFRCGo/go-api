from celery import shared_task
from django.template.loader import render_to_string
from notifications.notification import send_notification
from .models import Dref
from .utils import get_email_context


@shared_task
def send_dref_email(dref_id, new_or_updated=''):
    instance = Dref.objects.get(id=dref_id)
    email_context = get_email_context(instance)
    users_emails = [t.email for t in instance.users.iterator()]
    if users_emails:
        send_notification(
            f'{new_or_updated} DREF: {instance.title}',
            users_emails,
            render_to_string('email/dref/dref.html', email_context),
            f'{new_or_updated} DREF'
        )
    return email_context
