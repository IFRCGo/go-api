from datetime import datetime, timezone, timedelta
from django.db.models import Q, F, ExpressionWrapper, DurationField, Sum
from django.db.models.query import QuerySet
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.template.loader import render_to_string
from elasticsearch.helpers import bulk
from api.indexes import ES_PAGE_NAME
from api.esconnection import ES_CLIENT
from api.models import Country, Appeal, Event, FieldReport, ActionsTaken, CronJob, CronJobStatus
from api.logger import logger
from notifications.models import RecordType, SubscriptionType, Subscription, SurgeAlert
from notifications.hello import get_hello
from notifications.notification import send_notification
from deployments.models import PersonnelDeployment, ERU, Personnel
from main.frontend import frontend_url
import html

time_5_minutes = timedelta(minutes = 5)
time_1_day = timedelta(days = 1) # to check: the change was not between time_interval and time_interva2, so that the user don't receive email more frequent than a day.
time_1_week = timedelta(days = 7) # for digest mode
digest_time = int(10314) # weekday - hour - min for digest timing (5 minutes once a week, Monday dawn)
daily_retro = int(654) # hour - min for daily retropective email timing (5 minutes a day) | Should not contain a leading 0!
max_length = 860 # after this length (at the first space) we cut the sent content
events_sent_to = {} # to document sent events before re-sending them via specific following
template_types = {
    99: 'design/generic_notification.html',
    RecordType.FIELD_REPORT: 'design/field_report.html',
    RecordType.APPEAL: 'design/new_operation.html',
    98: 'design/operation_update.html', # TODO: Either Operation Update needs a number or it should be constructed from other types (ask someone)
    RecordType.WEEKLY_DIGEST: 'design/weekly_digest.html',
}

