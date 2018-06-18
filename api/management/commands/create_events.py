from django.core.management.base import BaseCommand
from api.models import Appeal, Event

class Command(BaseCommand):
    help = 'Creates an event to go with each appeal that lacks one'
    def handle(self, *args, **options):
        print('%s current events' % Event.objects.all().count())

        appeals_without_events = list(Appeal.objects.filter(event__isnull=True))
        print ('Creating %s events' % len(appeals_without_events))
        for appeal in appeals_without_events:
            fields = {
                'name': appeal.name,
                'dtype': appeal.dtype,
                'disaster_start_date': appeal.start_date,
                'auto_generated': True,
                'auto_generated_source': 'Automated appeal script',
            }
            event = Event.objects.create(**fields)
            if appeal.country is not None:
                event.countries.add(appeal.country)
            if appeal.region is not None:
                event.regions.add(appeal.region)
            appeal.event = event
            appeal.save()

        print('%s current events' % Event.objects.all().count())
