from datetime import datetime, timezone, timedelta
from django.db.models import Q, F, ExpressionWrapper, DurationField, Sum
from django.db.models.query import QuerySet
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.template.loader import render_to_string
from elasticsearch.helpers import bulk
from utils.elasticsearch import construct_es_data
from api.esconnection import ES_CLIENT
from api.models import UserRegion, Region, Event, ActionsTaken, CronJob, CronJobStatus, Profile
from api.logger import logger
from notifications.models import RecordType, SubscriptionType, Subscription, SurgeAlert
from notifications.hello import get_hello
from notifications.notification import send_notification
from deployments.models import PersonnelDeployment, ERU, Personnel
from main.frontend import frontend_url
from registrations.models import Pending
from notifications.notification import send_notification
import html


time_3_day = timedelta(days=3)



class Command(BaseCommand):
    help = 'Send reminder about the pending registrations'

    def diff_3_day(self):
        return datetime.utcnow().replace(tzinfo=timezone.utc) - time_3_day

    def handle(self, *args, **options):
        region_ids = Region.objects.all().values_list('id', flat=True)
        time_diff_3_day = self.diff_3_day()
        
        for region_id in region_ids:
            region_admin_emails = list(UserRegion.objects.filter(region_id = region_id).values_list('user__email',flat=True))
            pending3days = Pending.objects.filter(user__profile__country__region_id=region_id).filter(reminder_sent_to_admin=False).filter(created_at__lte=time_diff_3_day)
            userlist = self.create_html_list_of_pending_users(pending3days)
            
            email_context = {
                   'userlist': userlist,
                }
          
            if len(pending3days)>0 and len(region_admin_emails)>0 :
                
                send_notification('Pending registrations for more than 3 days',
                                region_admin_emails,
                                render_to_string('email/registration/reminder.html', email_context),
                                'Reminder')

                pending3days.update(reminder_sent_to_admin=True)


    def create_html_list_of_pending_users(self, pendings):
        retval = '<ul>'
        for pending in pendings:
            retval += '<li>'
            retval += pending.user.email
            retval += '</li>'
        retval +='</ul>'
        return retval
