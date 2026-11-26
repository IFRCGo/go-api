from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand

from dref.models import DREF_FINAL_REPORT_DUE_MONTHS, Dref
from dref.utils import get_final_report_operation_end_date


class Command(BaseCommand):
    help = (
        "Recompute final_report_due_date for every Dref from its current end_date/approved "
        "Operational Update data (see dref.utils.get_final_report_operation_end_date). Useful "
        "after a change to the underlying due-date logic (e.g. switching what counts as an "
        "'approved' Operational Update) so existing rows reflect the new rules immediately, "
        "instead of waiting for their next unrelated save()."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report which Dref rows would change, without writing anything.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        updated_count = 0
        unchanged_count = 0

        for dref in Dref.objects.all().iterator():
            end_date = get_final_report_operation_end_date(dref)
            due_date = end_date + relativedelta(months=DREF_FINAL_REPORT_DUE_MONTHS) if end_date else None
            if due_date == dref.final_report_due_date:
                unchanged_count += 1
                continue

            updated_count += 1
            self.stdout.write(
                f"Dref id={dref.id} appeal_code={dref.appeal_code!r}: "
                f"final_report_due_date {dref.final_report_due_date} -> {due_date}"
            )
            if not dry_run:
                Dref.objects.filter(pk=dref.pk).update(final_report_due_date=due_date)

        action = "Would update" if dry_run else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} {updated_count} Dref row(s); {unchanged_count} already up to date."))
