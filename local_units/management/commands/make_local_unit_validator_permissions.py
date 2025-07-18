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
        regions = Region.objects.all()
        countries = Country.objects.filter(
            is_deprecated=False, independent=True, iso3__isnull=False, record_type=CountryType.COUNTRY
        )
        # Global level Permissions and Groups
        self.stdout.write(self.style.NOTICE("Creating/Updating global validators permissions and groups"))
        for local_unit_type in local_unit_types.iterator():
            codename = "local_unit_global_validator_%s" % local_unit_type.id
            name = "Local unit global validator for %s" % local_unit_type.name
            permission, _ = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults=dict(name=name),
            )
            group_name = "Local unit global validator for %s" % local_unit_type.name
            group, _ = Group.objects.get_or_create(name=group_name)
            group.permissions.add(permission)
            self.stdout.write(
                self.style.SUCCESS(
                    "Local unit global validator for %s permission and group created successfully" % local_unit_type.name
                )
            )

        # Region level Permissions and Groups
        self.stdout.write(self.style.NOTICE("Creating/Updating region-level permissions and groups"))
        for region in regions.iterator():
            for local_unit_type in local_unit_types.iterator():
                codename = "local_unit_region_validator_%s_%s" % (local_unit_type.id, region.id)
                name = "Local unit validator for %s %s" % (local_unit_type.name, region.get_name_display())
                permission, _ = Permission.objects.get_or_create(
                    codename=codename,
                    content_type=content_type,
                    defaults=dict(name=name),
                )
                group_name = "Local unit validator for %s %s" % (local_unit_type.name, region.get_name_display())
                group, _ = Group.objects.get_or_create(name=group_name)
                group.permissions.add(permission)
                self.stdout.write(
                    self.style.SUCCESS(
                        "Local unit validator in %s for %s permission and group created successfully"
                        % (region.get_name_display(), local_unit_type.name)
                    )
                )

        # Country level Permissions and Groups
        self.stdout.write(self.style.NOTICE("Creating/Updating country-level permissions and groups"))
        for country in countries.iterator():
            for local_unit_type in local_unit_types.iterator():
                codename = "local_unit_country_validator_%s_%s" % (local_unit_type.id, country.id)
                name = "Local unit validator for %s %s" % (local_unit_type.name, country.name)
                permission, _ = Permission.objects.get_or_create(
                    codename=codename,
                    content_type=content_type,
                    defaults=dict(name=name),
                )
                group_name = "Local unit validator for %s %s" % (local_unit_type.name, country.name)
                group, _ = Group.objects.get_or_create(name=group_name)
                group.permissions.add(permission)
                self.stdout.write(
                    self.style.SUCCESS(
                        "Local unit validator in %s for %s permission and group created successfully"
                        % (country.name, local_unit_type.name)
                    )
                )
