from datetime import datetime

from celery import shared_task
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework.authtoken.models import Token

from api.logger import logger
from api.playwright import render_pdf_from_url
from api.utils import generate_eap_export_url
from eap.models import EAPRegistration, EAPType, EmailRecipient, FullEAP, SimplifiedEAP
from eap.utils import (
    get_eap_email_context,
    get_eap_registration_email_context,
    get_emails_by_type,
    get_regional_coordinator_emails,
)
from main.utils import logger_context
from notifications.notification import send_notification


def build_filename(eap_registration: EAPRegistration) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    title = f"{eap_registration.national_society.name}-{eap_registration.disaster_type.name}"
    return f"EAP-{title}-({timestamp}).pdf"


@shared_task
def generate_eap_summary_pdf(eap_registration_id):
    eap_registration = EAPRegistration.objects.get(id=eap_registration_id)
    user = User.objects.get(id=eap_registration.created_by_id)
    token = Token.objects.filter(user=user).last()

    url = generate_eap_export_url(
        registration_id=eap_registration_id,
        summary=True,
    )

    logger.info(f"Starting EAP summary PDF generation: {eap_registration.pk}")
    try:
        file = render_pdf_from_url(
            url=url,
            user=user,
            token=token,
        )

        file_name = build_filename(eap_registration)
        eap_registration.summary_file.save(file_name, file)

        logger.info(f"EAP summary generation completed: {eap_registration.pk}")

    except Exception:
        logger.error(
            f"Failed to generate EAP summary PDF: {eap_registration.pk}",
            exc_info=True,
            extra=logger_context(
                dict(eap_registration_id=eap_registration.pk),
            ),
        )


@shared_task
def generate_export_diff_pdf(eap_registration_id, version):
    eap_registration = EAPRegistration.objects.get(id=eap_registration_id)
    user = User.objects.get(id=eap_registration.created_by_id)
    token = Token.objects.filter(user=user).last()

    url = generate_eap_export_url(
        registration_id=eap_registration_id,
        diff=True,
        version=version,
    )

    logger.info(f"Starting EAP diff PDF generation: {eap_registration.pk}")
    try:
        file = render_pdf_from_url(
            url=url,
            user=user,
            token=token,
        )

        file_name = build_filename(eap_registration)
        if eap_registration.eap_type == EAPType.SIMPLIFIED_EAP:
            simplified_eap = SimplifiedEAP.objects.filter(
                eap_registration=eap_registration,
                version=version,
            ).first()
            if not simplified_eap:
                raise ValueError("Simplified EAP version not found.")

            simplified_eap.diff_file.save(file_name, file)
        else:
            full_eap = FullEAP.objects.filter(
                eap_registration=eap_registration,
                version=version,
            ).first()
            if not full_eap:
                raise ValueError("Full EAP version not found.")

            full_eap.diff_file.save(file_name, file)

        logger.info(f"EAP diff generation completed: {eap_registration.pk}")

    except Exception:
        logger.error(
            f"Failed to generate EAP diff PDF: {eap_registration.pk}",
            exc_info=True,
            extra=logger_context(
                dict(eap_registration_id=eap_registration.pk),
            ),
        )


@shared_task
def generate_export_eap_pdf(eap_registration_id, version):
    eap_registration = EAPRegistration.objects.get(id=eap_registration_id)
    user = User.objects.get(id=eap_registration.created_by_id)
    token = Token.objects.filter(user=user).last()
    url = generate_eap_export_url(
        registration_id=eap_registration_id,
        version=version,
    )

    logger.info(f"Starting EAP export PDF generation: {eap_registration.pk}")
    try:
        file = render_pdf_from_url(
            url=url,
            user=user,
            token=token,
        )

        file_name = build_filename(eap_registration)
        if eap_registration.eap_type == EAPType.SIMPLIFIED_EAP:
            simplified_eap = SimplifiedEAP.objects.filter(
                eap_registration=eap_registration,
                version=version,
            ).first()
            if not simplified_eap:
                raise ValueError("Simplified EAP version not found.")

            simplified_eap.export_file.save(file_name, file)
        else:
            full_eap = FullEAP.objects.filter(
                eap_registration=eap_registration,
                version=version,
            ).first()
            if not full_eap:
                raise ValueError("Full EAP version not found.")

            full_eap.export_file.save(file_name, file)

        logger.info(f"EAP export generation completed: {eap_registration.pk}")

    except Exception:
        logger.error(
            f"Failed to generate EAP export PDF: {eap_registration.pk}",
            exc_info=True,
            extra=logger_context(
                dict(eap_registration_id=eap_registration.pk),
            ),
        )


