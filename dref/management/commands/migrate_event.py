from django.core.management.base import BaseCommand

from api.models import Appeal, AppealType
from dref.models import Dref


class Command(BaseCommand):
    help = "Migrate related Event to Dref"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting migration of events to Dref..."))

        appeal_qs = Appeal.objects.filter(atype=AppealType.DREF).exclude(code__isnull=True)

        appeal_map = {appeal.code: appeal.event for appeal in appeal_qs if appeal.event}

        drefs = Dref.objects.exclude(appeal_code__isnull=True)
        self.stdout.write(self.style.NOTICE(f"Total Dref records with appeal code:{drefs.count()}"))
        count = 0

        for dref in drefs:
            event_id = appeal_map.get(dref.appeal_code)
            if event_id:
                dref.event = event_id
                count += 1

        Dref.objects.bulk_update(drefs, ["event"])
        self.stdout.write(self.style.SUCCESS(f"Updated {count} Dref records with related Event"))
