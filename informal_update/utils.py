from io import BytesIO
from django.conf import settings
from django.template.loader import render_to_string

from xhtml2pdf import pisa


def render_to_pdf(template_src, context_dict={}):
    html = render_to_string(template_src, context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        file = {
            'filename': 'informal_update.pdf',
            'file': result.getvalue()
        }
        return file
    return None


def generate_file_data(data, list):
    for file in data:
        file_dict = dict()
        if file['file']:
            file_url = settings.BASE_URL + file['file']
            file_dict['image'] = file_url
        file_dict['caption'] = file['caption']
        list.append(file_dict)
