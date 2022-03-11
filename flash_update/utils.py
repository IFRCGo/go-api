import logging
from io import BytesIO

from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.contrib.auth.models import User

from xhtml2pdf import pisa

from notifications.notification import send_notification
from main.frontend import get_project_url
from .models import Donors

logger = logging.getLogger(__name__)


def render_to_pdf(template_src, context_dict={}):
    html = render_to_string(template_src, context_dict)
    result = BytesIO()
    try:
        pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
        if not pdf.err:
            file = {
                'filename': 'flash_update.pdf',
                'file': result.getvalue()
            }
            return file
    except Exception as e:
        logger.error('Error in rendering html to pdf', exc_info=True)
        return None


def generate_file_data(data):
    return [
        {
            'image': item.get('file') and (settings.BASE_URL + item['file']),
            'caption': item['caption'],
        }
        for item in data
    ]


def get_email_context(instance):
    from flash_update.serializers import FlashUpdateSerializer

    flash_update_data = FlashUpdateSerializer(instance).data
    map_list = generate_file_data(flash_update_data['map_files'])
    graphics_list = generate_file_data(flash_update_data['graphics_files'])
    actions_taken = [dict(action_taken) for action_taken in flash_update_data['actions_taken']]
    resources = [dict(refrence) for refrence in flash_update_data['references']]
    email_context = {
        'resource_url': get_project_url(instance.id),
        'title': flash_update_data['title'],
        'situational_overview': flash_update_data['situational_overview'],
        'map_list': map_list,
        'graphic_list': graphics_list,
        'actions_taken': actions_taken,
        'resources': resources,
        'document_url': flash_update_data['extracted_file']
    }
    return email_context


def send_flash_update_email(instance):
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


def share_flash_update(instance):
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

