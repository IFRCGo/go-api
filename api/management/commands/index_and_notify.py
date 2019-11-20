from datetime import datetime, timezone, timedelta
from django.db.models import Q, Sum
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.template.loader import render_to_string
from elasticsearch.helpers import bulk
from api.indexes import ES_PAGE_NAME
from api.esconnection import ES_CLIENT
from api.models import Country, Appeal, Event, FieldReport
from api.logger import logger
from notifications.models import RecordType, SubscriptionType, Subscription, SurgeAlert
from notifications.hello import get_hello
from notifications.notification import send_notification
from deployments.models import PersonnelDeployment
from main.frontend import frontend_url
import html

time_interval  = timedelta(minutes = 5)
time_interva2  = timedelta(   days = 1) # to check: the change was not between time_interval and time_interva2, so that the user don't receive email more frequent than a day.
time_interva7  = timedelta(   days = 7) # for digest mode
basetime       = int(10314) # weekday - hour - min for digest timing (5 minutes once a week)
daily_retro    = int(654) # hour - min for daily retropective email timing (5 minutes a day) | Should not contain a leading 0!
max_length     = 280 # after this length (at the first space) we cut the sent content
events_sent_to = {} # to document sent events before re-sending them via specific following
template_types = {
    99: 'design/generic_notification.html',
    RecordType.FIELD_REPORT: 'design/field_report.html',
    RecordType.NEW_OPERATIONS: 'design/new_operation.html',
    98: 'design/operation_update.html', # TODO: Either Operation Update needs a number or it should be constructed from other types (ask someone)
    RecordType.WEEKLY_DIGEST: 'design/weekly_digest.html',
}

