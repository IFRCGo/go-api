from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from analytics.models import DocumentDownloadLog


class Command(BaseCommand):
    help = "Delete DocumentDownloadLog entries older than 6 months."

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=183)
        deleted, _ = DocumentDownloadLog.objects.filter(downloaded_at__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} document download log entries older than 6 months."))
