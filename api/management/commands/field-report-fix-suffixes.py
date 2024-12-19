import re

from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import FieldReport


class Command(BaseCommand):
    help = "Migrate legacy FieldReport data to populate fr_num"

    def handle(self, *args, **kwargs):
        suffix_pattern = re.compile(r"#(\d+)")
        reports = FieldReport.objects.filter(summary__icontains="#")
        self.stdout.write(f"Found {reports.count()} FieldReports to process.")

        # Dictionary to store highest fr_num for each event, country
        event_country_data = {}

        for report in reports:
            if not report.event or not report.countries.exists():
                self.stdout.write(f"Skipping report with ID {report.id} due to missing event or countries.")
                continue

            country = report.countries.first()

            summary_match = suffix_pattern.search(report.summary)
            derived_fr_num = int(summary_match.group(1)) if summary_match else None

            key = (report.event.id, country.id)

            # Initialize data for the event country group if not present
            if key not in event_country_data:
                event_country_data[key] = {
                    "highest_fr_num": 0,
                    "report_highest_fr": None,
                }

            group_data = event_country_data[key]
            max_fr_num = max(derived_fr_num or 0, report.fr_num or 0)

            # Update the group data if this report has the highest fr number
            if max_fr_num > group_data["highest_fr_num"]:
                self.stdout.write(f"Updating highest fr_num for group (event_id={report.event.id}, country_id={country.id})")
                group_data["highest_fr_num"] = max_fr_num
                group_data["report_highest_fr"] = report

        with transaction.atomic():
            for (event_id, country_id), data in event_country_data.items():
                highest_report = data["report_highest_fr"]
                highest_fr_num = data["highest_fr_num"]

                if highest_report:
                    highest_report.fr_num = highest_fr_num
                    highest_report.save(update_fields=["fr_num"])

                # Set fr_num to null for all other reports in the group
                FieldReport.objects.filter(event_id=event_id, countries=country_id).exclude(id=highest_report.id).update(
                    fr_num=None
                )

        self.stdout.write("Migration completed successfully.")
