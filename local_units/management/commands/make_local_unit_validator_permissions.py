import logging

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from api.models import Region
from local_units.models import Country, LocalUnit, LocalUnitType

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create local unit validator permissions and groups for each local unit type"

    def handle(self, *args, **options):
        content_type = ContentType.objects.get_for_model(LocalUnit)
        local_unit_types = LocalUnitType.objects.all()
        regions = Region.objects.all()
        countries = Country.objects.filter(is_deprecated=False, independent=True, iso3__isnull=False)

        # Global level Permissions and Groups
        logger.info("Creating global validators permissions and groups...")
        for local_unit_type in local_unit_types:
            type_name = local_unit_type.name.replace(" ", "_").lower()
            codename = f"local_unit_global_validator_{type_name}"
            permission, created = Permission.objects.get_or_create(
                codename=codename, name=f"Local Unit Global Validator For {local_unit_type.name}", content_type=content_type
            )
            group_name = f"local_unit_global_validator_for_{type_name}"
            group, group_created = Group.objects.get_or_create(name=group_name)
            group.permissions.add(permission)
            logger.info(
                f"Local unit global validator for {local_unit_type.name} permission and group created successfully"  # noqa: E501
            )

        # Region level Permissions and Groups
        logger.info("Creating region-level permissions and groups...")
        for region in regions:
            region_label = region.label.replace(" ", "_").lower()

            for local_unit_type in local_unit_types:
                type_name = local_unit_type.name.replace(" ", "_").lower()
                codename = f"local_unit_validator_{region_label}_{type_name}"

                permission, created = Permission.objects.get_or_create(
                    codename=codename,
                    name=f"Local Unit Validator For {local_unit_type.name} in {region.label}",
                    content_type=content_type,
                )
                group_name = f"local_unit_validator_for_{type_name}_{region_label}"
                group, group_created = Group.objects.get_or_create(name=group_name)
                group.permissions.add(permission)
                logger.info(
                    f"Local unit validator in {region.label} for {local_unit_type.name} permission and group created successfully"  # noqa: E501
                )

        # Country level Permissions and Groups
        logger.info("Creating country-level permissions and groups...")
        for country in countries:
            country_name = country.name.replace(" ", "_").lower()
            for local_unit_type in local_unit_types:
                type_name = local_unit_type.name.replace(" ", "_").lower()
                codename = f"local_unit_validator_{country_name}_{type_name}"

                permission, created = Permission.objects.get_or_create(
                    codename=codename,
                    name=f"Local Unit Validator For {local_unit_type.name} in {country.name}",
                    content_type=content_type,
                )
                group_name = f"local_unit_validator_for_{type_name}_{country_name}"
                group, group_created = Group.objects.get_or_create(name=group_name)
                group.permissions.add(permission)
                logger.info(
                    f"Local unit validator in {country.name} for {local_unit_type.name} permission and group created successfully"  # noqa: E501
                )
