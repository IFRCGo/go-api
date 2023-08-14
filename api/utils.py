import base64
from django.utils.translation import gettext
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
        raise ValidationError(gettext('slug should not start with a number'))


def is_user_ifrc(user):
    """ Checks if the user has IFRC Admin or superuser permissions """
    if user.has_perm('api.ifrc_admin') or user.is_superuser:
        return True
    return False

# FIXME: not usable because of circular dependency
# def filter_visibility_by_auth(user, visibility_model_class):
#     if user.is_authenticated:
#         if is_user_ifrc(user):
#             return visibility_model_class.objects.all()
#         else:
#             return visibility_model_class.objects.exclude(visibility=VisibilityChoices.IFRC)
#     return visibility_model_class.objects.filter(visibility=VisibilityChoices.PUBLIC)


def get_model_name(model):
    return f'{model._meta.app_label}.{model.__name__}'


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value
