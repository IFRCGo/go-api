from django import template
from django.conf import settings
from django.core.files.storage import FileSystemStorage, storages
from django.templatetags.static import static

register = template.Library()


@register.filter(is_safe=True)
def static_full_path(path):
    static_path = static(path)
    # XXX: Using this as the static files are stored locally, not in separate storage (e.g. S3, Blob)
    if isinstance(storages["staticfiles"], FileSystemStorage):
        return f"{settings.GO_API_URL}{static_path}"
    return static_path
