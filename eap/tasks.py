import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

from eap.models import EAPRegistration
from eap.utils import (
    get_coordinator_emails_by_region,
    get_eap_registration_email_context,
)
from notifications.notification import send_notification

User = get_user_model()

logger = logging.getLogger(__name__)


@shared_task
def send_new_eap_registration_email(eap_registration_id: int):

    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None

    regional_coordinator_emails = get_coordinator_emails_by_region(instance.country.region)

    recipients = [
        settings.EMAIL_EAP_DREF_ANTICIPATORY_PILLAR,
        instance.ifrc_contact_email,
    ]
    cc_recipients = list(
        set(
            [
                instance.national_society_contact_email,
                *settings.EMAIL_EAP_DREF_AA_GLOBAL_TEAM,
                *regional_coordinator_emails,
            ]
        )
    )
    email_context = get_eap_registration_email_context(instance)
    email_subject = (
        f"[{instance.get_eap_type_display() if instance.get_eap_type_display() else 'EAP'} IN DEVELOPMENT] "
        f"{instance.country} {instance.disaster_type}"
    )
    email_body = render_to_string("email/eap/registration.html", email_context)
    email_type = "New EAP Registration"

    send_notification(
        subject=email_subject,
        recipients=recipients,
        html=email_body,
        mailtype=email_type,
        cc_recipients=cc_recipients,
    )

    return email_context
