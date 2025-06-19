from django.core.management.base import BaseCommand
from django.db.models import F

from dref.models import DrefOperationalUpdate


class Command(BaseCommand):
    help = "Update DREF operations total DREF allocation field based on additional allocation"

    def handle(self, *args, **options):
        dref_operational_qs = DrefOperationalUpdate.objects.filter(
            dref_allocated_so_far__isnull=False,
            additional_allocation__isnull=True,
            total_dref_allocation__isnull=True,
        ).update(
            total_dref_allocation=F("dref_allocated_so_far"),
        )

        self.stdout.write(
            self.style.SUCCESS(f"Updated {dref_operational_qs} DREF operational updates with total DREF allocation.")
        )
