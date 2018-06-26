from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from api.models import Country, Region

class Command(BaseCommand):
    help = 'Create standard geographic permissions classes and groups'

    def handle(self, *args, **options):
        country_content_type = ContentType.objects.get_for_model(Country)
        countries = Country.objects.all()
        for country in countries:
            codename = 'country_admin_%s' % country.id
            name = 'Admin for %s' % country.name
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=country_content_type
            )
            # If it's a new permission, create a group for it
            group, created = Group.objects.get_or_create(
                name='%s Admins' % country.name
            )
            group.permissions.add(permission)

        region_content_type = ContentType.objects.get_for_model(Region)
        regions = Region.objects.all()
        for region in regions:
            codename = 'region_admin_%s' % region.id
            name = 'Admin for %s' % region.name
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                name=name,
                content_type=region_content_type
            )
            # If it's a new permission, create a group for it
            group, created = Group.objects.get_or_create(
                name='%s Regional Admins' % region.name
            )
            group.permissions.add(permission)

        # Create an IFRC permission and attach it to a group
        ifrc_permission, perm_created = Permission.objects.get_or_create(
            codename='ifrc_admin',
            name='IFRC Admin',
            content_type=ContentType.objects.get_for_model(Country),
        )

        ifrc_group, group_created = Group.objects.get_or_create(
            name='IFRC Admins'
        )
        ifrc_group.permissions.add(ifrc_permission)
