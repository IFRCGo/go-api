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
        self.stdout.write(self.style.NOTICE("Creating global validators permissions and groups"))
        for local_unit_type in local_unit_types.iterator():
            type_name = local_unit_type.name.replace(" ", "_").lower()
            codename = f"local_unit_global_validator_{type_name}"
            permission, _ = Permission.objects.get_or_create(
                codename=codename, name=f"Local Unit Global Validator For {local_unit_type.name}", content_type=content_type
            )
            group_name = f"local_unit_global_validator_for_{type_name}"
            group, _ = Group.objects.get_or_create(name=group_name)
            group.permissions.add(permission)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Local unit global validator for {local_unit_type.name} permission and group created successfully"  # noqa: E501
                )
            )
        # Region level Permissions and Groups
        self.stdout.write(self.style.NOTICE("Creating region-level permissions and groups"))
        for region in regions.iterator():
            region_label = region.label.replace(" ", "_").lower()
            for local_unit_type in local_unit_types.iterator():
                type_name = local_unit_type.name.replace(" ", "_").lower()
                codename = f"local_unit_validator_{region_label}_{type_name}"
                permission, _ = Permission.objects.get_or_create(
                    codename=codename,
                    name=f"Local Unit Validator For {local_unit_type.name} in {region.label}",
                    content_type=content_type,
                )
                group_name = f"local_unit_validator_for_{type_name}_{region_label}"
                group, _ = Group.objects.get_or_create(name=group_name)
                group.permissions.add(permission)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Local unit validator in {region.label} for {local_unit_type.name} permission and group created successfully"  # noqa: E501
                    )
                )
        # Country level Permissions and Groups
        self.stdout.write(self.style.NOTICE("Creating country-level permissions and groups"))
        for country in countries.iterator():
            country_name = country.name.replace(" ", "_").lower()
            for local_unit_type in local_unit_types.iterator():
                type_name = local_unit_type.name.replace(" ", "_").lower()
                codename = f"local_unit_validator_{country_name}_{type_name}"

                permission, _ = Permission.objects.get_or_create(
                    codename=codename,
                    name=f"Local Unit Validator For {local_unit_type.name} in {country.name}",
                    content_type=content_type,
                )
                group_name = f"local_unit_validator_for_{type_name}_{country_name}"
                group, _ = Group.objects.get_or_create(name=group_name)
                group.permissions.add(permission)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Local unit validator in {country.name} for {local_unit_type.name} permission and group created successfully"  # noqa: E501
                    )
                )
