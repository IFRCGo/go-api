from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from api.models import Region


class Command(BaseCommand):
    help = "Create standard dref geographic permissions classes and groups"

    def handle(self, *args, **options):

        print("- Creating/Updating permissions/groups for Dref regions admin")
        region_content_type = ContentType.objects.get_for_model(Region)
        regions = Region.objects.all()
        for region in regions:
            codename = "dref_region_admin_%s" % region.id
            name = "Dref Admin for %s" % region.name
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=region_content_type,
                defaults=dict(name=name),
            )
            # If it's a new permission, create a group for it
            group, created = Group.objects.get_or_create(name="%s Dref Regional Admins" % region.name)
            group.permissions.add(permission)
