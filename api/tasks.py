from datetime import datetime

from celery import shared_task
from django.contrib.auth.models import User
from django.core import management
from django.utils import timezone
from rest_framework.authtoken.models import Token

from api.playwright import render_pdf_from_url
from main.lock import RedisLockKey, redis_lock
from main.utils import logger_context

from .logger import logger
from .models import Export


def build_export_filename(export: Export, title: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")

    prefix_map = {
        Export.ExportType.PER: "PER",
        Export.ExportType.SIMPLIFIED_EAP: "SIMPLIFIED EAP",
        Export.ExportType.FULL_EAP: "FULL EAP",
    }

    prefix = prefix_map.get(export.export_type, "DREF")
    return f"{prefix} {title} ({timestamp}).pdf"


@shared_task
def generate_export_pdf(export_id, title, set_user_language="en"):
    export = Export.objects.get(id=export_id)
    user = User.objects.get(id=export.requested_by.id)
    token = Token.objects.filter(user=user).last()
    logger.info(f"Starting export: {export.pk}")

    try:
        file = render_pdf_from_url(
            url=export.url,
            user=user,
            token=token,
            language=set_user_language,
        )

        file_name = build_export_filename(export, title)
        export.pdf_file.save(file_name, file)
        export.status = Export.ExportStatus.COMPLETED
        export.completed_at = timezone.now()
        export.save(
            update_fields=[
                "status",
                "completed_at",
            ]
        )
    except Exception:
        logger.error(
            f"Failed to export PDF: {export.export_type}",
            exc_info=True,
            extra=logger_context(dict(export_id=export.pk)),
        )
        export.status = Export.ExportStatus.ERRORED
        export.save(update_fields=["status"])
    logger.info(f"End export: {export.pk}")


# TODO(susilnem): Do we need this cron?
@shared_task
def clear_expired_django_sessions():
    """Purge expired django_session rows -- nothing else prunes them."""
    with redis_lock(RedisLockKey.CLEAR_EXPIRED_DJANGO_SESSIONS) as acquired:
        if not acquired:
            logger.warning("clear_expired_django_sessions: already running, skipping")
            return
        management.call_command("clearsessions", verbosity=0)


@shared_task
def celery_queue_uptime_check(queue: str) -> None:
    """No-op heartbeat proving beat dispatches and that `queue` has a consumer."""
    logger.info("Celery queue '%s' is taking tasks", queue)
