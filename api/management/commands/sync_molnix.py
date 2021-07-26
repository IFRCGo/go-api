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

'''
    Some NS names coming from Molnix are mapped to "countries"
    in the GO db via this mapping below, as the NS names do not line up.
'''
NS_MATCHING_OVERRIDES = {
    'Red Cross Society of China-Hong Kong Branch': 'China',
    'Macau Red Cross': 'China',
    'Ifrc Headquarters': 'IFRC',
    'Ifrc Mena': 'IFRC',
    'Ifrc Asia Pacific': 'IFRC',
    'Ifrc Africa': 'IFRC',
    'Ifrc Americas': 'IFRC',
    'Ifrc Europe': 'IFRC',
    'IFRC': 'IFRC',
    'Icrc Staff': 'ICRC'
}

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
                logger.warning('%s tag is not a valid OP- tag' % event_id)
                continue
            try:
                event = Event.objects.get(id=event_id_int)
            except:
                logger.warning('Emergency with ID %d not found' % event_id_int)
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

def get_status_message(positions_messages, deployments_messages, positions_warnings, deployments_warnings):
    msg = ''
    msg += 'Summary of Open Positions Import:\n\n'
    msg += '\n'.join(positions_messages)
    msg += '\n\n'
    msg += 'Summary of Deployments Import:\n\n'
    msg += '\n'.join(deployments_messages)
    msg += '\n\n'
    if len(positions_warnings) > 0:
        msg += 'Warnings for Open Positions Imports:\n\n'
        msg += '\n'.join(positions_warnings)
        msg += '\n\n'
    if len(deployments_warnings) > 0:
        msg += 'Warnings for Deployment Imports:\n\n'
        msg += '\n'.join(deployments_warnings)
        msg += '\n\n'
    return msg

def add_tags_to_obj(obj, tags):
    # We clear all tags first, and then re-add them
    tag_molnix_ids = [t['id'] for t in tags]
    obj.molnix_tags.clear()
    for molnix_id in tag_molnix_ids:
        try:
            t = MolnixTag.objects.get(molnix_id=molnix_id)
        except:
            logger.error('ERROR - tag not found: %d' % molnix_id)
            continue
        obj.molnix_tags.add(t)
    obj.save()

    

def sync_deployments(molnix_deployments):
    #import json
    #print(json.dumps(molnix_deployments, indent=2))
    molnix_ids = [d['id'] for d in molnix_deployments]

    warnings = []
    messages = []
    successful_creates = 0
    successful_updates = 0
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
            if p.event_deployed_to.countries.all().count() > 0:
                p.country_deployed_to = p.event_deployed_to.countries.all()[0]
                p.region_deployed_to = p.event_deployed_to.countries.all()[0].region
            else:
                warning = 'Event id %d without country' % p.event_deployed_to.id
                logger.warning(warning)
                warnings.append(warning)
                continue
            
            p.is_molnix = True
            p.save()
    
    # Create Personnel objects
    for md in molnix_deployments:
        try:
            personnel = Personnel.objects.get(molnix_id=md['id'])
            created = False
        except:
            personnel = Personnel(molnix_id=md['id'])
            created = True
        # print('personnel found', personnel)
        event = get_go_event(md['tags'])
        if not event:
            warning = 'Deployment id %d does not have a valid Emergency tag.' % md['id']
            logger.warning(warning)
            warnings.append(warning)
            continue
        try:
            deployment = PersonnelDeployment.objects.get(is_molnix=True, event_deployed_to=event)
        except:
            logger.warning('Did not import Deployment with Molnix ID %d. Invalid Event.' % md['id'])
            continue

        personnel.deployment = deployment
        personnel.molnix_id = md['id']
        if md['hidden'] == 1 or md['draft'] == 1:
            personnel.is_active = False
        else:
            personnel.is_active = True
        personnel.type = Personnel.RR
        personnel.start_date = get_datetime(md['start'])
        personnel.end_date = get_datetime(md['end'])
        personnel.name = md['person']['fullname']
        personnel.role = md['title']
        country_from = None

        # Sometimes the `incoming` value from Molnix is null.
        if md['incoming']:
            incoming_name = md['incoming']['name'].strip()

            # We over-ride the matching for some NS names from Molnix
            if incoming_name in NS_MATCHING_OVERRIDES:
                country_name = NS_MATCHING_OVERRIDES[incoming_name]
                try:
                    country_from = Country.objects.get(name_en=country_name)
                except:
                    warning = 'Mismatch in NS name: %s' % md['incoming']['name']
                    logger.warning(warning)
                    warnings.append(warning)
            else:
                try:
                    country_from = Country.objects.get(society_name=incoming_name, independent=True)
                except:
                    #FIXME: Catch possibility of .get() returning multiple records
                    # even though that should ideally never happen
                    warning = 'NS Name not found for Deployment ID: %d with secondment_incoming %s' % (md['id'], md['incoming']['name'],)
                    logger.warning(warning)
                    warnings.append(warning)
        else:
            warning = 'No data for secondment incoming from Molnix API - id %d' % md['id']
            logger.warning(warning)
            warnings.append(warning)

        personnel.country_from = country_from
        personnel.save()
        add_tags_to_obj(personnel, md['tags'])
        if created:
            successful_creates += 1
        else:
            successful_updates += 1
    all_active_personnel = Personnel.objects.filter(is_active=True, molnix_id__isnull=False)
    active_personnel_ids = [a.molnix_id for a in all_active_personnel]
    inactive_ids = list(set(active_personnel_ids) - set(molnix_ids))
    marked_inactive = len(inactive_ids)
    # Mark Personnel entries no longer in Molnix as inactive:

    for id in inactive_ids:
        personnel = Personnel.objects.get(pk=id)
        personnel.is_active = False
        personnel.save()

    messages = [
        'Successfully created: %d' % successful_creates,
        'Successfully updated: %d' % successful_updates,
        'Marked inactive: %d' % marked_inactive,
        'No of Warnings: %d' % len(warnings)
    ]
    return messages, warnings, successful_creates


