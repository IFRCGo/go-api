from django.core.management.base import BaseCommand

from api.models import Appeal, AppealType
from dref.models import Dref, DrefFinalReport, DrefOperationalUpdate


class Command(BaseCommand):
    help = "Migrate related Event from Appeal / Dref Final / Operational Update to Dref"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting migration of events to Dref..."))

        appeal_map = dict(
            Appeal.objects.filter(
                atype=AppealType.DREF,
                event__isnull=False,
            )
            .exclude(code__isnull=True)
            .values_list("code", "id")
        )

        appeal_event_map = dict(
            Appeal.objects.filter(
                atype=AppealType.DREF,
                event__isnull=False,
            )
            .exclude(code__isnull=True)
            .values_list("code", "event_id")
        )

        final_report_map = dict(DrefFinalReport.objects.exclude(appeal_code__isnull=True).values_list("appeal_code", "id"))

        operational_update_map = dict(
            DrefOperationalUpdate.objects.exclude(appeal_code__isnull=True).values_list("appeal_code", "id")
        )

        dref_queryset = Dref.objects.only("id", "title", "appeal_code", "event_id")

        self.stdout.write(self.style.NOTICE(f"Found {dref_queryset.count()} Dref records"))
        self.stdout.write(self.style.NOTICE("\nMigrating Dref Event Mapping"))

        drefs_to_update = []

        for dref in dref_queryset.iterator():
            code = dref.appeal_code

            self.stdout.write(self.style.NOTICE(f"\nDref: {dref.title} (id={dref.id})"))

            new_event_id = None
            matched_with = None

            appeal_id = None
            final_id = None
            op_id = None

            self.stdout.write(self.style.NOTICE("\tChecking Appeal"))

            if code:
                appeal_id = appeal_map.get(code)
                new_event_id = appeal_event_map.get(code)

            if new_event_id:
                matched_with = f"APPEAL (id:{appeal_id})"
                self.stdout.write(self.style.SUCCESS(f"\t\tMatched with Appeal (id:{appeal_id})"))
            else:
                self.stdout.write(self.style.WARNING("\t\tNo match in Appeal"))

            if not new_event_id:
                self.stdout.write(self.style.NOTICE("\tChecking Final Report"))

                final_id = final_report_map.get(code)

                if final_id:
                    new_event_id = appeal_event_map.get(code)
                    if new_event_id:
                        matched_with = f"DREF FINAL REPORT (id:{final_id})"
                        self.stdout.write(self.style.SUCCESS(f"\t\tMatched with Final Report (id:{final_id})"))
                else:
                    self.stdout.write(self.style.WARNING("\t\tNo match in Final Report"))

            if not new_event_id:
                self.stdout.write(self.style.NOTICE("\tChecking Operational Update"))

                op_id = operational_update_map.get(code)

                if op_id:
                    new_event_id = appeal_event_map.get(code)
                    if new_event_id:
                        matched_with = f"DREF OPERATIONAL UPDATE (id:{op_id})"
                        self.stdout.write(self.style.SUCCESS(f"\t\tMatched with Operational Update (id:{op_id})"))
                else:
                    self.stdout.write(self.style.WARNING("\t\tNo match in Operational Update"))

            if not new_event_id:
                self.stdout.write(self.style.WARNING("\tNo matching event found"))
                continue

            if dref.event_id and dref.event_id != new_event_id:
                self.stdout.write(
                    self.style.WARNING(f"\tConflict: existing_event_id={dref.event_id}, new_event_id={new_event_id} (skipped)")
                )
                continue

            dref.event_id = new_event_id
            drefs_to_update.append(dref)

            self.stdout.write(self.style.SUCCESS(f"\tUpdating event using {matched_with}"))

        Dref.objects.bulk_update(drefs_to_update, ["event_id"])

        self.stdout.write(self.style.SUCCESS(f"\nSuccessfully updated {len(drefs_to_update)} Dref records\n"))
