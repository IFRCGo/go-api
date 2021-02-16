from django.core.management.base import BaseCommand
from api.models import Country
from django.db import transaction
from django.db.models import Q
from api.logger import logger


class Command(BaseCommand):
    help = 'Update Countries initially to set/revoke their in_search field (probably one-time run only)'

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            # Update countries which should appear in search
            inc_c = Country.objects.filter(disputed=False, record_type=1).update(in_search=True)
            # Update countries which should NOT appear in search
            exc_c = Country.objects.filter(Q(disputed=True) | ~Q(record_type=1)).update(in_search=False)
            logger.info('Successfully set in_search for Countries')
        except Exception as ex:
            logger.error(f'Failed to set in_search for Countries. Error: {str(ex)}')

