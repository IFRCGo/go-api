from django import template
from django.conf import settings
from django.core.files.storage import FileSystemStorage, get_storage_class

register = template.Library()

StorageClass = get_storage_class()


@register.filter(is_safe=True)
def media_full_path(path):
    # TODO: Refactor http and https
    # NOTE: This should point to the goadmin FullURL
    if StorageClass == FileSystemStorage:
        if settings.DEBUG:
            return f"http://serve:8000{path}"
        return f"https://{settings.BASE_URL}{path}"
    return path
