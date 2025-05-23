import re

from django.core.management.base import BaseCommand
from django.db.models.expressions import Exists, OuterRef

from api.models import FieldReport
from main.managers import BulkUpdateManager


class Command(BaseCommand):
    help = "Migrate legacy FieldReport data to populate fr_num"

    def handle(self, *args, **kwargs):

        suffix_pattern = re.compile(r"#\s*(\d+)")

        reports = (
            FieldReport.objects.filter(event__isnull=False, countries__isnull=False, summary__icontains="#")
            .annotate(
                has_fr_num=Exists(
                    FieldReport.objects.filter(event=OuterRef("event"), countries=OuterRef("countries"), fr_num__isnull=False)
                )
            )
            .exclude(has_fr_num=True)
        )

        report_count = reports.count()
        self.stdout.write(self.style.NOTICE(f"Found {report_count} FieldReports to process"))

        if report_count == 0:
            self.stdout.write(self.style.WARNING("No FieldReports found to process"))
            return

        event_country_data = {}

        for report in reports.iterator():
            country = report.countries.first()

            if country is None:
                self.stdout.write(self.style.ERROR(f"FieldReport ID: ({report.id}) has no associated country."))
                continue

            summary_match = suffix_pattern.search(report.summary)
            derived_fr_num = int(summary_match.group(1)) if summary_match else 0

            max_fr_num = max(derived_fr_num, report.fr_num or 0)
            key = (report.event.id, country.id)

            group_data = event_country_data.get(
                key,
                {
                    "highest_fr_num": 0,
                    "report_highest_fr": None,
                },
            )

            if max_fr_num > group_data["highest_fr_num"]:
                group_data["highest_fr_num"] = max_fr_num
                group_data["report_highest_fr"] = report

            event_country_data[key] = group_data

        bulk_mgr = BulkUpdateManager(update_fields=["fr_num"])

        for data in event_country_data.values():
            highest_report = data["report_highest_fr"]
            highest_fr_num = data["highest_fr_num"]
            if highest_report:
                self.stdout.write(
                    self.style.NOTICE(f"Preparing to update FieldReport ID:({highest_report.id}) with fr_num:({highest_fr_num}).")
                )
                bulk_mgr.add(
                    FieldReport(
                        id=highest_report.id,
                        fr_num=highest_fr_num,
                    )
                )
        bulk_mgr.done()
        self.stdout.write(self.style.SUCCESS("FieldReport migration completed successfully."))
