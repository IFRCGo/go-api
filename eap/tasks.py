import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

from eap.models import EAPRegistration, EAPType, FullEAP, SimplifiedEAP
from eap.utils import get_coordinator_emails_by_region, get_eap_email_context
from notifications.notification import send_notification

User = get_user_model()

logger = logging.getLogger(__name__)


@shared_task
def send_new_eap_registration_email(eap_registration_id: int):

    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None

    regional_coordinator_emails: list[str] = get_coordinator_emails_by_region(instance.country.region)

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
    email_context = get_eap_email_context(instance)
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


@shared_task
def send_new_eap_submission_email(eap_registration_id: int):
    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None

    if instance.get_eap_type_enum == EAPType.SIMPLIFIED_EAP:
        latest_simplified_eap = instance.latest_simplified_eap
        partner_ns_email = latest_simplified_eap.partner_ns_email
    else:
        latest_full_eap = instance.latest_full_eap
        partner_ns_email = latest_full_eap.partner_ns_email

    regional_coordinator_emails: list[str] = get_coordinator_emails_by_region(instance.country.region)

    recipients = [
        settings.EMAIL_EAP_DREF_ANTICIPATORY_PILLAR,
        instance.ifrc_contact_email,
    ]
    cc_recipients = list(
        set(
            [
                partner_ns_email,
                instance.national_society_contact_email,
                *settings.EMAIL_EAP_DREF_AA_GLOBAL_TEAM,
                *regional_coordinator_emails,
            ]
        )
    )
    email_context = get_eap_email_context(instance)
    email_subject = (
        f"[DREF {instance.get_eap_type_display()} FOR REVIEW] " f"{instance.country} {instance.disaster_type} TO THE IFRC-DREF"
    )
    email_body = render_to_string("email/eap/submission.html", email_context)
    email_type = "EAP Submission"
    send_notification(
        subject=email_subject,
        recipients=recipients,
        html=email_body,
        mailtype=email_type,
        cc_recipients=cc_recipients,
    )

    return email_context


@shared_task
def send_feedback_email(eap_registration_id: int):

    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None

    if instance.get_eap_type_enum == EAPType.SIMPLIFIED_EAP:
        latest_simplified_eap = instance.latest_simplified_eap
        partner_ns_email = latest_simplified_eap.partner_ns_email
        ifrc_delegation_focal_point_email = latest_simplified_eap.ifrc_delegation_focal_point_email
    else:
        latest_full_eap = instance.latest_full_eap
        partner_ns_email = latest_full_eap.partner_ns_name
        ifrc_delegation_focal_point_email = latest_full_eap.ifrc_delegation_focal_point_email

    regional_coordinator_emails: list[str] = get_coordinator_emails_by_region(instance.country.region)

    recipient = [
        instance.national_society_contact_email,
    ]

    cc_recipients = list(
        set(
            [
                partner_ns_email,
                ifrc_delegation_focal_point_email,
                settings.EMAIL_EAP_DREF_ANTICIPATORY_PILLAR,
                *settings.EMAIL_EAP_DREF_AA_GLOBAL_TEAM,
                *regional_coordinator_emails,
            ]
        )
    )
    email_context = get_eap_email_context(instance)
    email_subject = (
        f"[DREF {instance.get_eap_type_display()} FEEDBACK] "
        f"{instance.country} {instance.disaster_type} TO THE {instance.national_society}"
    )
    email_body = render_to_string("email/eap/feedback_to_national_society.html", email_context)
    email_type = "Feedback to the National Society"
    send_notification(
        subject=email_subject,
        recipients=recipient,
        html=email_body,
        mailtype=email_type,
        cc_recipients=cc_recipients,
    )

    return email_context