@shared_task
def send_new_eap_registration_email(eap_registration_id: int):
    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None

    regional_coordinator_emails: list[str] = get_regional_coordinator_emails(instance.country.region)

    recipients = [
        *get_emails_by_type(EmailRecipient.EmailType.DREF_ANTICIPATORY),
        instance.ifrc_contact_email,
    ]
    cc_recipients = list(
        set(
            [
                instance.national_society_contact_email,
                *get_emails_by_type(EmailRecipient.EmailType.DREF_AA_GLOBAL_TEAM),
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
    return True


@shared_task
def send_new_eap_submission_email(eap_registration_id: int):
    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None

    if instance.get_eap_type_enum == EAPType.SIMPLIFIED_EAP:
        latest_eap = instance.latest_simplified_eap
    else:
        latest_eap = instance.latest_full_eap

    partner_ns_emails = list(latest_eap.partner_contacts.values_list("email", flat=True))

    regional_coordinator_emails: list[str] = get_regional_coordinator_emails(instance.country.region)

    recipients = [
        *get_emails_by_type(EmailRecipient.EmailType.DREF_ANTICIPATORY),
        instance.ifrc_contact_email,
    ]
    cc_recipients = list(
        set(
            [
                instance.national_society_contact_email,
                *get_emails_by_type(EmailRecipient.EmailType.DREF_AA_GLOBAL_TEAM),
                *regional_coordinator_emails,
                *partner_ns_emails,
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
    return True


@shared_task
def send_feedback_email(eap_registration_id: int):
    instance: EAPRegistration | None = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None

    if instance.get_eap_type_enum == EAPType.SIMPLIFIED_EAP:
        latest_eap = instance.latest_simplified_eap
    else:
        latest_eap = instance.latest_full_eap

    ifrc_delegation_focal_point_email = latest_eap.ifrc_delegation_focal_point_email

    partner_ns_emails = list(latest_eap.partner_contacts.values_list("email", flat=True))

    regional_coordinator_emails: list[str] = get_regional_coordinator_emails(instance.country.region)

    recipient = [
        instance.national_society_contact_email,
    ]

    cc_recipients = list(
        set(
            [
                ifrc_delegation_focal_point_email,
                *get_emails_by_type(EmailRecipient.EmailType.DREF_ANTICIPATORY),
                *get_emails_by_type(EmailRecipient.EmailType.DREF_AA_GLOBAL_TEAM),
                *regional_coordinator_emails,
                *partner_ns_emails,
            ]
        )
    )
    email_context = get_eap_email_context(instance)
    email_subject = (
        f"[DREF {instance.get_eap_type_display()} FEEDBACK] "
        f"{instance.country} {instance.disaster_type} TO THE {instance.national_society.society_name}"
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

    return True


@shared_task
def send_eap_resubmission_email(eap_registration_id: int):
    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None
    if instance.get_eap_type_enum == EAPType.SIMPLIFIED_EAP:
        latest_eap = instance.latest_simplified_eap
    else:
        latest_eap = instance.latest_full_eap

    partner_ns_emails = list(latest_eap.partner_contacts.values_list("email", flat=True))
    regional_coordinator_emails: list[str] = get_regional_coordinator_emails(instance.country.region)

    recipients = [
        *get_emails_by_type(EmailRecipient.EmailType.DREF_ANTICIPATORY),
        instance.ifrc_contact_email,
    ]

    cc_recipients = list(
        set(
            [
                instance.national_society_contact_email,
                *get_emails_by_type(EmailRecipient.EmailType.DREF_AA_GLOBAL_TEAM),
                *regional_coordinator_emails,
                *partner_ns_emails,
            ]
        )
    )
    email_context = get_eap_email_context(instance)
    email_subject = (
        f"[DREF {instance.get_eap_type_display()} FOR REVIEW] "
        f"{instance.country} {instance.disaster_type} version {latest_eap.version} TO THE IFRC-DREF"
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
    return True


@shared_task
def send_feedback_email_for_resubmitted_eap(eap_registration_id: int):
    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None

    if instance.get_eap_type_enum == EAPType.SIMPLIFIED_EAP:
        latest_eap = instance.latest_simplified_eap
    else:
        latest_eap = instance.latest_full_eap

    partner_ns_emails = list(latest_eap.partner_contacts.values_list("email", flat=True))

    regional_coordinator_emails: list[str] = get_regional_coordinator_emails(instance.country.region)

    recipients = [
        instance.national_society_contact_email,
    ]

    cc_recipients = list(
        set(
            [
                *get_emails_by_type(EmailRecipient.EmailType.DREF_ANTICIPATORY),
                *get_emails_by_type(EmailRecipient.EmailType.DREF_AA_GLOBAL_TEAM),
                *regional_coordinator_emails,
                *partner_ns_emails,
            ]
        )
    )
    email_context = get_eap_email_context(instance)
    email_subject = (
        f"[DREF {instance.get_eap_type_display()} FEEDBACK] "
        f"{instance.country} {instance.disaster_type} version {latest_eap.version} TO {instance.national_society.society_name}"
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

    return True


@shared_task
def send_technical_validation_email(eap_registration_id: int):

    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None

    partner_contacts = (
        instance.latest_simplified_eap.partner_contacts
        if instance.get_eap_type_enum == EAPType.SIMPLIFIED_EAP
        else instance.latest_full_eap.partner_contacts
    )

    partner_ns_emails = list(partner_contacts.values_list("email", flat=True))

    regional_coordinator_emails: list[str] = get_regional_coordinator_emails(instance.country.region)

    recipient = [
        instance.national_society_contact_email,
    ]

    cc_recipients = list(
        set(
            [
                *get_emails_by_type(EmailRecipient.EmailType.DREF_ANTICIPATORY),
                *get_emails_by_type(EmailRecipient.EmailType.DREF_AA_GLOBAL_TEAM),
                *regional_coordinator_emails,
                *partner_ns_emails,
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
    return True


@shared_task
def send_pending_pfa_email(eap_registration_id: int):

    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None

    is_full_eap = instance.get_eap_type_enum == EAPType.FULL_EAP

    latest_eap = instance.latest_full_eap if is_full_eap else instance.latest_simplified_eap
    partner_ns_emails = list(latest_eap.partner_contacts.values_list("email", flat=True))

    regional_coordinator_emails: list[str] = get_regional_coordinator_emails(instance.country.region)

    recipient = [
        instance.national_society_contact_email,
    ]

    cc_recipients = list(
        set(
            [
                *get_emails_by_type(EmailRecipient.EmailType.DREF_ANTICIPATORY),
                *get_emails_by_type(EmailRecipient.EmailType.DREF_AA_GLOBAL_TEAM),
                *regional_coordinator_emails,
                *partner_ns_emails,
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
    return True


@shared_task
def send_approved_email(eap_registration_id: int):

    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None

    partner_contacts = (
        instance.latest_simplified_eap.partner_contacts
        if instance.get_eap_type_enum == EAPType.SIMPLIFIED_EAP
        else instance.latest_full_eap.partner_contacts
    )

    partner_ns_emails = list(partner_contacts.values_list("email", flat=True))
    regional_coordinator_emails: list[str] = get_regional_coordinator_emails(instance.country.region)

    recipient = [
        instance.national_society_contact_email,
    ]

    cc_recipients = list(
        set(
            [
                *get_emails_by_type(EmailRecipient.EmailType.DREF_ANTICIPATORY),
                *get_emails_by_type(EmailRecipient.EmailType.DREF_AA_GLOBAL_TEAM),
                *regional_coordinator_emails,
                *partner_ns_emails,
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
    return True


@shared_task
def send_deadline_reminder_email(eap_registration_id: int):

    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance:
        return None

    partner_contacts = (
        instance.latest_simplified_eap.partner_contacts
        if instance.get_eap_type_enum == EAPType.SIMPLIFIED_EAP
        else instance.latest_full_eap.partner_contacts
    )

    partner_ns_emails = list(partner_contacts.values_list("email", flat=True))

    regional_coordinator_emails: list[str] = get_regional_coordinator_emails(instance.country.region)

    recipient = [
        instance.national_society_contact_email,
    ]

    cc_recipients = list(
        set(
            [
                *get_emails_by_type(EmailRecipient.EmailType.DREF_ANTICIPATORY),
                *get_emails_by_type(EmailRecipient.EmailType.DREF_AA_GLOBAL_TEAM),
                *regional_coordinator_emails,
                *partner_ns_emails,
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
    instance.deadline_remainder_sent_at = timezone.now()
    instance.save(update_fields=["deadline_remainder_sent_at"])

    return True


@shared_task
def send_eap_share_email(eap_registration_id: int, recipient_emails: list[str]):
    instance = EAPRegistration.objects.filter(id=eap_registration_id).first()
    if not instance or not recipient_emails:
        return None

    email_context = get_eap_registration_email_context(instance)
    email_subject = f"EAP shared: {instance.country} {instance.disaster_type}"
    email_body = render_to_string("email/eap/share_eap.html", email_context)
    email_type = "Shared EAP"

    send_notification(
        subject=email_subject,
        recipients=recipient_emails,
        html=email_body,
        mailtype=email_type,
    )
    return True
