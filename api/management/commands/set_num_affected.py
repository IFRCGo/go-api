from django.core.management.base import BaseCommand
from api.models import Appeal, Event

class Command(BaseCommand):
    help = 'Creates an event to go with each appeal that lacks one'
    def handle(self, *args, **options):
        print('%s current events' % Event.objects.all().count())

        events_with_appeals = list(Event.objects.prefetch_related().filter(appeals__isnull=False))
        print ('Adding data to %s events' % len(events_with_appeals))
        for event in events_with_appeals:
            num_affected = 0
            for appeal in event.appeals.all():
                num_affected += appeal.num_beneficiaries
            event.num_affected = num_affected
            event.save()
        print ('Done!')
