import logging
from io import BytesIO

from django.template.loader import render_to_string

from xhtml2pdf import pisa

from main.frontend import get_flash_update_url

from flash_update.models import FlashGraphicMap

logger = logging.getLogger(__name__)


def render_to_pdf(template_src, context_dict={}):
    html = render_to_string(template_src, context_dict)
    result = BytesIO()
    try:
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
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
            'image': item.file.url,
            'caption': item.caption,
        }
        for item in data
    ]


def get_email_context(instance):
    from flash_update.serializers import FlashUpdateSerializer

    flash_update_data = FlashUpdateSerializer(instance).data
    map_data = FlashGraphicMap.objects.filter(flash_map=instance)
    graphics_data = FlashGraphicMap.objects.filter(flash_graphics=instance)
    map_list = generate_file_data(map_data)
    graphics_list = generate_file_data(graphics_data)
    actions_taken = [dict(action_taken) for action_taken in flash_update_data['actions_taken']]
    resources = [dict(refrence) for refrence in flash_update_data['references']]
    email_context = {
        'resource_url': get_flash_update_url(instance.id),
        'title': flash_update_data['title'],
        'situational_overview': flash_update_data['situational_overview'],
        'map_list': map_list,
        'graphic_list': graphics_list,
        'actions_taken': actions_taken,
        'resources': resources,
    }
    return email_context
