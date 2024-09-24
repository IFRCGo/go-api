from django.conf import settings

from api.models import CronJob, CronJobStatus


def ifrc_go(request):
    # cron_error = CronJob.objects.filter(status=CronJobStatus.ERRONEOUS).order_by("-id").first()
    return {
        # Provide a variable to define current environment
        "GO_ENVIRONMENT": settings.GO_ENVIRONMENT,
        # For maintenance mode:
        "DJANGO_READ_ONLY": settings.DJANGO_READ_ONLY,
        # For header /_!_\ error symbol in base_site.html
        # "HAVING_INGEST_ISSUE": True if cron_error else False,
        # "INGEST_ISSUE_ID": cron_error.id if cron_error else None,
    }
