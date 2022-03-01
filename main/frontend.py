from django.conf import settings


def get_project_url(id):
    return f'https://{settings.FRONTEND_URL}/three-w/{id}/'
