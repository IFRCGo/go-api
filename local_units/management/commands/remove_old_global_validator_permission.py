from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction

from local_units.models import LocalUnit


class Command(BaseCommand):
    help = "Delete old permission and group for Local Unit Global Validator"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(" Deleting old permission and group for local unit global validator"))
        codename = "local_unit_global_validator"
        group_name = "Local Unit Global Validators"
        content_type = ContentType.objects.get_for_model(LocalUnit)

        permission = Permission.objects.filter(codename=codename, content_type=content_type)
        if permission.exists():
            permission.delete()
            self.stdout.write(self.style.SUCCESS(f"\t--> Deleted Permission {codename}"))
        else:
            self.stdout.write(self.style.WARNING(f"\t--> Permission {codename} not found"))
        group = Group.objects.filter(name=group_name)
        if group.exists():
            group.delete()
            self.stdout.write(self.style.SUCCESS(f"\t--> Deleted Group {group_name}"))
        else:
            self.stdout.write(self.style.WARNING(f"\t--> Group {group_name} not found"))
