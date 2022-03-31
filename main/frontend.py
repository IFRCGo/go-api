from django.conf import settings


def get_project_url(id):
    return f'https://{settings.FRONTEND_URL}/three-w/{id}/'


def get_flash_update_url(id):
    return f'https://{settings.FRONTEND_URL}/flash-update/{id}/'
