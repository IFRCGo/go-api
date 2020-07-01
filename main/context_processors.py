from django.conf import settings
from api.models import CronJob, CronJobStatus


def ifrc_go(request):
    cron_error = CronJob.objects.filter(status=CronJobStatus.ERRONEOUS).order_by('-id').first()
    return {
        # Provide a variable to define current environment
        'PRODUCTION_URL': settings.PRODUCTION_URL,
        'HIDE_LANGUAGE_UI': settings.HIDE_LANGUAGE_UI,
        'IS_STAGING': True if settings.PRODUCTION_URL == 'dsgocdnapi.azureedge.net' else False,
        # For header /_!_\ error symbol in base_site.html
        'HAVING_INGEST_ISSUE': True if cron_error else False,
        'INGEST_ISSUE_ID': cron_error.id if cron_error else None,
    }
