from django.core.management.base import BaseCommand

from local_units.models import LocalUnit


class Command(BaseCommand):
    help = "Mark existing local units as externally managed"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many local units would be updated without making changes.",
        )

    def handle(self, *args, **options):
        local_unit_qs = LocalUnit.objects.all()

        if options["dry_run"]:
            self.stdout.write(
                self.style.WARNING(f"[Dry Run]: {local_unit_qs.count} local units would be marked as externally managed.")
            )
            return

        updated_count = local_unit_qs.update(
            status=LocalUnit.Status.EXTERNALLY_MANAGED,
        )

        self.stdout.write(self.style.SUCCESS(f"Successfully marked {updated_count} local units as externally managed."))
