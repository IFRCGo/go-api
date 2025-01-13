import logging

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from local_units.models import LocalUnit

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create standard local unit global validator permission class and group"

    def handle(self, *args, **options):
        logger.info("Creating/Updating permissions/groups for local unit global validator")
        print("- Creating/Updating permissions/groups for local unit global validator")
        codename = "local_unit_global_validator"
        content_type = ContentType.objects.get_for_model(LocalUnit)
        permission, created = Permission.objects.get_or_create(
            codename=codename,
            name="Local Unit Global Validator",
            content_type=content_type,
        )

        # If it's a new permission, create a group for it
        group, created = Group.objects.get_or_create(name="Local Unit Global Validators")
        group.permissions.add(permission)
        logger.info("Local unit global validator permission and group created")