def sync_open_positions(molnix_positions, molnix_api):
    molnix_ids = [p['id'] for p in molnix_positions]
    warnings = []
    messages = []
    successful_creates = 0
    successful_updates = 0
    
    for position in molnix_positions:
        event = get_go_event(position['tags'])
        # If no valid GO Emergency tag is found, skip Position
        if not event:
            warning = 'Position id %d does not have a valid Emergency tag.' % position['id']
            logger.warning(warning)
            warnings.append(warning)
            continue
        go_alert, created = SurgeAlert.objects.get_or_create(molnix_id=position['id'])
        # We set all Alerts coming from Molnix to RR / Alert
        go_alert.atype = SurgeAlertType.RAPID_RESPONSE
        go_alert.category = SurgeAlertCategory.ALERT        
        # print(json.dumps(position, indent=2))
        go_alert.molnix_id = position['id']
        go_alert.message = position['name']
        go_alert.molnix_status = position['status']
        go_alert.event = event
        go_alert.opens = get_datetime(position['opens'])
        go_alert.closes = get_datetime(position['closes'])
        go_alert.start = get_datetime(position['start'])
        go_alert.end = get_datetime(position['end'])
        go_alert.is_active = True
        go_alert.save()
        add_tags_to_obj(go_alert, position['tags'])
        if created:
            successful_creates +=1
        else:
            successful_updates += 1

    # Find existing active alerts that are not in the current list from Molnix
    existing_alerts = SurgeAlert.objects.filter(is_active=True).exclude(molnix_id__isnull=True)
    existing_alert_ids = [e.molnix_id for e in existing_alerts]
    inactive_alerts = list(set(existing_alert_ids) - set(molnix_ids))

    # Mark alerts that are no longer in Molnix as inactive
    for alert in SurgeAlert.objects.filter(molnix_id__in=inactive_alerts):
        # We need to check the position ID in Molnix
        # If the status is "unfilled", we don't mark the position as inactive,
        # just set status to unfilled
        position = molnix_api.get_position(alert.molnix_id)
        if not position:
            warnings.append('Position id %d not found in Molnix API' % alert.molnix_id)
        if position and position['status'] == 'unfilled':
            alert.molnix_status = position['status']
        else:
            alert.is_active = False
        alert.save()
    
    marked_inactive = len(inactive_alerts)
    messages = [
        'Successfully created: %d' % successful_creates,
        'Successfully updated: %d' % successful_updates,
        'Marked inactive: %d' % marked_inactive,
        'No of Warnings: %d' % len(warnings)
    ]
    return messages, warnings, successful_creates

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
            positions_messages, positions_warnings, positions_created = sync_open_positions(open_positions, molnix)
            deployments_messages, deployments_warnings, deployments_created = sync_deployments(deployments)
        except Exception as ex:
            msg = 'Unknown Error occurred: %s' % str(ex)
            logger.error(msg)
            create_cron_record(CRON_NAME, msg, CronJobStatus.ERRONEOUS)
            return

        msg = get_status_message(positions_messages, deployments_messages, positions_warnings, deployments_warnings)
        num_records = positions_created + deployments_created
        has_warnings = len(positions_warnings) > 0 or len(deployments_warnings) > 0    
        cron_status = CronJobStatus.WARNED if has_warnings else CronJobStatus.SUCCESSFUL
        create_cron_record(CRON_NAME, msg, cron_status, num_result=num_records)
        molnix.logout()
