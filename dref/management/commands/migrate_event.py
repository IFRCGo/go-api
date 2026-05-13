from django.core.management.base import BaseCommand

from api.models import Appeal, AppealType
from dref.models import Dref


class Command(BaseCommand):
    help = "Migrate related Event from Appeal to Dref"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting migration of events to Dref..."))

        appeal_event_map = {
            appeal.code: appeal.event
            for appeal in Appeal.objects.filter(
                atype=AppealType.DREF,
                event__isnull=False,
            ).exclude(code__isnull=True)
        }

        dref_queryset = Dref.objects.exclude(appeal_code__isnull=True)

        self.stdout.write(self.style.NOTICE(f"Found {dref_queryset.count()} Dref records with appeal codes."))

        drefs_to_update = []
        for dref in dref_queryset:
            event = appeal_event_map.get(dref.appeal_code)

            if not event:
                continue

            self.stdout.write(
                self.style.NOTICE(
                    f"Dref(id: {dref.id}, title: {dref.title}, code: {dref.appeal_code}) "
                    f"->"
                    f"Event(id: {event.id}, name: {event.name})"
                )
            )
            dref.event = event
            drefs_to_update.append(dref)

        Dref.objects.bulk_update(drefs_to_update, ["event"])

        self.stdout.write(self.style.SUCCESS(f"Successfully updated {len(drefs_to_update)} Dref records."))
