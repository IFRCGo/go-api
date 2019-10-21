from django.conf import settings


def ifrc_go(request):
    return {
        # Provide a variable to define current environment
        'PRODUCTION_URL': settings.PRODUCTION_URL,
    }