@shared_task
def send_eap_resubmission_email(eap_registration_id: int):

    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None

    if instance.get_eap_type_enum == EAPType.SIMPLIFIED_EAP:
        latest_simplified_eap = instance.latest_simplified_eap
        partner_ns_email = latest_simplified_eap.partner_ns_email
        latest_version = latest_simplified_eap.version
    else:
        latest_full_eap = instance.latest_full_eap
        partner_ns_email = latest_full_eap.partner_ns_name
        latest_version = latest_full_eap.version

    regional_coordinator_emails: list[str] = get_coordinator_emails_by_region(instance.country.region)

    recipients = [
        settings.EMAIL_EAP_DREF_ANTICIPATORY_PILLAR,
        instance.ifrc_contact_email,
    ]

    cc_recipients = list(
        set(
            [
                partner_ns_email,
                instance.national_society_contact_email,
                *settings.EMAIL_EAP_DREF_AA_GLOBAL_TEAM,
                *regional_coordinator_emails,
            ]
        )
    )
    email_context = get_eap_email_context(instance)
    email_subject = (
        f"[DREF {instance.get_eap_type_display()} FOR REVIEW] "
        f"{instance.country} {instance.disaster_type} version {latest_version} TO THE IFRC-DREF"
    )
    email_body = render_to_string("email/eap/re-submission.html", email_context)
    email_type = "Feedback to the National Society"
    send_notification(
        subject=email_subject,
        recipients=recipients,
        html=email_body,
        mailtype=email_type,
        cc_recipients=cc_recipients,
    )

    return email_context


@shared_task
def send_feedback_email_for_resubmitted_eap(eap_registration_id: int):

    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None

    if instance.get_eap_type_enum == EAPType.SIMPLIFIED_EAP:
        partner_ns_email = instance.latest_simplified_eap.partner_ns_email
        latest_version = instance.latest_simplified_eap.version
        qs = SimplifiedEAP.objects.filter(eap_registration=instance, version__lt=latest_version).order_by("-version").first()
        previous_version = qs.version if qs else None

    else:
        partner_ns_email = instance.latest_full_eap.partner_ns_email
        latest_version = instance.latest_full_eap.version
        qs = FullEAP.objects.filter(eap_registration=instance, version__lt=latest_version).order_by("-version").first()
        previous_version = qs.version if qs else None

    regional_coordinator_emails: list[str] = get_coordinator_emails_by_region(instance.country.region)

    recipients = [
        instance.national_society_contact_email,
    ]

    cc_recipients = list(
        set(
            [
                partner_ns_email,
                settings.EMAIL_EAP_DREF_ANTICIPATORY_PILLAR,
                *settings.EMAIL_EAP_DREF_AA_GLOBAL_TEAM,
                *regional_coordinator_emails,
            ]
        )
    )
    email_context = get_eap_email_context(instance)
    email_subject = (
        f"[DREF {instance.get_eap_type_display()} FEEDBACK] "
        f"{instance.country} {instance.disaster_type} version {previous_version} TO {instance.national_society}"
    )
    email_body = render_to_string("email/eap/feedback_to_revised_eap.html", email_context)
    email_type = "Feedback to the National Society"
    send_notification(
        subject=email_subject,
        recipients=recipients,
        html=email_body,
        mailtype=email_type,
        cc_recipients=cc_recipients,
    )

    return email_context


@shared_task
def send_technical_validation_email(eap_registration_id: int):

    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None

    if instance.get_eap_type_enum == EAPType.SIMPLIFIED_EAP:
        latest_simplified_eap = instance.latest_simplified_eap
        partner_ns_email = latest_simplified_eap.partner_ns_email
    else:
        latest_full_eap = instance.latest_full_eap
        partner_ns_email = latest_full_eap.partner_ns_name

    regional_coordinator_emails: list[str] = get_coordinator_emails_by_region(instance.country.region)

    recipient = [
        instance.national_society_contact_email,
    ]

    cc_recipients = list(
        set(
            [
                partner_ns_email,
                settings.EMAIL_EAP_DREF_ANTICIPATORY_PILLAR,
                *settings.EMAIL_EAP_DREF_AA_GLOBAL_TEAM,
                *regional_coordinator_emails,
            ]
        )
    )
    email_context = get_eap_email_context(instance)
    email_subject = f"[DREF {instance.get_eap_type_display()} TECHNICALLY VALIDATED] {instance.country} {instance.disaster_type}"
    email_body = render_to_string("email/eap/technically_validated_eap.html", email_context)
    email_type = "Technically Validated EAP"
    send_notification(
        subject=email_subject,
        recipients=recipient,
        html=email_body,
        mailtype=email_type,
        cc_recipients=cc_recipients,
    )
    return email_context


