from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from api.molnix_utils import MolnixApi
from api.logger import logger

def get_unique_tags(deployments, open_positions):
    tags = []
    tag_ids = []
    for deployment in deployments:
        for tag in deployment['tags']:
            if tag['id'] not in tag_ids:
                tags.append(tag)
                tag_ids.append(tag['id'])
    return tags

class Command(BaseCommand):
    help = "Sync data from Molnix API to GO db"

    @transaction.atomic
    def handle(self, *args, **options):
        molnix = MolnixApi(
            url=settings.MOLNIX_API_BASE,
            username=settings.MOLNIX_USERNAME,
            password=settings.MOLNIX_PASSWORD
        )
        try:
            molnix.login()
        except Exception as ex:
            logger.error('Failed to login to Molnix API: %s' % str(ex))
            return
        try:
            # tags = molnix.get_tags()
            deployments = molnix.get_deployments()
            open_positions = molnix.get_open_positions()
        except Exception as ex:
            logger.error('Failed to fetch data from Molnix API: %s' % str(ex))
            return
        used_tags = get_unique_tags(deployments, open_positions)
        print(used_tags)
        molnix.logout()
