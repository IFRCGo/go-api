from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import Country, CountryType
from local_units.models import ExternallyManagedLocalUnit, LocalUnit, LocalUnitType


class Command(BaseCommand):
    help = "Create Externally Managed status for all local units type and mark all local units as externally managed."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many local units would be updated without making changes.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        local_unit_qs = LocalUnit.objects.all()

        if options["dry_run"]:
            self.stdout.write(
                self.style.WARNING(f"[Dry Run]: {local_unit_qs.count()} local units would be marked as externally managed.")
            )
            return

        # Create Country level Externally Managed
        local_unit_types = LocalUnitType.objects.all()
        self.stdout.write(self.style.NOTICE("\n Creating/Updating Externally Managed local units"))
        countries = Country.objects.filter(
            is_deprecated=False,
            independent=True,
            iso3__isnull=False,
            record_type=CountryType.COUNTRY,
        )
        for country in countries.iterator():
            self.stdout.write(self.style.NOTICE(f"--> Country: {country.name}"))
            for local_unit_type in local_unit_types.iterator():
                instance, _ = ExternallyManagedLocalUnit.objects.get_or_create(
                    country=country,
                    local_unit_type=local_unit_type,
                )
                instance.enabled = True
                instance.save(update_fields=["enabled"])
                self.stdout.write(self.style.SUCCESS(f"\t--> Created externally managed for {local_unit_type.name}"))

        # Update all local units to Externally managed
        updated_count = local_unit_qs.update(
            status=LocalUnit.Status.EXTERNALLY_MANAGED,
        )

        self.stdout.write(self.style.SUCCESS(f"Successfully marked {updated_count} local units as externally managed."))
