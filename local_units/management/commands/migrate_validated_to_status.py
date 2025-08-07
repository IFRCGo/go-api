from django.core.management.base import BaseCommand
from django.db import transaction

from local_units.models import LocalUnit


class Command(BaseCommand):
    help = "Migrate validated boolean field to status field."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        validated_local_unit = LocalUnit.objects.filter(validated=True)
        unvalidated_local_unit = LocalUnit.objects.filter(validated=False)
        validated_updated = validated_local_unit.update(status=LocalUnit.Status.VALIDATED)
        unvalidated_updated = unvalidated_local_unit.update(status=LocalUnit.Status.UNVALIDATED)
        self.stdout.write(self.style.SUCCESS("Migration complete."))
        self.stdout.write(f"Total validated local unit before migration: {validated_local_unit.count()}")
        self.stdout.write(f"Total unvalidated local unit before migration: {unvalidated_local_unit.count()}")
        self.stdout.write(f"Total validated local unit after migration: {validated_updated}")
        self.stdout.write(f"Total unvalidated local unit after migration: {unvalidated_updated}")
