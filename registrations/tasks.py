from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string

from notifications.notification import send_notification


@shared_task
def send_notification_create(token, username, is_staff, email):
    email_context = {
        "confirmation_link": "%s/verify_email/?token=%s&user=%s"
        % (
            settings.GO_API_URL,  # on PROD it should point to goadmin...
            token,
            username,
        )
    }

    # if validated email accounts get a different message
    if is_staff:
        template = "email/registration/verify-staff-email.html"
    else:
        template = "email/registration/verify-outside-email.html"

    send_notification(
        "Validate your account", [email], render_to_string(template, email_context), "Validate account - " + username
    )
