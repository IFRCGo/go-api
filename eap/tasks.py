from datetime import datetime

from celery import shared_task
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from api.logger import logger
from api.playwright import render_pdf_from_url
from api.utils import generate_eap_export_url
from eap.models import EAPRegistration, EAPType, FullEAP, SimplifiedEAP
from main.utils import logger_context


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
