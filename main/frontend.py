from django.conf import settings


def get_project_url(id):
    return f"{settings.GO_WEB_URL}/three-w/projects/{id}/"


def get_flash_update_url(id):
    return f"https://{settings.GO_WEB_URL}/flash-updates/{id}/"
