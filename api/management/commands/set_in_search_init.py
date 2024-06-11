from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from api.logger import logger
from api.models import Country


class Command(BaseCommand):
    help = "Update Countries initially to set/revoke their in_search field (probably one-time run only)"

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            # Update countries which should appear in search
            Country.objects.filter(independent=True, is_deprecated=False, record_type=1).update(in_search=True)
            # Update countries which should NOT appear in search
            # independent can be null too thus why negated check
            Country.objects.filter(~Q(independent=True) | Q(is_deprecated=True) | ~Q(record_type=1)).update(in_search=False)
            logger.info("Successfully set in_search for Countries")
        except Exception as ex:
            logger.error(f"Failed to set in_search for Countries. Error: {str(ex)}")