class Command(BaseCommand):
    help = 'Index and send notifications about new/changed records'

    # Digest mode duration is 5 minutes once a week
    def is_digest_mode(self):
        today = datetime.utcnow().replace(tzinfo=timezone.utc)
        weekdayhourmin = int(today.strftime('%w%H%M'))
        return basetime <= weekdayhourmin and weekdayhourmin < basetime + 5

    def is_retro_mode(self):
        today = datetime.utcnow().replace(tzinfo=timezone.utc)
        hourmin = int(today.strftime('%H%M'))
        return daily_retro <= hourmin and hourmin < daily_retro + 5

    def get_time_threshold(self):
        return datetime.utcnow().replace(tzinfo=timezone.utc) - time_interval

    def get_time_threshold2(self):
        return datetime.utcnow().replace(tzinfo=timezone.utc) - time_interva2

    def get_time_threshold_digest(self):
        return datetime.utcnow().replace(tzinfo=timezone.utc) - time_interva7

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
        # Correction for the new notification types:
        if  rtype == RecordType.EVENT or rtype == RecordType.FIELD_REPORT:
            rtype_of_subscr = RecordType.NEW_EMERGENCIES
            stype = SubscriptionType.NEW
        elif rtype == RecordType.APPEAL:
            rtype_of_subscr = RecordType.NEW_OPERATIONS
            stype = SubscriptionType.NEW
        else:
            rtype_of_subscr = rtype

        # Gather the email addresses of users who should be notified
        if self.is_digest_mode():
            subscribers = User.objects.filter(subscription__rtype=RecordType.WEEKLY_DIGEST, \
                                          is_active=True).values('email')
            # In digest mode we do not care about other circumstances, just get every subscriber's email.
            emails = [subscriber['email'] for subscriber in subscribers]
            return emails
        else:
        # Start with any users subscribed directly to this record type.
            subscribers = User.objects.filter(subscription__rtype=rtype_of_subscr, \
                                          subscription__stype=stype, is_active=True).values('email')

        # For FOLLOWED_EVENTs and DEPLOYMENTs we do not collect other generic (d*, country, region) subscriptions, just one. This part is not called.
        if rtype_of_subscr != RecordType.FOLLOWED_EVENT and \
           rtype_of_subscr != RecordType.SURGE_ALERT and \
           rtype_of_subscr != RecordType.SURGE_DEPLOYMENT_MESSAGES:
            dtypes = list(set(['d%s' % record.dtype.id for record in records if record.dtype is not None]))

            if (rtype_of_subscr == RecordType.NEW_OPERATIONS):
                countries, regions = self.gather_country_and_region(records)
            else:
                countries, regions = self.gather_countries_and_regions(records)

            lookups = dtypes + countries + regions
            if len(lookups):
                subscribers = (subscribers | User.objects.filter(subscription__lookup_id__in=lookups, is_active=True).values('email')).distinct()
        emails = [subscriber['email'] for subscriber in subscribers]
        return emails


    def get_template(self, rtype=99):
        #older: return 'email/generic_notification.html'
        #old: return 'design/generic_notification.html'
        return template_types[rtype]


    # Get the front-end url of the resource
    def get_resource_uri (self, record, rtype):
        # Determine the front-end URL
        resource_uri = frontend_url
        if rtype == RecordType.SURGE_ALERT or rtype == RecordType.FIELD_REPORT: # Pointing to event instead of field report %s/%s/%s - Munu asked - ¤
            belonging_event = record.event.id if record.event is not None else 999 # Very rare
            resource_uri = '%s/emergencies/%s#overview' % (frontend_url, belonging_event)
        elif rtype == RecordType.SURGE_DEPLOYMENT_MESSAGES:
            resource_uri = '%s/%s' % (frontend_url, 'deployments')  # can be further sophisticated
        elif rtype == RecordType.APPEAL and (
                record.event is not None and not record.needs_confirmation):
            # Appeals with confirmed emergencies link to that emergency
            resource_uri = '%s/emergencies/%s#overview' % (frontend_url, record.event.id)
        elif rtype != RecordType.APPEAL:
            # One-by-one followed or globally subscribed emergencies
            resource_uri = '%s/%s/%s' % (
                frontend_url,
                'emergencies' if rtype == RecordType.EVENT or rtype == RecordType.FOLLOWED_EVENT else 'reports', # this else never occurs, see ¤
                record.id
            )
        return resource_uri

    def get_admin_uri (self, record, rtype):
        admin_page = {
            RecordType.FIELD_REPORT: 'api/fieldreport',
            RecordType.APPEAL: 'api/appeal',
            RecordType.EVENT: 'api/event',
            RecordType.FOLLOWED_EVENT: 'api/event',
            RecordType.SURGE_DEPLOYMENT_MESSAGES: 'deployments/personneldeployment',
            RecordType.SURGE_ALERT: 'notifications/surgealert',
        }[rtype]
        return 'https://%s/admin/%s/%s/change' % (
            settings.BASE_URL,
            admin_page,
            record.id,
        )

    def get_record_title(self, record, rtype):
        if rtype == RecordType.FIELD_REPORT:
            sendMe = record.summary
            if record.countries.all():
                country = record.countries.all()[0].name
                if country not in sendMe:
                    sendMe = sendMe + ' (' + country + ')'
            return sendMe
        elif rtype == RecordType.SURGE_ALERT:
            return record.operation + ' (' + record.atype.name + ', ' + record.category.name.lower() +')'
        elif rtype == RecordType.SURGE_DEPLOYMENT_MESSAGES:
            return '%s, %s' % (record.country_deployed_to, record.region_deployed_to)
        else:
            return record.name

    def get_record_content(self, record, rtype):
        if rtype == RecordType.FIELD_REPORT:
            sendMe = record.description
        elif rtype == RecordType.APPEAL:
            sendMe = record.sector
            if record.code:
                sendMe += ', ' + record.code
        elif rtype == RecordType.EVENT or rtype == RecordType.FOLLOWED_EVENT:
            sendMe = record.summary
        elif rtype == RecordType.SURGE_ALERT:
            sendMe = record.message
        elif rtype == RecordType.SURGE_DEPLOYMENT_MESSAGES:
            sendMe = record.comments
        else:
            sendMe = '?'
        return html.unescape(sendMe) # For contents we allow HTML markup. = autoescape off in generic_notification.html template.

    def get_record_display(self, rtype, count):
        display = {
            RecordType.FIELD_REPORT: 'field report',
            RecordType.APPEAL: 'operation',
            RecordType.EVENT: 'event',
            RecordType.FOLLOWED_EVENT: 'event',
            RecordType.SURGE_DEPLOYMENT_MESSAGES: 'surge deployment',
            RecordType.SURGE_ALERT: 'surge alert',
        }[rtype]
        if (count > 1):
            display += 's'
        return display

    def get_weekly_digest_data(self, field):
        today = datetime.utcnow().replace(tzinfo=timezone.utc)
        if field == 'dref':
            return Appeal.objects.filter(end_date__gt=today, atype=0).count()
        elif field == 'ea':
            return Appeal.objects.filter(end_date__gt=today, atype=1).count()
        elif field == 'fund':
            amount_req = (
                Appeal.objects
                    .filter(Q(end_date__gt=today, atype=1) | Q(end_date__gt=today, atype=2))
                    .aggregate(Sum('amount_requested'))['amount_requested__sum'] or 0
            )
            amount_fund = (
                Appeal.objects
                    .filter(Q(end_date__gt=today, atype=1) | Q(end_date__gt=today, atype=2))
                    .aggregate(Sum('amount_funded'))['amount_funded__sum'] or 0
            )
            percent = round(amount_fund / amount_req, 3) * 100
            return percent
        elif field == 'budget':
            amount = Appeal.objects.filter(end_date__gt=today).aggregate(Sum('amount_requested'))['amount_requested__sum'] or 0
            rounded_amount = round(amount / 1000000, 2)
            return rounded_amount
        elif field == 'pop':
            people = Appeal.objects.filter(end_date__gt=today).aggregate(Sum('num_beneficiaries'))['num_beneficiaries__sum'] or 0
            rounded_people = round(people / 1000000, 2)
            return rounded_people
    
    def get_weekly_digest_latest_ops(self):
        ops = Appeal.objects.filter(modified_at__gte=self.get_time_threshold_digest()).order_by('-modified_at')
        ret_ops = []
        for op in ops:
            op_to_add = {
                'op_event_id': op.event_id,
                'op_country': Country.objects.values_list('name', flat=True).get(id=op.country_id),
                'op_name': op.name,
                'op_modified_at': op.modified_at,
                'op_funding': op.amount_requested,
            }
            ret_ops.append(op_to_add)
        return ret_ops

    def get_weekly_digest_highlights(self):
        events = Event.objects.filter(is_featured=True, updated_at__gte=self.get_time_threshold_digest()).order_by('-updated_at')
        ret_highlights = []
        for ev in events:
            amount_requested = Appeal.objects.filter(event_id=ev.id).aggregate(Sum('amount_requested'))['amount_requested__sum'] or 0
            amount_funded = Appeal.objects.filter(event_id=ev.id).aggregate(Sum('amount_funded'))['amount_funded__sum'] or 0
            data_to_add = {
                'hl_id': ev.id,
                'hl_name': ev.name,
                'hl_last_update': ev.updated_at,
                'hl_people': Appeal.objects.filter(event_id=ev.id).aggregate(Sum('num_beneficiaries'))['num_beneficiaries'] or 0,
                'hl_funding': amount_requested,
                'hl_deployed_eru': PersonnelDeployment.objects.filter(event_deployed_to_id=ev.id).count(),
                'hl_deployed_sp': '', # TODO: surge personnel, where this comes from
                'hl_coverage': round(amount_funded / amount_requested, 1),
            }
            ret_highlights.append(data_to_add)
        return ret_highlights

    # Based on the notification type this constructs the different type of objects needed for the different templates
    def construct_template_record(self, rtype, record):
        if rtype != RecordType.WEEKLY_DIGEST:
            shortened = self.get_record_content(record, rtype)
            if len(shortened) > max_length:
                shortened = shortened[:max_length] + \
                            shortened[max_length:].split(' ', 1)[0] + '...' # look for the first space

        # TODO: Operation Update and Announcement types are missing
        if rtype == RecordType.FIELD_REPORT:
            rec_obj = {
                'resource_uri': self.get_resource_uri(record, rtype),
                'admin_uri': self.get_admin_uri(record, rtype),
                'title': self.get_record_title(record, rtype),
                'description': shortened,
                'key_figures': {
                    'affected': (record.num_affected or 0) + (record.gov_num_affected or 0) + (record.other_num_affected or 0),
                    'injured': (record.num_injured or 0) + (record.gov_num_injured or 0) + (record.other_num_injured or 0),
                    'dead': (record.num_dead or 0) + (record.gov_num_dead or 0) + (record.other_num_dead or 0),
                    'missing': (record.num_missing or 0) + (record.gov_num_missing or 0) + (record.other_num_missing or 0),
                    'displaced': (record.num_displaced or 0) + (record.gov_num_displaced or 0) + (record.other_num_displaced or 0),
                    'assisted': (record.num_assisted or 0) + (record.gov_num_assisted or 0) + (record.other_num_assisted or 0),
                    'local_staff': record.num_localstaff,
                    'volunteers': record.num_volunteers,
                    'expat_delegates': record.num_expats_delegates,
                },
                'actions_others': record.actions_others, # TODO: check if this is enough or actions needed from other tables
                'assistance': 'Yes' if record.request_assistance else 'No',
            }
        elif rtype == RecordType.NEW_OPERATIONS:
            rec_obj = {
                'resource_uri': self.get_resource_uri(record, rtype),
                'admin_uri': self.get_admin_uri(record, rtype),
                'title': self.get_record_title(record, rtype),
                'situation_overview': Event.objects.values_list('summary', flat=True).get(id=record.event_id),
                'key_figures': {
                    'people_targeted': record.num_beneficaries,
                    'funding_req': record.amount_requested,
                    'appeal_code': record.code,
                    'start_date': record.start_date,
                    'end_date': record.end_date,
                    'local_staff': record.num_localstaff,
                    'volunteers': record.num_volunteers,
                    'expat_delegates': record.num_expats_delegates,
                },
                'field_reports': list(FieldReport.objects.filter(event_id=record.event_id)),
            }
        elif rtype == RecordType.WEEKLY_DIGEST:
            rec_obj = {
                'active_dref': self.get_weekly_digest_data('dref'),
                'active_ea': self.get_weekly_digest_data('ea'),
                'funding_coverage': self.get_weekly_digest_data('fund'),
                'budget': self.get_weekly_digest_data('budget'),
                'population': self.get_weekly_digest_data('pop'),
                'highlighted_ops': self.get_weekly_digest_highlights(),
                'latest_ops': self.get_weekly_digest_latest_ops(),
                'latest_deployments': list(SurgeAlert.objects.filter(created_at__gte=self.get_time_threshold_digest()).order_by('-created_at')),
                'latest_field_reports': list(FieldReport.objects.filter(updated_at__gte=self.get_time_threshold_digest()).order_by('-updated_at')),
            }
        else: # The default (old) template
            rec_obj = {
                'resource_uri': self.get_resource_uri(record, rtype),
                'admin_uri': self.get_admin_uri(record, rtype),
                'title': self.get_record_title(record, rtype),
                'content': shortened,
            }
        return rec_obj

    def notify(self, records, rtype, stype, uid=None):
        record_count = 0
        if records:
            record_count = records.count()
        if not record_count and rtype != RecordType.WEEKLY_DIGEST:
            return

        # Decide if it is a personal notification or batch
        if uid is None:
            emails = self.gather_subscribers(records, rtype, stype)
            if not len(emails):
                return
        else:
            usr = User.objects.filter(pk=uid, is_active=True)
            if not len(usr):
                return
            else:
                emails = list(usr.values_list('email', flat=True))  # Only one email in this case
        
        # TODO: maybe this needs to be adjusted based on the new functionality (at first only handling Weekly Digest)
        # Only serialize the first 10 records
        record_entries = []
        if rtype == RecordType.WEEKLY_DIGEST:
            record_entries.append(self.construct_template_record(rtype, None))
        else:
            entries = list(records) if record_count <= 10 else list(records[:10])
            for record in entries:
                record_entries.append(self.construct_template_record(rtype, record))

        if uid is not None:
            is_staff = usr.values_list('is_staff', flat=True)[0]
        
        if rtype == RecordType.WEEKLY_DIGEST:
            record_type = 'weekly digest'
        else:
            record_type = self.get_record_display(rtype, record_count)
        if uid is None:
            adj = 'new' if stype == SubscriptionType.NEW else 'modified'
            #subject = '%s %s %s in IFRC GO' % (
            if rtype == RecordType.WEEKLY_DIGEST:
                subject = '%s %s' % (
                    adj,
                    record_type,
                )
            else:
                subject = '%s %s %s' % (
                    record_count,
                    adj,
                    record_type,
                )
        else:
            #subject = '%s followed %s modified in IFRC GO' % (
            subject = '%s followed %s modified' % (
                record_count,
                record_type,
            )

        if self.is_retro_mode():
            subject += ' [daily followup]'
        
        template_path = self.get_template()
        if rtype == RecordType.FIELD_REPORT or rtype == RecordType.NEW_OPERATIONS or rtype == RecordType.WEEKLY_DIGEST:
            template_path = self.get_template(rtype)

        # TODO: (mayyybe not needed) Rewrite this based on the template, maybe cut this out into a new function
        html = render_to_string(template_path, {
            'hello': get_hello(),
            'count': record_count,
            'records': record_entries,
            'is_staff': True if uid is None else is_staff, # TODO: fork the sending to "is_staff / not ~" groups
            'subject': subject,
        })
        recipients = emails

        if uid is None:
            if record_count == 1:
                subject += ': ' + record_entries[0]['title'] # On purpose after rendering – the subject changes only, not email body

            # For new (email-documented :10) events we store data to events_sent_to{ event_id: recipients }
            if stype == SubscriptionType.EDIT: # Recently we do not allow EDIT substription
                for e in list(records.values('id'))[:10]:
                    i = e['id']
                    if i not in events_sent_to:
                        events_sent_to[i] = []
                    email_list_to_add = list(set(events_sent_to[i] + recipients))
                    if email_list_to_add:
                        events_sent_to[i] = list(filter(None, email_list_to_add)) # filter to skip empty elements

            plural = '' if len(emails) == 1 else 's' # record_type has its possible plural thanks to get_record_display()
            logger.info('Notifying %s subscriber%s about %s %s %s' % (len(emails), plural, record_count, adj, record_type))
            send_notification(subject, recipients, html)
        else:
            if len(recipients):
                # check if email is not in events_sent_to{event_id: recipients}
                if not emails:
                    logger.info('Silent about the one-by-one subscribed %s – user %s has not set email address' % (record_type, uid))
                # Recently we do not allow EDIT (modif.) subscription, so it is irrelevant recently (do not check the 1+ events in loop) :
                elif (records[0].id not in events_sent_to) or (emails[0] not in events_sent_to[records[0].id]):
                    logger.info('Notifying %s subscriber about %s one-by-one subscribed %s' % (len(emails), record_count, record_type))
                    send_notification(subject, recipients, html)
                else:
                    logger.info('Silent about a one-by-one subscribed %s – user already notified via generic subscription' % (record_type))


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
            created, errors = bulk(client=ES_CLIENT , actions=actions)
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
        if hasattr(queryset.first(), 'modified_at') and queryset.first().modified_at is not None:
            return [record for record in queryset if (
                record.modified_at.replace(microsecond=0) == record.created_at.replace(microsecond=0))]
        else:
            return [record for record in queryset if (
                record.updated_at.replace(microsecond=0) == record.created_at.replace(microsecond=0))]


    def handle(self, *args, **options):
        if self.is_digest_mode():
            t = self.get_time_threshold_digest() # in digest mode (1ce a week, for new_entities only) we use a bigger interval
        else:
            t = self.get_time_threshold()
        t2 = self.get_time_threshold2()

        cond1 = Q(created_at__gte=t)
        condU = Q(updated_at__gte=t)
        condR = Q(real_data_update__gte=t) # instead of modified at
        cond2 = ~Q(previous_update__gte=t2) # we negate (~) this, so we want: no previous_update in the last day. So: send once a day!
        condF = Q(auto_generated_source='New field report') # We exclude those events that were generated from field reports, to avoid 2x notif.

        # In this section we check if there was 2 FOLLOWED_EVENT modifications in the last 24 hours (for which there was no duplicated email sent, but now will be one).
        if self.is_retro_mode():
            condU = Q(updated_at__gte=t2)
            cond2 = Q(previous_update__gte=t2) # not negated. We collect those, who had 2 changes in the last 1 day.
            followed_eventparams = Subscription.objects.filter(event_id__isnull=False)
            users_of_followed_events = followed_eventparams.values_list('user_id', flat=True).distinct()
            for usr in users_of_followed_events: # looping in user_ids of specific FOLLOWED_EVENT subscriptions (8)
                eventlist = followed_eventparams.filter(user_id=usr).values_list('event_id', flat=True).distinct()
                cond3 = Q(pk__in=eventlist) # getting their events as a condition
                followed_events = Event.objects.filter(condU & cond2 & cond3)
                if len(followed_events): # usr - unique (we loop one-by-one), followed_events - more
                    self.notify(followed_events, RecordType.FOLLOWED_EVENT, SubscriptionType.NEW, usr)
        else:
            new_reports = FieldReport.objects.filter(cond1)
            updated_reports = FieldReport.objects.filter(condU & cond2)

            new_appeals = Appeal.objects.filter(cond1)
            updated_appeals = Appeal.objects.filter(condR & cond2)

            new_events = Event.objects.filter(cond1).exclude(condF)
            updated_events = Event.objects.filter(condU & cond2)

            new_surgealerts = SurgeAlert.objects.filter(cond1)

            new_pers_deployments = PersonnelDeployment.objects.filter(cond1) # CHECK: Best instantiation of Deployment Messages? Frontend appearance?!?
            # No need for indexing for personnel deployments

            # Approaching End of Mission ? new_approanching_end = PersonnelDeployment.objects.filter(end-date is close?)
            # No need for indexing for Approaching End of Mission

            # PER Due Dates ? new_per_due_date_warnings = User.objects.filter(PER admins of countries/regions, for whom the setting/per_due_date is in 1 week)
            # No need for indexing for PER Due Dates

            followed_eventparams = Subscription.objects.filter(event_id__isnull=False)
            ## followed_events = Event.objects.filter(updated_at__gte=t, pk__in=[x.event_id for x in followed_eventparams])

            # TODO: check how this really works
            # Merge Weekly Digest into one mail instead of separate ones
            if self.is_digest_mode():
                self.notify(None, RecordType.WEEKLY_DIGEST, SubscriptionType.NEW)
            else:
                self.notify(new_reports, RecordType.FIELD_REPORT, SubscriptionType.NEW)
                #self.notify(updated_reports, RecordType.FIELD_REPORT, SubscriptionType.EDIT)

                self.notify(new_appeals, RecordType.APPEAL, SubscriptionType.NEW)
                #self.notify(updated_appeals, RecordType.APPEAL, SubscriptionType.EDIT)

                self.notify(new_events, RecordType.EVENT, SubscriptionType.NEW)
                #self.notify(updated_events, RecordType.EVENT, SubscriptionType.EDIT)

                self.notify(new_surgealerts, RecordType.SURGE_ALERT, SubscriptionType.NEW)

                self.notify(new_pers_deployments, RecordType.SURGE_DEPLOYMENT_MESSAGES, SubscriptionType.NEW)

            users_of_followed_events = followed_eventparams.values_list('user_id', flat=True).distinct()
            for usr in users_of_followed_events: # looping in user_ids of specific FOLLOWED_EVENT subscriptions (8)
                eventlist = followed_eventparams.filter(user_id=usr).values_list('event_id', flat=True).distinct()
                cond3 = Q(pk__in=eventlist) # getting their events as a condition
                followed_events = Event.objects.filter(condU & cond2 & cond3)
                if len(followed_events): # usr - unique (we loop one-by-one), followed_events - more
                    self.notify(followed_events, RecordType.FOLLOWED_EVENT, SubscriptionType.NEW, usr)

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
