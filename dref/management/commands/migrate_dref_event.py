from django.core.management.base import BaseCommand
from django.db.models import Case, IntegerField, Value, When

from api.models import Appeal, AppealType
from dref.models import Dref, DrefFinalReport, DrefOperationalUpdate


class Command(BaseCommand):
    help = "Migrate related Event from Appeal / Dref Final / Operational Update to Dref"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting migration of events to Dref..."))

        appeal_event_map = dict(
            Appeal.objects.filter(
                atype=AppealType.DREF,
                event__isnull=False,
            )
            .exclude(code__isnull=True)
            .values_list("code", "event_id")
        )

        final_report_map = dict(
            DrefFinalReport.objects.exclude(appeal_code__isnull=True)
            .annotate(
                approval_priority=Case(
                    When(status=Dref.Status.APPROVED, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )
            .order_by("dref_id", "approval_priority")
            .distinct("dref_id")
            .values_list("dref_id", "appeal_code")
        )

        operational_update_map = dict(
            DrefOperationalUpdate.objects.exclude(appeal_code__isnull=True)
            .annotate(
                approval_priority=Case(
                    When(status=Dref.Status.APPROVED, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )
            .order_by("dref_id", "approval_priority", "-created_at")
            .distinct("dref_id")
            .values_list("dref_id", "appeal_code")
        )

        dref_queryset = Dref.objects.only("id", "title", "appeal_code", "event_id")
        self.stdout.write(self.style.NOTICE("\nMigrating Dref Event Mapping"))

        drefs_to_update = []
        for dref in dref_queryset.iterator():
            self.stdout.write(self.style.NOTICE(f"\nDref: {dref.title} (id={dref.id})"))

            appeal_code = None
            matched_with = None

            self.stdout.write(self.style.NOTICE("\tChecking Final Report"))
            if final_report_map.get(dref.id):
                appeal_code = final_report_map[dref.id]
                matched_with = "DREF FINAL REPORT"
                self.stdout.write(self.style.SUCCESS(f"\t\tFound appeal_code from Final Report ({appeal_code})"))
            else:
                self.stdout.write(self.style.WARNING("\t\tNo appeal_code in Final Report"))

            if not appeal_code:
                self.stdout.write(self.style.NOTICE("\tChecking Operational Update"))
                if operational_update_map.get(dref.id):
                    appeal_code = operational_update_map[dref.id]
                    matched_with = "DREF OPERATIONAL UPDATE"
                    self.stdout.write(self.style.SUCCESS(f"\t\tFound appeal_code from Operational Update ({appeal_code})"))
                else:
                    self.stdout.write(self.style.WARNING("\t\tNo appeal_code in Operational Update"))

            if not appeal_code:
                self.stdout.write(self.style.NOTICE("\tChecking Dref"))
                if dref.appeal_code:
                    appeal_code = dref.appeal_code
                    matched_with = "DREF"
                    self.stdout.write(self.style.SUCCESS(f"\t\tFound appeal_code from Dref ({appeal_code})"))
                else:
                    self.stdout.write(self.style.WARNING("\t\tNo appeal_code in Dref"))

            if not appeal_code:
                self.stdout.write(self.style.WARNING("\tNo appeal_code found, skipping..."))
                continue

            new_event_id = appeal_event_map.get(appeal_code)
            if not new_event_id:
                self.stdout.write(self.style.WARNING(f"\tNo matching Appeal found for appeal_code={appeal_code}, skipping..."))
                continue

            if dref.event_id and dref.event_id != new_event_id:
                self.stdout.write(
                    self.style.WARNING(f"\tConflict: existing_event_id={dref.event_id}, new_event_id={new_event_id} (skipped)")
                )
                continue

            dref.event_id = new_event_id
            drefs_to_update.append(dref)
            self.stdout.write(self.style.SUCCESS(f"\tUpdating event_id={new_event_id} using {matched_with}"))

        Dref.objects.bulk_update(drefs_to_update, ["event_id"])
        self.stdout.write(self.style.SUCCESS(f"\nSuccessfully updated {len(drefs_to_update)} Dref records\n"))
