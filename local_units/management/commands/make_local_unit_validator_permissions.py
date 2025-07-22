from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import Country, CountryType, Region
from local_units.models import LocalUnit, LocalUnitType


class Command(BaseCommand):
    help = "Create local unit validator permissions and groups for each local unit type"

    @transaction.atomic
    def handle(self, *args, **options):
        content_type = ContentType.objects.get_for_model(LocalUnit)
        local_unit_types = LocalUnitType.objects.all()

        # Global level Permissions and Groups
        self.stdout.write(self.style.NOTICE("\n--- Creating/Updating GLOBAL validator permissions and groups"))
        for local_unit_type in local_unit_types.iterator():
            codename = f"local_unit_global_validator_{local_unit_type.id}"
            name = f"Global validator for {local_unit_type.name}"
            permission, _ = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults=dict(name=name),
            )
            group_name = f"Local unit global validator for {local_unit_type.name}"
            group, _ = Group.objects.get_or_create(name=group_name)
            group.permissions.add(permission)
            self.stdout.write(self.style.SUCCESS(f"\t--> {local_unit_type.name}"))

        # Region level Permissions and Groups
        self.stdout.write(self.style.NOTICE("\n--- Creating/Updating REGION-LEVEL validator permissions and groups"))
        regions = Region.objects.all()
        for region in regions.iterator():
            region_name = region.get_name_display()
            self.stdout.write(self.style.NOTICE(f"--> Region: {region_name}"))
            for local_unit_type in local_unit_types.iterator():
                codename = f"local_unit_region_validator_{local_unit_type.id}_{region.id}"
                name = f"Local unit validator for {local_unit_type.name} {region_name}"
                permission, _ = Permission.objects.get_or_create(
                    codename=codename,
                    content_type=content_type,
                    defaults=dict(name=name),
                )
                group_name = f"Local unit validator for {local_unit_type.name} {region_name}"
                group, _ = Group.objects.get_or_create(name=group_name)
                group.permissions.add(permission)
                self.stdout.write(self.style.SUCCESS(f"\t--> {local_unit_type.name}"))

        # Country level Permissions and Groups
        self.stdout.write(self.style.NOTICE("\n--- Creating/Updating COUNTRY-LEVEL validator permissions and groups"))
        countries = Country.objects.filter(
            is_deprecated=False, independent=True, iso3__isnull=False, record_type=CountryType.COUNTRY
        )
        for country in countries.iterator():
            self.stdout.write(self.style.NOTICE(f"--> Country: {country.name}"))
            for local_unit_type in local_unit_types.iterator():
                codename = f"local_unit_country_validator_{local_unit_type.id}_{country.id}"
                name = f"Local unit validator for {local_unit_type.name} {country.name}"
                permission, _ = Permission.objects.get_or_create(
                    codename=codename,
                    content_type=content_type,
                    defaults=dict(name=name),
                )
                group_name = f"Local unit validator for {local_unit_type.name} {country.name}"
                group, _ = Group.objects.get_or_create(name=group_name)
                group.permissions.add(permission)
                self.stdout.write(self.style.SUCCESS(f"\t--> {local_unit_type.name}"))

        self.stdout.write(self.style.SUCCESS("\n All permissions and groups created/updated successfully\n"))
