import base64
from django.core.exceptions import ValidationError

def pretty_request(request):
    headers = ''
    for header, value in request.META.items():
        if not header.startswith('HTTP'):
            continue
        header = '-'.join([h.capitalize() for h in header[5:].lower().split('_')])
        headers += '{}: {}\n'.format(header, value)

    return (
        '{method} HTTP/1.1\n'
        'Content-Length: {content_length}\n'
        'Content-Type: {content_type}\n'
        '{headers}\n\n'
        '{body}'
    ).format(
        method=request.method,
        content_length=request.META['CONTENT_LENGTH'],
        content_type=request.META['CONTENT_TYPE'],
        headers=headers,
        body=request.body,
    )


def base64_encode(string):
    return base64.urlsafe_b64encode(
        string.encode('UTF-8')
    ).decode('ascii')

def validate_slug_number(value):
    if value[0].isdigit():
        raise ValidationError('slug should not start with a number')
