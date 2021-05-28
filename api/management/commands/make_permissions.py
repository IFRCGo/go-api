from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_permission_codename
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.conf import settings

from api.models import Country, Region
from lang.models import String


class Command(BaseCommand):
    help = 'Create standard geographic permissions classes and groups'

    def handle(self, *args, **options):
        print('- Creating/Updating permissions/groups for countries')
        country_content_type = ContentType.objects.get_for_model(Country)
        countries = Country.objects.all()
        for country in countries:
            print(f'\t-> {country}')
            codename = 'country_admin_%s' % country.id
            name = 'Admin for %s' % country.name
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=country_content_type,
                defaults=dict(name=name),
            )
            # If it's a new permission, create a group for it
            group, created = Group.objects.get_or_create(
                name='%s Admins' % country.name
            )
            group.permissions.add(permission)

        print('- Creating/Updating permissions/groups for regions')
        region_content_type = ContentType.objects.get_for_model(Region)
        regions = Region.objects.all()
        for region in regions:
            print(f'\t-> {region}')
            codename = 'region_admin_%s' % region.id
            name = 'Admin for %s' % region.name
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=region_content_type,
                defaults=dict(name=name),
            )
            # If it's a new permission, create a group for it
            group, created = Group.objects.get_or_create(
                name='%s Regional Admins' % region.name
            )
            group.permissions.add(permission)

        print('- Creating/Updating permissions/groups for IFRC Admin')
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

        print('- Creating/Updating permissions/groups for Language')
        # Language permission
        string_content_type = ContentType.objects.get_for_model(String)
        lang_permissions = defaultdict(list)
        for lang_code, _ in settings.LANGUAGES:
            print(f'\t-> {lang_code}')
            lang_permission, _ = Permission.objects.get_or_create(
                codename=f'lang__string__maintain__{lang_code}',
                content_type=string_content_type,
                defaults=dict(name=f'Language <{lang_code}> (API Level Access)'),
            )
            lang_permissions[lang_code] = lang_permission

        language_maintainers_group, _ = Group.objects.get_or_create(name='Language maintainers (Admin Panel)')
        language_maintainers_group.permissions.add(
            *[
                Permission.objects.get(codename=get_permission_codename(action, String._meta))
                for action in ['view', 'add', 'change', 'delete']
            ]
        )
