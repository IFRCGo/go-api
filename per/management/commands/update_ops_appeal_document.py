from django.core.management.base import BaseCommand
from api.models import AppealDocumentType, AppealDocument
from per.models import OpsLearning


class Command(BaseCommand):
    help = "Update appeal_document_id in OpsLearning using Final report AppealDocument"

    def handle(self, *args, **kwargs):
        final_report_type = AppealDocumentType.objects.filter(
            name__iexact="Final Report"
        ).first()

        if not final_report_type:
            self.stderr.write(
                self.style.ERROR(
                    "AppealDocumentType with name 'Final report' not found."
                )
            )
            return

        ops_learnings = OpsLearning.objects.filter(
            is_validated=True,
            appeal_code__isnull=False,
        )

        updated = 0
        skipped = 0

        for ops in ops_learnings:
            appeal = ops.appeal_code

            # Taking latest final report file
            final_report = (
                AppealDocument.objects.filter(
                    appeal=appeal,
                    type=final_report_type,
                )
                .order_by("-created_at")
                .first()
            )

            if not final_report:
                skipped += 1
                continue

            if ops.appeal_document_id != final_report.id:
                ops.appeal_document_id = final_report.id
                ops.save(update_fields=["appeal_document_id"])
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"OpsLearning update completed. Updated: {updated}, Skipped: {skipped}"
            )
        )
