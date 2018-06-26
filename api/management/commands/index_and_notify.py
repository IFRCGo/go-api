from datetime import datetime, timezone, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.template.loader import render_to_string
from elasticsearch.helpers import bulk
from api.indexes import ES_PAGE_NAME
from api.esconnection import ES_CLIENT
from api.models import Country, Appeal, Event, FieldReport
from api.logger import logger
from notifications.models import RecordType, SubscriptionType
from notifications.hello import get_hello
from notifications.notification import send_notification
from main.frontend import frontend_url

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


    def get_template(self):
        return 'email/generic_notification.html'


    # Get the front-end url of the resource
    def get_resource_uri (self, record, rtype):
        # Determine the front-end URL
        resource_uri = frontend_url
        if rtype == RecordType.APPEAL and (
                record.event is not None and not record.needs_confirmation):
            # Appeals with confirmed emergencies link to that emergency
            resource_uri = '%s/emergencies/%s' % (frontend_url, record.event.id)
        elif rtype != RecordType.APPEAL:
            # Field reports and emergencies
            resource_uri = '%s/%s/%s' % (
                frontend_url,
                'emergencies' if rtype == RecordType.EVENT else 'reports',
                record.id
            )
        return resource_uri


    def get_admin_uri (self, record, rtype):
        admin_page = {
            RecordType.FIELD_REPORT: 'fieldreport',
            RecordType.APPEAL: 'appeal',
            RecordType.EVENT: 'event',
        }[rtype]
        return '%s/admin/%s/%s/change' % (
            settings.BASE_URL,
            admin_page,
            record.id,
        )


    def get_record_title(self, record, rtype):
        if rtype == RecordType.FIELD_REPORT:
            return record.summary
        else:
            return record.name


    def get_record_display(self, rtype, count):
        display = {
            RecordType.FIELD_REPORT: 'field report',
            RecordType.APPEAL: 'appeal',
            RecordType.EVENT: 'event',
        }[rtype]
        if (count > 1):
            display += 's'
        return display


    def notify(self, records, rtype, stype):
        record_count = records.count()
        if not record_count:
            return
        emails = self.gather_subscribers(records, rtype, stype)
        if not len(emails):
            return

        # Only serialize the first 10 records
        entries = list(records) if record_count <= 10 else list(records[:10])
        record_entries = []
        for record in entries:
            record_entries.append({
                'resource_uri': self.get_resource_uri(record, rtype),
                'admin_uri': self.get_admin_uri(record, rtype),
                'title': self.get_record_title(record, rtype),
            })

        template_path = self.get_template()
        html = render_to_string(template_path, {
            'hello': get_hello(),
            'count': record_count,
            'records': record_entries,
        })
        recipients = emails
        adj = 'New' if stype == SubscriptionType.NEW else 'Modified'
        record_type = self.get_record_display(rtype, record_count)
        subject = '%s %s %s(s) in IFRC GO ' % (
            record_count,
            adj,
            record_type,
        )
        logger.info('Notifying %s subscriber(s) about %s %s %s' % (len(emails), record_count, adj.lower(), record_type))
        send_notification(subject, recipients, html)


    def index_new_records(self, records):
        self.bulk([self.convert_for_bulk(record, create=True) for record in list(records)])


    def index_updated_records(self, records):
        self.bulk([self.convert_for_bulk(record, create=False) for record in list(records)])


    def convert_for_bulk(self, record, create):
        data = record.indexing()
        metadata = {
            '_op_type': 'create' if create else 'update',
            '_index': ES_PAGE_NAME,
            '_type': 'page',
            '_id': record.es_id()
        }
        if (create):
            metadata.update(**data)
        else:
            metadata['doc'] = data
        return metadata


    def bulk(self, actions):
        try:
            created, errors = bulk(client=ES_CLIENT, actions=actions)
            if len(errors):
                logger.error('Produced the following errors:')
                logger.error('[%s]' % ', '.join(map(str, errors)))
        except Exception as e:
            logger.error('Could not index records')
            logger.error('%s...' % str(e)[:512])


    # Remove items in a queryset where updated_at == created_at.
    # This leaves us with only ones that have been modified.
    def filter_just_created(self, queryset):
        if queryset.first() is None:
            return []
        if queryset.first().modified_at is not None:
            return [record for record in queryset if (
                record.modified_at.replace(microsecond=0) == record.created_at.replace(microsecond=0))]
        else:
            return [record for record in queryset if (
                record.updated_at.replace(microsecond=0) == record.created_at.replace(microsecond=0))]


    def handle(self, *args, **options):
        t = self.get_time_threshold()

        new_reports = FieldReport.objects.filter(created_at__gte=t)
        updated_reports = FieldReport.objects.filter(updated_at__gte=t)

        new_appeals = Appeal.objects.filter(created_at__gte=t)
        updated_appeals = Appeal.objects.filter(modified_at__gte=t)

        new_events = Event.objects.filter(created_at__gte=t)
        updated_events = Event.objects.filter(updated_at__gte=t)

        self.notify(new_reports, RecordType.FIELD_REPORT, SubscriptionType.NEW)
        self.notify(updated_reports, RecordType.FIELD_REPORT, SubscriptionType.EDIT)

        self.notify(new_appeals, RecordType.APPEAL, SubscriptionType.NEW)
        self.notify(updated_appeals, RecordType.APPEAL, SubscriptionType.EDIT)

        self.notify(new_events, RecordType.EVENT, SubscriptionType.NEW)
        self.notify(updated_events, RecordType.EVENT, SubscriptionType.EDIT)

        logger.info('Indexing %s updated field reports' % updated_reports.count())
        self.index_updated_records(self.filter_just_created(updated_reports))
        logger.info('Indexing %s updated appeals' % updated_appeals.count())
        self.index_updated_records(self.filter_just_created(updated_appeals))
        logger.info('Indexing %s updated events' % updated_events.count())
        self.index_updated_records(self.filter_just_created(updated_events))

        logger.info('Indexing %s new field reports' % new_reports.count())
        self.index_new_records(new_reports)
        logger.info('Indexing %s new appeals' % new_appeals.count())
        self.index_new_records(new_appeals)
        logger.info('Indexing %s new events' % new_events.count())
        self.index_new_records(new_events)
