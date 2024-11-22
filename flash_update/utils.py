import logging
from io import BytesIO

from django.template.loader import render_to_string
from xhtml2pdf import pisa

from flash_update.models import FlashGraphicMap
from main.frontend import get_flash_update_url

logger = logging.getLogger(__name__)


def render_to_pdf(template_src, context_dict={}):
    html = render_to_string(template_src, context_dict)
    result = BytesIO()
    try:
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        if not pdf.err:
            file = {"filename": "flash_update.pdf", "file": result.getvalue()}
            return file
    except Exception:
        logger.error("Error in rendering html to pdf", exc_info=True)
        return None


def generate_file_data(data):
    return [
        {
            "image": item.file.url,
            "caption": item.caption,
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
    actions_taken = [dict(action_taken) for action_taken in flash_update_data["actions_taken"]]
    resources = [dict(reference) for reference in flash_update_data["references"]]
    documents_map = {
        document.id: document.file.url
        for document in FlashGraphicMap.objects.filter(id__in=[resource["document"] for resource in resources]).only("id", "file")
    }
    for resource in resources:
        resource["flash_file"] = documents_map.get(resource["document"])

    email_context = {
        "resource_url": get_flash_update_url(instance.id),
        "title": flash_update_data["title"],
        "situational_overview": flash_update_data["situational_overview"],
        "map_list": map_list,
        "graphic_list": graphics_list,
        "actions_taken": actions_taken,
        "resources": resources,
    }
    email_context = {key: value for key, value in email_context.items() if value is not None}
    return email_context
