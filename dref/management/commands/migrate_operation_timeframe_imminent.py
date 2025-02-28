from django.core.management.base import BaseCommand
from django.db.models import DurationField, ExpressionWrapper, F
from django.db.models.functions import ExtractDay

from dref.models import Dref


class Command(BaseCommand):
    help = "Migrate Dref imminent's operation_timeframe to new field in days"

    def handle(self, *args, **options):
        dref_imminent_qs = (
            Dref.objects.filter(
                type_of_dref=Dref.DrefType.IMMINENT,
            )
            .annotate(
                operation_timeframe_imminent_days=ExtractDay(
                    ExpressionWrapper(
                        (F("end_date") - F("date_of_approval")),
                        output_field=DurationField(),
                    )
                )
            )
            .update(
                operation_timeframe_imminent=F("operation_timeframe_imminent_days"),
            )
        )

        self.stdout.write(self.style.SUCCESS(f"Updated {dref_imminent_qs} Dref imminent's operation timeframes in days"))
