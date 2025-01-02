import re

from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from api.models import FieldReport
from main.managers import BulkUpdateManager


class Command(BaseCommand):
    help = "Migrate legacy FieldReport data to populate fr_num"

    def handle(self, *args, **kwargs):

        suffix_pattern = re.compile(r"#(\d+)")

        event_country_filter_qs = FieldReport.objects.values("event", "countries").annotate(
            count=Count("id", filter=Q(fr_num__isnull=True))
        )
        reports = (
            FieldReport.objects.filter(
                event__in=event_country_filter_qs.values("event"),
                countries__in=event_country_filter_qs.values("countries"),
            )
            .distinct()
            .select_related("event")
            .prefetch_related("countries")
        )

        self.stdout.write(f"Found {reports.count()} FieldReports to process.")

        if not reports:
            self.stdout.write("No FieldReports found to migrate.")
            return

        event_country_data = {}

        for report in reports.iterator():
            country = report.countries.first()

            if country is None:
                self.stdout.write(f"FieldReport ID {report.rid} has no associated country.")
                continue

            summary_match = suffix_pattern.search(report.summary)
            derived_fr_num = int(summary_match.group(1)) if summary_match else None

            max_fr_num = max(derived_fr_num or 0, report.fr_num or 0)
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

        for (event_id, country_id), data in event_country_data.items():
            highest_report = data["report_highest_fr"]
            highest_fr_num = data["highest_fr_num"]
            if highest_report:
                self.stdout.write(f"Preparing to update FieldReport ID {highest_report.id} with fr_num {highest_fr_num}.")
                highest_report.fr_num = highest_fr_num
                bulk_mgr.add(
                    FieldReport(
                        id=highest_report.id,
                        fr_num=highest_fr_num,
                    )
                )
        bulk_mgr.done()

        self.stdout.write("FieldReport migration completed successfully.")
