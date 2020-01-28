from django.conf import settings
from api.models import CronJob, CronJobStatus


def ifrc_go(request):
    having_ingest_issue = CronJob.objects.raw('SELECT * FROM api_cronjob WHERE status=' + str(CronJobStatus.ERRONEOUS.value))
    ingest_issue_id = having_ingest_issue[0].id if len(having_ingest_issue) > 0 else -1
    return {
        # Provide a variable to define current environment
        'PRODUCTION_URL': settings.PRODUCTION_URL,
        'IS_STAGING': True if settings.PRODUCTION_URL == 'dsgocdnapi.azureedge.net' else False,
        'HAVING_INGEST_ISSUE': True if len(having_ingest_issue) > 0 else False,
        'INGEST_ISSUE_ID': ingest_issue_id,
    }
