from django.conf import settings


def get_email_context(instance):
    from dref.serializers import DrefSerializer

    dref_data = DrefSerializer(instance).data
    email_context = {
        'id': dref_data['id'],
        'title': dref_data['title'],
        'frontend_url': settings.FRONTEND_URL,
    }
    return email_context
