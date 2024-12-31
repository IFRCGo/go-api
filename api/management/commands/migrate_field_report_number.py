import logging
import os
import re

import psutil
from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from api.models import FieldReport
from main.managers import BulkUpdateManager

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Migrate legacy FieldReport data to populate fr_num"

    def handle(self, *args, **kwargs):
        suffix_pattern = re.compile(r"#(\d+)")

        event_country_filter_qs = (
            FieldReport.objects.order_by()
            .values("event", "countries")
            .annotate(count=Count("id", filter=Q(fr_num__isnull=True)))
            .exclude(count__gte=1)
        )

        reports = FieldReport.objects.filter(
            event__in=event_country_filter_qs.values("event"),
            countries__in=event_country_filter_qs.values("countries"),
        ).distinct()

        # reports = FieldReport.objects.filter(fr_num__isnull=True).select_related('event').distinct()
        logger.info(f"Found {reports.count()} FieldReports to process.")

        if not reports:
            logger.warning("No FieldReports found.")
            return

        event_country_data = {}

        for report in reports.iterator():
            country = report.countries.first()

            summary_match = suffix_pattern.search(report.summary)
            derived_fr_num = int(summary_match.group(1)) if summary_match else None
            key = (report.event.id, country.id)

            # Initialize or retrieve group data
            group_data = event_country_data[key] = event_country_data.get(
                key,
                {
                    "highest_fr_num": 0,
                    "report_highest_fr": None,
                },
            )

            max_fr_num = max(derived_fr_num or 0, report.fr_num or 0)

            if max_fr_num > group_data["highest_fr_num"]:
                group_data["highest_fr_num"] = max_fr_num
                group_data["report_highest_fr"] = report

        bulk_manager = BulkUpdateManager(update_fields=["fr_num"])

        for (event_id, country_id), data in event_country_data.items():
            highest_report = data["report_highest_fr"]
            highest_fr_num = data["highest_fr_num"]

            if highest_report:
                logger.debug(f"Preparing to update FieldReport ID {highest_report.id} with fr_num {highest_fr_num}.")
                highest_report.fr_num = highest_fr_num
                bulk_manager._process_obj(highest_report)
        bulk_manager._commit

        process = psutil.Process(os.getpid())

        memory_usage = process.memory_info().rss / (1024 * 1024)
        logger.info(f"Memory usage:{memory_usage} MB")

        logger.info("FieldReport migration completed successfully.")