class Command(BaseCommand):
    help = 'Index and send notifications about new/changed records'

    # Digest mode duration is 5 minutes once a week
    def is_digest_mode(self):
        today = datetime.utcnow().replace(tzinfo=timezone.utc)
        weekdayhourmin = int(today.strftime('%w%H%M'))
        return digest_time <= weekdayhourmin and weekdayhourmin < digest_time + 5

    def is_daily_checkup_time(self):
        today = datetime.utcnow().replace(tzinfo=timezone.utc)
        hourmin = int(today.strftime('%H%M'))
        return daily_retro <= hourmin and hourmin < daily_retro + 5

    def diff_5_minutes(self):
        return datetime.utcnow().replace(tzinfo=timezone.utc) - time_5_minutes

    def diff_1_day(self):
        return datetime.utcnow().replace(tzinfo=timezone.utc) - time_1_day

    def diff_1_week(self):
        return datetime.utcnow().replace(tzinfo=timezone.utc) - time_1_week

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
            belonging_event = record.event.id if record.event is not None else 57 # Very rare – giving a non-existent
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
            percent = float(round(amount_fund / amount_req, 3) * 100) if amount_req != 0 else 0
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
        dig_time = self.diff_1_week()
        ops = Appeal.objects.filter(created_at__gte=dig_time).order_by('-created_at')
        ret_ops = []
        for op in ops:
            op_to_add = {
                'op_event_id': op.event_id,
                'op_country': Country.objects.values_list('name', flat=True).get(id=op.country_id) if op.country_id else '',
                'op_name': op.name,
                'op_created_at': op.created_at,
                'op_funding': float(op.amount_requested),
            }
            ret_ops.append(op_to_add)
        return ret_ops

    def get_weekly_digest_latest_deployments(self):
        dig_time = self.diff_1_week()
        ret_data = []

        # Surge Alerts
        # surge_list = list(SurgeAlert.objects.filter(created_at__gte=dig_time).order_by('-created_at'))
        # if surge_list:
        #     for alert in surge_list:
        #         event = Event.objects.get(id=alert.event_id) if alert.event_id != None else None
        #         alert_to_add = {
        #             'type': 'Alert',
        #             'operation': alert.operation,
        #             'event_url': '{}/emergencies/{}#overview'.format(frontend_url, event.id) if event else frontend_url,
        #             'society_from': '',
        #             'deployed_to': '',
        #             'name': '',
        #             'role': '',
        #             'appeal': '',
        #         }
        #         ret_data.append(alert_to_add)

        # Surge Deployments
        personnel_list = Personnel.objects.filter(start_date__gte=dig_time).order_by('start_date')
        for pers in personnel_list:
            deployment = PersonnelDeployment.objects.get(id=pers.deployment_id)
            event = Event.objects.get(id=deployment.event_deployed_to_id) if deployment.event_deployed_to_id != None else None
            country_from = Country.objects.get(id=pers.country_from_id) if pers.country_from_id != None else None
            dep_to_add = {
                'operation': event.name if event else '',
                'event_url': '{}/emergencies/{}#overview'.format(frontend_url, event.id) if event else frontend_url,
                'society_from': country_from.society_name if country_from else '',
                'name': pers.name,
                'role': pers.role,
                'start_date': pers.start_date,
                'end_date': pers.end_date,
            }
            ret_data.append(dep_to_add)

        return ret_data


    def get_weekly_digest_highlights(self):
        dig_time = self.diff_1_week()
        events = Event.objects.filter(is_featured=True, updated_at__gte=dig_time).order_by('-updated_at')
        ret_highlights = []
        for ev in events:
            amount_requested = Appeal.objects.filter(event_id=ev.id).aggregate(Sum('amount_requested'))['amount_requested__sum'] or '--'
            amount_funded = Appeal.objects.filter(event_id=ev.id).aggregate(Sum('amount_funded'))['amount_funded__sum'] or '--'
            coverage = '--'
            
            if amount_funded != '--' and amount_requested != '--':
                coverage = round(amount_funded / amount_requested, 1) if amount_requested != 0 else 0
            
            data_to_add = {
                'hl_id': ev.id,
                'hl_name': ev.name,
                'hl_last_update': ev.updated_at,
                'hl_people': Appeal.objects.filter(event_id=ev.id).aggregate(Sum('num_beneficiaries'))['num_beneficiaries__sum'] or '--',
                'hl_funding': amount_requested,
                'hl_deployed_eru': ERU.objects.filter(event_id=ev.id).aggregate(Sum('units'))['units__sum'] or '--',
                'hl_deployed_sp': PersonnelDeployment.objects.filter(event_deployed_to_id=ev.id).count(),
                'hl_coverage': coverage,
            }
            ret_highlights.append(data_to_add)
        return ret_highlights

    def get_actions_taken(self, frid):
        ret_actions_taken = {
            'NTLS': [],
            'PNS': [],
            'FDRN': [],
        }
        actions_taken = ActionsTaken.objects.filter(field_report_id=frid)
        for at in actions_taken:
            action_to_add = {
                'action_summary': at.summary,
                'actions': [],
            }
            if at.actions.all():
                for act in at.actions.all():
                    action_to_add['actions'].append(act)
            if at.organization == 'NTLS':
                ret_actions_taken['NTLS'].append(action_to_add)
            elif at.organization == 'PNS':
                ret_actions_taken['PNS'].append(action_to_add)
            elif at.organization == 'FDRN':
                ret_actions_taken['FDRN'].append(action_to_add)
        return ret_actions_taken

    def get_weekly_latest_frs(self):
        dig_time = self.diff_1_week()
        ret_fr_list = []
        fr_list = list(FieldReport.objects.filter(created_at__gte=dig_time).order_by('-created_at'))
        for fr in fr_list:
            fr_data = {
                'id': fr.id,
                'country': fr.countries.all()[0].name if fr.countries else None,
                'summary': fr.summary,
                'created_at': fr.created_at,
            }
            ret_fr_list.append(fr_data)
        return ret_fr_list

    def get_fieldreport_keyfigures(self, num_list):
        is_none = all(num == None for num in num_list)
        if is_none:
            return '--'

        return float(sum(filter(None, num_list)))

    # Based on the notification type this constructs the different type of objects needed for the different templates
    def construct_template_record(self, rtype, record):
        if rtype != RecordType.WEEKLY_DIGEST:
            shortened = self.get_record_content(record, rtype)
            if len(shortened) > max_length:
                shortened = shortened[:max_length] + \
                            shortened[max_length:].split(' ', 1)[0] + '...' # look for the first space

        if rtype == RecordType.FIELD_REPORT:
            rec_obj = {
                'resource_uri': self.get_resource_uri(record, rtype),
                'admin_uri': self.get_admin_uri(record, rtype),
                'title': self.get_record_title(record, rtype),
                'description': shortened,
                'key_figures': {
                    'affected': self.get_fieldreport_keyfigures([record.num_affected, record.gov_num_affected, record.other_num_affected]),
                    'injured': self.get_fieldreport_keyfigures([record.num_injured, record.gov_num_injured, record.other_num_injured]),
                    'dead': self.get_fieldreport_keyfigures([record.num_dead, record.gov_num_dead, record.other_num_dead]),
                    'missing': self.get_fieldreport_keyfigures([record.num_missing, record.gov_num_missing, record.other_num_missing]),
                    'displaced': self.get_fieldreport_keyfigures([record.num_displaced, record.gov_num_displaced, record.other_num_displaced]),
                    'assisted': self.get_fieldreport_keyfigures([record.num_assisted, record.gov_num_assisted, record.other_num_assisted]),
                    # 'local_staff': record.num_localstaff or '--',
                    # 'volunteers': record.num_volunteers or '--',
                    # 'expat_delegates': record.num_expats_delegates or '--',
                },
                'epi_key_figures': { #TODO: rework this too
                    'who_cases': record.who_cases or '--',
                    'who_suspected': record.who_suspected_cases or '--',
                    'who_probable': record.who_probable_cases or '--',
                    'who_confirmed': record.who_confirmed_cases or '--',
                    'who_dead': record.who_num_dead or '--',
                    'health_cases': record.health_min_cases or '--',
                    'health_suspected': record.health_min_suspected_cases or '--',
                    'health_probable': record.health_min_probable_cases or '--',
                    'health_confirmed': record.health_min_confirmed_cases or '--',
                    'health_dead': record.health_min_num_dead or '--',
                    'other_cases': record.other_cases or '--',
                    'other_suspected': record.other_suspected_cases or '--',
                    'other_probable': record.other_probable_cases or '--',
                    'other_confirmed': record.other_confirmed_cases or '--',
                    'other_dead': record.other_num_dead or '--', # not sure but couldn't find other related field
                },
                'sit_fields_date': record.sit_fields_date,
                'actions_taken': self.get_actions_taken(record.id),
                'actions_others': record.actions_others,
                'gov_assistance': 'Yes' if record.request_assistance else 'No',
                'ns_assistance': 'Yes' if record.ns_request_assistance else 'No',
                'dtype_id': record.dtype_id,
            }
        elif rtype == RecordType.APPEAL:
            # localstaff = FieldReport.objects.filter(event_id=record.event_id).values_list('num_localstaff', flat=True)
            # volunteers = FieldReport.objects.filter(event_id=record.event_id).values_list('num_volunteers', flat=True)
            # expats = FieldReport.objects.filter(event_id=record.event_id).values_list('num_expats_delegates', flat=True)
            optypes = {
                0: 'DREF',
                1: 'Emergency Appeal',
                2: 'International Appeal',
            }
            rec_obj = {
                'resource_uri': self.get_resource_uri(record, rtype),
                'follow_url': '{}/account#notifications'.format(frontend_url),
                'admin_uri': self.get_admin_uri(record, rtype),
                'title': self.get_record_title(record, rtype),
                'situation_overview': Event.objects.values_list('summary', flat=True).get(id=record.event_id) if record.event_id != None else '',
                'key_figures': {
                    'people_targeted': float(record.num_beneficiaries),
                    'funding_req': float(record.amount_requested),
                    'appeal_code': record.code,
                    'start_date': record.start_date,
                    'end_date': record.end_date,
                    # 'local_staff': localstaff[0] if localstaff else 0,
                    # 'volunteers': volunteers[0] if volunteers else 0,
                    # 'expat_delegates': expats[0] if expats else 0,
                },
                'operation_type': optypes[record.atype],
                'field_reports': list(FieldReport.objects.filter(event_id=record.event_id)) if record.event_id != None else None,
            }
        elif rtype == RecordType.WEEKLY_DIGEST:
            dig_time = self.diff_1_week()
            rec_obj = {
                'active_dref': self.get_weekly_digest_data('dref'),
                'active_ea': self.get_weekly_digest_data('ea'),
                'funding_coverage': self.get_weekly_digest_data('fund'),
                'budget': self.get_weekly_digest_data('budget'),
                'population': self.get_weekly_digest_data('pop'),
                'highlighted_ops': self.get_weekly_digest_highlights(),
                'latest_ops': self.get_weekly_digest_latest_ops(),
                'latest_deployments': self.get_weekly_digest_latest_deployments(),
                'latest_field_reports': self.get_weekly_latest_frs(),
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
            if isinstance(records, QuerySet):
                record_count = records.count()
            elif isinstance(records, list):
                record_count = len(records)
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
                subject = '%s' % (
                    record_type,
                )
                # subject = '%s %s' % (
                #     adj,
                #     record_type,
                # )
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

        if self.is_daily_checkup_time():
            subject += ' [daily followup]'
        
        template_path = self.get_template()
        if rtype == RecordType.FIELD_REPORT or rtype == RecordType.APPEAL or rtype == RecordType.WEEKLY_DIGEST:
            template_path = self.get_template(rtype)

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
            send_notification(subject, recipients, html, True if rtype == RecordType.FOLLOWED_EVENT else False)
        else:
            if len(recipients):
                # check if email is not in events_sent_to{event_id: recipients}
                if not emails:
                    logger.info('Silent about the one-by-one subscribed %s – user %s has not set email address' % (record_type, uid))
                # Recently we do not allow EDIT (modif.) subscription, so it is irrelevant recently (do not check the 1+ events in loop) :
                elif (records[0].id not in events_sent_to) or (emails[0] not in events_sent_to[records[0].id]):
                    logger.info('Notifying %s subscriber about %s one-by-one subscribed %s' % (len(emails), record_count, record_type))
                    send_notification(subject, recipients, html, True if rtype == RecordType.FOLLOWED_EVENT else False)
                else:
                    logger.info('Silent about a one-by-one subscribed %s – user already notified via generic subscription' % (record_type))

    
    def index_records(self, records, to_create=True):
        self.bulk([self.convert_for_bulk(record, create=to_create) for record in list(records)])


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


    def check_ingest_issues(self, having_ingest_issue):
        # having_ingest_issue = CronJob.objects.raw('SELECT * FROM api_cronjob WHERE status=' + str(CronJobStatus.ERRONEOUS.value))
        ingest_issue_id = having_ingest_issue[0].id if len(having_ingest_issue) > 0 else -1
        ingestor_name = having_ingest_issue[0].name if len(having_ingest_issue) > 0 else ''
        if len(having_ingest_issue) > 0:
            #                                Would be better in ENV variable:
            send_notification('API monitor – ingest issues!', ['im@ifrc.org'], 'Ingest issue(s) occured, one of them is ' + ingestor_name + ', via CronJob log record id: https://' +
                settings.BASE_URL + '/api/cronjob/' + str(ingest_issue_id) + '. Please fix it ASAP.')
            logger.info('Ingest issue occured, e.g. by ' + ingestor_name + ', via CronJob log record id: ' + str(ingest_issue_id) + ', notification sent to IM team')


    def handle(self, *args, **options):
        if self.is_digest_mode():
            time_diff = self.diff_1_week() # in digest mode (once a week, for new_entities only) we use a bigger interval
        else:
            time_diff = self.diff_5_minutes()
        time_diff_1_day = self.diff_1_day()

        cond1 = Q(created_at__gte=time_diff)
        condU = Q(updated_at__gte=time_diff)
        condR = Q(real_data_update__gte=time_diff) # instead of modified at
        cond2 = ~Q(previous_update__gte=time_diff_1_day) # we negate (~) this, so we want: no previous_update in the last day. So: send once a day!
        condF = Q(auto_generated_source='New field report') # We exclude those events that were generated from field reports, to avoid 2x notif.
        condE = Q(status=CronJobStatus.ERRONEOUS)

        # ".annotate(diff...)" - To check if a record was newly created, we check if
        # `created_at` and `updated_at` are within one minute of each other, since those values
        # can be off by some miliseconds upon insertion. (could be seconds too perhaps)
        new_reports = FieldReport.objects.filter(cond1)
        updated_reports = FieldReport.objects.annotate(
            diff = ExpressionWrapper(F('updated_at') - F('created_at'), output_field=DurationField())
        ).filter(condU & cond2 & Q(diff__gt=timedelta(minutes=1)))

        new_appeals = Appeal.objects.filter(cond1)
        updated_appeals = Appeal.objects.annotate(
            diff = ExpressionWrapper(F('real_data_update') - F('created_at'), output_field=DurationField())
        ).filter(condR & cond2 & Q(diff__gt=timedelta(minutes=1)))

        new_events = Event.objects.filter(cond1).exclude(condF)
        updated_events = Event.objects.annotate(
            diff = ExpressionWrapper(F('updated_at') - F('created_at'), output_field=DurationField())
        ).filter(condU & cond2 & Q(diff__gt=timedelta(minutes=1)))

        new_surgealerts = SurgeAlert.objects.filter(cond1)
        new_pers_deployments = PersonnelDeployment.objects.filter(cond1)

        # Merge Weekly Digest into one mail instead of separate ones
        if self.is_digest_mode():
            self.notify(None, RecordType.WEEKLY_DIGEST, SubscriptionType.NEW)
        
        self.notify(new_reports, RecordType.FIELD_REPORT, SubscriptionType.NEW)
        #self.notify(updated_reports, RecordType.FIELD_REPORT, SubscriptionType.EDIT)
        self.notify(new_appeals, RecordType.APPEAL, SubscriptionType.NEW)
        #self.notify(updated_appeals, RecordType.APPEAL, SubscriptionType.EDIT)
        self.notify(new_events, RecordType.EVENT, SubscriptionType.NEW)
        #self.notify(updated_events, RecordType.EVENT, SubscriptionType.EDIT)
        self.notify(new_surgealerts, RecordType.SURGE_ALERT, SubscriptionType.NEW)
        self.notify(new_pers_deployments, RecordType.SURGE_DEPLOYMENT_MESSAGES, SubscriptionType.NEW)

        # Followed Events
        if self.is_daily_checkup_time():
            condU = Q(updated_at__gte=time_diff_1_day)
            cond2 = Q(previous_update__gte=time_diff_1_day) # not negated, we collect those, who had 2 changes in the last 1 day

        fe_subs = Subscription.objects.filter(event_id__isnull=False) # subscriptions of FEs
        subscribers = fe_subs.values_list('user_id', flat=True).distinct()
        for usr in subscribers: # looping in user_ids of specific FOLLOWED_EVENT subscriptions
            eventlist = fe_subs.filter(user_id=usr).values_list('event_id', flat=True).distinct()
            cond3 = Q(pk__in=eventlist)
            followed_events = Event.objects.filter(condU & cond2 & cond3)
            if len(followed_events): # usr - unique (we loop one-by-one), followed_events - more
                self.notify(followed_events, RecordType.FOLLOWED_EVENT, SubscriptionType.NEW, usr)

        # Indexing
        logger.info('Indexing %s new field reports' % new_reports.count())
        self.index_records(new_reports)
        logger.info('Indexing %s new appeals' % new_appeals.count())
        self.index_records(new_appeals)
        logger.info('Indexing %s new events' % new_events.count())
        self.index_records(new_events)

        logger.info('Indexing %s updated field reports' % updated_reports.count())
        self.index_records(updated_reports, to_create=False)
        logger.info('Indexing %s updated appeals' % updated_appeals.count())
        self.index_records(updated_appeals, to_create=False)
        logger.info('Indexing %s updated events' % updated_events.count())
        self.index_records(updated_events, to_create=False)
        

        # CronJob feedback of smtp server working is in: notifications/notification.py
        having_ingest_issue = CronJob.objects.filter(cond1 & condE)
        self.check_ingest_issues(having_ingest_issue)
        logger.info('API monitoring. Ingest issues are checked.')
