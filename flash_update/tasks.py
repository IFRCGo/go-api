from celery import shared_task

from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.contrib.auth.models import User

from notifications.notification import send_notification
from .models import Donors, FlashUpdate, FlashUpdateShare
from .utils import render_to_pdf, get_email_context


@shared_task
def share_flash_update(flash_update_share_id):
    instance = FlashUpdateShare.objects.get(id=flash_update_share_id)
    flash_update = instance.flash_update
    context_for_pdf = get_email_context(flash_update)
    if flash_update.extracted_at is None or flash_update.modified_at > flash_update.extracted_at:
        pdf = render_to_pdf('email/flash_update/flash_pdf.html', context_for_pdf)

        # save the generated pdf
        flash_update.extracted_file.save(pdf['filename'], ContentFile(pdf['file']))
        flash_update.extracted_at = timezone.now()
        flash_update.save(update_fields=('extracted_at',))

    # create url for pdf in email
    email_context = {
        'document_url': settings.BASE_URL + flash_update.extracted_file.url
    }
    donors_emails = instance.donors.all().values_list('email', flat=True)
    donor_groups_emails = Donors.objects.filter(
        groups__in=instance.donor_groups.all()
    ).values_list('email', flat=True)

    users_emails = set([*donors_emails, *donor_groups_emails])
    send_notification(
        f'Flash Update #{flash_update.id}',
        users_emails,
        render_to_string('email/flash_update/donor_email.html', email_context),
        'Flash Update',
    )
    return context_for_pdf


@shared_task
def send_flash_update_email(flash_update_id):
    instance = FlashUpdate.objects.get(id=flash_update_id)
    share_with_group = instance.share_with
    if instance.share_with is None:
        return

    email_context = get_email_context(instance)
    users_emails = User.objects.filter(
        groups__flash_email_subscription__share_with=share_with_group
    ).values_list('email', flat=True)
    if users_emails:
        send_notification(
            'Flash Update',
            users_emails,
            render_to_string('email/flash_update/flash_update.html', email_context),
            'Flash Update'
        )
    return email_context