@shared_task
def send_pending_pfa_email(eap_registration_id: int):

    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None

    if instance.get_eap_type_enum == EAPType.SIMPLIFIED_EAP:
        latest_simplified_eap = instance.latest_simplified_eap
        partner_ns_email = latest_simplified_eap.partner_ns_email
    else:
        latest_full_eap = instance.latest_full_eap
        partner_ns_email = latest_full_eap.partner_ns_name

    regional_coordinator_emails: list[str] = get_coordinator_emails_by_region(instance.country.region)

    recipient = [
        instance.national_society_contact_email,
    ]

    cc_recipients = list(
        set(
            [
                partner_ns_email,
                settings.EMAIL_EAP_DREF_ANTICIPATORY_PILLAR,
                *settings.EMAIL_EAP_DREF_AA_GLOBAL_TEAM,
                *regional_coordinator_emails,
            ]
        )
    )
    email_context = get_eap_email_context(instance)
    email_subject = f"[DREF {instance.get_eap_type_display()} APPROVED PENDING PFA] {instance.country} {instance.disaster_type}"
    email_body = render_to_string("email/eap/pending_pfa.html", email_context)
    email_type = "Approved Pending PFA EAP"
    send_notification(
        subject=email_subject,
        recipients=recipient,
        html=email_body,
        mailtype=email_type,
        cc_recipients=cc_recipients,
    )
    return email_context


@shared_task
def send_approved_email(eap_registration_id: int):

    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None

    if instance.get_eap_type_enum == EAPType.SIMPLIFIED_EAP:
        latest_simplified_eap = instance.latest_simplified_eap
        partner_ns_email = latest_simplified_eap.partner_ns_email
        email_context = "Simplified EAP"
    else:
        latest_full_eap = instance.latest_full_eap
        partner_ns_email = latest_full_eap.partner_ns_name
        email_context = "Full EAP"

    regional_coordinator_emails: list[str] = get_coordinator_emails_by_region(instance.country.region)

    recipient = [
        instance.national_society_contact_email,
    ]

    cc_recipients = list(
        set(
            [
                partner_ns_email,
                settings.EMAIL_EAP_DREF_ANTICIPATORY_PILLAR,
                *settings.EMAIL_EAP_DREF_AA_GLOBAL_TEAM,
                *regional_coordinator_emails,
            ]
        )
    )
    email_context = get_eap_email_context(instance)
    email_subject = f"[DREF {instance.get_eap_type_display()} APPROVED] {instance.country} {instance.disaster_type}"
    email_body = render_to_string("email/eap/approved.html", email_context)
    email_type = "Approved EAP"
    send_notification(
        subject=email_subject,
        recipients=recipient,
        html=email_body,
        mailtype=email_type,
        cc_recipients=cc_recipients,
    )
    return email_context


@shared_task
def send_deadline_reminder_email(eap_registration_id: int):

    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None

    if instance.get_eap_type_enum == EAPType.SIMPLIFIED_EAP:
        latest_simplified_eap = instance.latest_simplified_eap
        partner_ns_email = latest_simplified_eap.partner_ns_email
    else:
        latest_full_eap = instance.latest_full_eap
        partner_ns_email = latest_full_eap.partner_ns_name

    regional_coordinator_emails: list[str] = get_coordinator_emails_by_region(instance.country.region)

    recipient = [
        instance.national_society_contact_email,
    ]

    cc_recipients = list(
        set(
            [
                partner_ns_email,
                settings.EMAIL_EAP_DREF_ANTICIPATORY_PILLAR,
                *settings.EMAIL_EAP_DREF_AA_GLOBAL_TEAM,
                *regional_coordinator_emails,
            ]
        )
    )
    email_context = get_eap_email_context(instance)
    email_subject = f"[DREF {instance.get_eap_type_display()} SUBMISSION REMINDER] {instance.country} {instance.disaster_type}"
    email_body = render_to_string("email/eap/reminder.html", email_context)
    email_type = "Approved EAP"
    send_notification(
        subject=email_subject,
        recipients=recipient,
        html=email_body,
        mailtype=email_type,
        cc_recipients=cc_recipients,
    )
    return email_context
