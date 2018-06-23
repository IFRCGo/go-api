from datetime import datetime, timezone, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Country, Appeal, Event, FieldReport
from api.logger import logger
from notifications.models import RecordType, SubscriptionType

time_interval = timedelta(minutes=5)

class Command(BaseCommand):
    help = 'Index and send notificatins about recently changed records'


    def get_time_threshold(self):
        return datetime.utcnow().replace(tzinfo=timezone.utc) - time_interval


    def gather_country_and_region(self, records):
        # Appeals only, since these have a single country/region
        countries = []
        regions = []
        for record in records:
            if record.country is not None:
                countries.append('c%s' % record.country.id)
                if record.country.region is not None:
                    regions.append('r%s' % record.country.region.id)
        countries = list(set(countries))
        regions = list(set(regions))
        return countries, regions


    def gather_countries_and_regions(self, records):
        # Applies to emergencies and field reports, which have a
        # many-to-many relationship to countries and regions
        countries = []
        for record in records:
            if record.countries is not None:
                countries += [country.id for country in record.countries.all()]
        countries = list(set(countries))
        qs = Country.objects.filter(pk__in=countries)
        regions = ['r%s' % country.region.id for country in qs if country.region is not None]
        countries = ['c%s' % id for id in countries]
        return countries, regions


    def gather_subscribers(self, records, rtype, stype):
        # Gather the email addresses of users who should be notified
        # Start with any users subscribed directly to this record type.
        subscribers = User.objects.filter(subscription__rtype=rtype, subscription__stype=stype).values('email')

        dtypes = list(set(['d%s' % record.dtype.id for record in records if record.dtype is not None]))
        if (rtype == RecordType.APPEAL):
            countries, regions = self.gather_country_and_region(records)
        else:
            countries, regions = self.gather_countries_and_regions(records)

        lookups = dtypes + countries + regions
        if len(lookups):
            subscribers = (subscribers | User.objects.filter(subscription__lookup_id__in=lookups).values('email')).distinct()
        emails = [subscriber['email'] for subscriber in subscribers]
        return emails


    def notify(self, records, rtype, stype):
        if not records.count():
            return
        emails = self.gather_subscribers(records, rtype, stype)
        # TODO send notifications to users


    def handle(self, *args, **options):
        t = self.get_time_threshold()

        self.notify(FieldReport.objects.filter(created_at__gte=t),
                    RecordType.FIELD_REPORT,
                    SubscriptionType.NEW)
