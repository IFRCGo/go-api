from dateutil import parser as date_parser
import json
from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from api.molnix_utils import MolnixApi
from api.logger import logger
from deployments.models import MolnixTag, PersonnelDeployment, Personnel
from notifications.models import SurgeAlert, SurgeAlertType, SurgeAlertCategory
from api.models import Event, Country, CronJobStatus
from api.create_cron import create_cron_record

CRON_NAME = 'sync_molnix'

def get_unique_tags(deployments, open_positions):
    tags = []
    tag_ids = []
    for deployment in deployments:
        for tag in deployment['tags']:
            if tag['id'] not in tag_ids:
                tags.append(tag)
                tag_ids.append(tag['id'])
    return tags


def add_tags(molnix_tags):
    for molnix_tag in molnix_tags:
        tag, created = MolnixTag.objects.get_or_create(molnix_id=molnix_tag['id'])
        tag.molnix_id = molnix_tag['id']
        tag.name = molnix_tag['name']
        tag.description = molnix_tag['description']
        tag.tag_type = molnix_tag['type']
        tag.save()
        print('saved tag %s' % tag.name)



def get_go_event(tags):
    '''
        Returns a GO Event object, by looking for a tag like `OP-<event_id>` or
        None if there is not a valid OP- tag on the Position
    '''
    event = None
    for tag in tags:
        if tag['name'].startswith('OP-'):
            event_id = tag['name'].replace('OP-', '').strip()
            try:
                event_id_int = int(event_id)
            except:
                logger.warn('%s tag is not a valid OP- tag' % event_id)
                continue
            try:
                event = Event.objects.get(id=event_id_int)
            except:
                logger.warn('Emergency with ID %d not found' % event_id_int)
                continue
            return event
    return event


def get_datetime(datetime_string):
    '''
        Return a python datetime from a date-time string from the API
    '''
    if not datetime_string or datetime_string == '':
        return None
    return date_parser.parse(datetime_string)


def add_tags_to_obj(obj, tags):
    # We clear all tags first, and then re-add them
    tag_molnix_ids = [t['id'] for t in tags]
    obj.molnix_tags.clear()
    for molnix_id in tag_molnix_ids:
        try:
            t = MolnixTag.objects.get(molnix_id=molnix_id)
        except:
            print('ERROR: %d' % molnix_id)
            continue
        obj.molnix_tags.add(t)
    obj.save()

    

def sync_deployments(molnix_deployments):
    molnix_ids = [d['id'] for d in molnix_deployments]

    # Ensure there are PersonnelDeployment instances for every unique emergency
    events = [get_go_event(d['tags']) for d in molnix_deployments]
    event_ids = [ev.id for ev in events if ev]
    unique_event_ids = list(set(event_ids))
    for event_id in unique_event_ids:
        if PersonnelDeployment.objects.filter(is_molnix=True, event_deployed_to=event_id).count() == 0:
            event = Event.objects.get(pk=event_id)
            p = PersonnelDeployment()
            p.event_deployed_to = event

            # FIXME: check if country exists, etc.
            p.country_deployed_to = p.event_deployed_to.countries.all()[0]
            p.region_deployed_to = p.event_deployed_to.countries.all()[0].region
            p.is_molnix = True
            p.save()
            print('saved Personnel Deployment!')
    
    # Create Personnel objects
    for md in molnix_deployments:
        print(md)
        try:
            personnel = Personnel.objects.get(molnix_id=md['id'])
        except:
            personnel = Personnel(molnix_id=md['id'])
        # print('personnel found', personnel)
        event = get_go_event(md['tags'])
        if not event:
            print('NOT EVENT')
            continue
        deployment = PersonnelDeployment.objects.get(is_molnix=True, event_deployed_to=event)
        print('deployment', deployment.id)
        personnel.deployment = deployment
        personnel.molnix_id = md['id']
        personnel.is_active = True
        personnel.type = Personnel.RR
        personnel.start_date = get_datetime(md['start'])
        personnel.end_date = get_datetime(md['end'])
        personnel.name = md['person']['fullname']
        personnel.role = md['title']
        try:
            personnel.country_from = Country.objects.get(society_name=md['secondment_incoming'])
        except:
            personnel.country_from = None
        personnel.save()
        add_tags_to_obj(personnel, md['tags'])
        print('saved %s' % personnel.name)

    all_active_personnel = Personnel.objects.filter(is_active=True, molnix_id__isnull=False)
    active_personnel_ids = [a.id for a in all_active_personnel]
    inactive_ids = list(set(active_personnel_ids) - set(molnix_ids))
    
    # Mark Personnel entries no longer in Molnix as inactive:

    for id in inactive_ids:
        personnel = Personnel.objects.get(pk=id)
        personnel.is_active = False
        personnel.save()


def sync_open_positions(molnix_positions):
    molnix_ids = [p['id'] for p in molnix_positions]
    for position in molnix_positions:
        event = get_go_event(position['tags'])

        # If no valid GO Emergency tag is found, skip Position
        if not event:
            logger.warn('Position id %d does not have an Emergency tag.' % position['id'])
            continue
        go_alert, created = SurgeAlert.objects.get_or_create(molnix_id=position['id'])

        # We set all Alerts coming from Molnix to RR / Alert
        go_alert.atype = SurgeAlertType.RAPID_RESPONSE
        go_alert.category = SurgeAlertCategory.ALERT        
        # print(json.dumps(position, indent=2))
        go_alert.molnix_id = position['id']
        go_alert.message = position['name']
        go_alert.event = event
        go_alert.opens = get_datetime(position['opens'])
        go_alert.closes = get_datetime(position['closes'])
        go_alert.start = get_datetime(position['start'])
        go_alert.end = get_datetime(position['end'])
        go_alert.is_active = True
        go_alert.save()
        add_tags_to_obj(go_alert, position['tags'])
        print('SurgeAlert saved: %s' % go_alert.message)
    
    # Find existing active alerts that are not in the current list from Molnix
    existing_alerts = SurgeAlert.objects.filter(is_active=True).exclude(molnix_id__isnull=True)
    existing_alert_ids = [e.molnix_id for e in existing_alerts]
    inactive_alerts = list(set(existing_alert_ids) - set(molnix_ids))

    # Mark alerts that are no longer in Molnix as inactive
    for alert in SurgeAlert.objects.filter(molnix_id__in=inactive_alerts):
        alert.is_active = False
        alert.save()


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
            msg = 'Failed to login to Molnix API: %s' % str(ex)
            logger.error(msg)
            create_cron_record(CRON_NAME, msg, CronJobStatus.ERRONEOUS)
            return
        try:
            # tags = molnix.get_tags()
            deployments = molnix.get_deployments()
            open_positions = molnix.get_open_positions()
        except Exception as ex:
            msg = 'Failed to fetch data from Molnix API: %s' % str(ex)
            logger.error(msg)
            create_cron_record(CRON_NAME, msg, CronJobStatus.ERRONEOUS)
            return

        try:    
            used_tags = get_unique_tags(deployments, open_positions)
            add_tags(used_tags)
            sync_open_positions(open_positions)
            sync_deployments(deployments)
        except Exception as ex:
            msg = 'Unknown Error occurred: %s' % str(ex)
            logger.error(msg)
            create_cron_record(CRON_NAME, msg, CronJobStatus.ERRONEOUS)
            return
        
        create_cron_record(CRON_NAME, 'success', CronJobStatus.SUCCESSFUL)
        molnix.logout()
