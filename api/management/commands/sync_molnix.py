from dateutil import parser as date_parser
import json
from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from api.molnix_utils import MolnixApi
from api.logger import logger
from deployments.models import MolnixTag, MolnixTagGroup, PersonnelDeployment, Personnel
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
    'Icrc Staff': 'ICRC',
    'ICRC': 'ICRC'
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


def add_tags(molnix_tags, api):
    modality = ['In Person', 'Remote']
    region = ['ASIAP', 'AMER', 'AFRICA', 'MENA', 'EURO']
    scope = ['REGIONAL', 'GLOBAL']
    status = ['Archive', 'AVAIL', 'Consult HR', 'HOLD']
    sector = ['ADMIN', 'ASSESS', 'CEA', 'CIVMIL', 'COM', 'CVA', 'DRR', 'FIN', 'HEALTH', 'HR', 'IDRL', 'IM', 'IT', 'LOGS',
              'LVES', 'MHPSS', 'MIG', 'NSD', 'OPS-LEAD', 'PER', 'PGI', 'PMER', 'PRD', 'PSS', 'REC', 'REL', 'RFL', 'SEC',
              'SHCLUSTER', 'SHELTER', 'STAFFHEALTH', 'WASH']

    for molnix_tag in molnix_tags:
        tag, created = MolnixTag.objects.get_or_create(molnix_id=molnix_tag['id'])
        tag_groups = api.get_tag_groups(molnix_tag['id']) if molnix_tag['id'] else []
        for g in tag_groups:
            tag_group, created = MolnixTagGroup.objects.get_or_create(
                molnix_id=g['id'],
                name=g['name'])
            if created:
                tag_group.created_at = g['created_at']
            tag_group.updated_at = g['updated_at']
            tag_group.save()
            tag.groups.add(tag_group)
        tag.molnix_id = molnix_tag['id']
        tag.name = n = molnix_tag['name']
        tag.description = molnix_tag['description']
        if tag.description is None:
            tag.description = ''
            logger.warning('%s named tag has no description.' % tag.name)
        tag.tag_type = molnix_tag['type']
        tag.tag_category = 'molnix_language' if n.startswith('L-') else \
            'molnix_operation' if n.startswith('OP-') else \
            'molnix_modality' if n in modality else \
            'molnix_region' if n in region else \
            'molnix_scope' if n in scope else \
            'molnix_sector' if n in sector else \
            'molnix_status' if n in status else \
            'molnix_role_profile'
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

def get_go_country(countries, country_id):
    '''
        Given a Molnix country ID, returns GO country id
    '''
    if not country_id in countries:
        return None
    iso = countries[country_id]
    country = Country.objects.get(iso=iso, independent=True)
    return country

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
    _ids = [int(t['id']) for t in tags]
    tags = list(  # Fetch all at once
        MolnixTag.objects.filter(molnix_id__in=_ids)
    )
    if len(tags) != len(_ids):  # Show warning if all tags are not available
        missing_tag_ids = list(set(_ids) - set([tag.id for tag in tags]))
        logger.warning(f'Missing _ids: {missing_tag_ids}')
        # or   ^^^^^^^ logger.error if we need to add molnix tags manually.
    obj.molnix_tags.set(tags)  # Add new ones, remove old ones


def sync_deployments(molnix_deployments, molnix_api, countries):
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

            if p.event_deployed_to.countries.all().count() > 0:
                # Since different personnel deployed to the same emergency
                # can be deployed to different countries affected by the emergency,
                # we should no longer use country_deployed_to from PersonnelDeployment,
                # rather get the country for each deployed person directly from the
                # Personnel model for each deployed person.
                # FIXME: we should look to deprecate usage of this field entirely.
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

        surge_alert = None
        try:
            if md['position_id']:
                surge_alert = SurgeAlert.objects.get(molnix_id=md['position_id'])
        except:
            logger.warning('Did not find SurgeAlert with Molnix position_id %d.' % md['position_id'])
            continue

        appraisal_received = 'appraisals' in md and len(md['appraisals'])

        gender = None
        try:
            if md['person'] and 'sex' in md['person']:
                gender = md['person']['sex']
        except:
            logger.warning('Did not find gender info in %d' % md['id'])
            continue

        location = None
        try:
            if md['contact'] and 'addresses' in md['contact'] and len(md['contact']['addresses']) and 'city' in md['contact'][0]:
                location = md['contact']['addresses'][0]['city']
        except:
            logger.warning('Did not find city info in %d' % md['id'])
            continue

        personnel.deployment = deployment
        personnel.molnix_id = md['id']
        if md['hidden'] == 1:
            personnel.molnix_status = 'hidden'
            personnel.is_active = False
        elif md['draft'] == 1:
            personnel.molnix_status = 'draft'
            personnel.is_active = False
        else:
            personnel.molnix_status = 'active'
            personnel.is_active = True
        personnel.type = Personnel.TypeChoices.RR
        personnel.start_date = get_datetime(md['start'])
        personnel.end_date = get_datetime(md['end'])
        personnel.name = md['person']['fullname']
        personnel.role = md['title']
        country_to = get_go_country(countries, md['country_id'])
        if not country_to:
            warning = 'Position id %d does not have a valid Country To' % (md['id'])
            logger.warning(warning)
            warnings.append(warning)
            country_to = None
        personnel.country_to = country_to
        country_from = None
        personnel.surge_alert = surge_alert
        personnel.appraisal_received = appraisal_received
        personnel.gender = gender
        personnel.location = location

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
        personnel = Personnel.objects.get(molnix_id=id)
        personnel.molnix_status = 'deleted'
        personnel.is_active = False
        personnel.save()

    messages = [
        'Successfully created: %d' % successful_creates,
        'Successfully updated: %d' % successful_updates,
        'Marked inactive: %d' % marked_inactive,
        'No of Warnings: %d' % len(warnings)
    ]
    return messages, warnings, successful_creates


def sync_open_positions(molnix_positions, molnix_api, countries):
    molnix_ids = [p['id'] for p in molnix_positions]
    warnings = []
    messages = []
    successful_creates = 0
    successful_updates = 0

    for position in molnix_positions:
        event = get_go_event(position['tags'])
        country = get_go_country(countries, position['country_id'])
        if not country:
            warning = 'Position id %d does not have a valid Country' % (position['id'])
            logger.warning(warning)
            warnings.append(warning)
            continue
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
        go_alert.country = country
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
            countries = molnix.get_countries()
            deployments = molnix.get_deployments()
            open_positions = molnix.get_open_positions()
        except Exception as ex:
            msg = 'Failed to fetch data from Molnix API: %s' % str(ex)
            logger.error(msg)
            create_cron_record(CRON_NAME, msg, CronJobStatus.ERRONEOUS)
            return

        try:
            used_tags = get_unique_tags(deployments, open_positions)
            add_tags(used_tags, molnix)  # FIXME 2nd arg: a workaround to be able to get the group details inside.
            positions_messages, positions_warnings, positions_created = sync_open_positions(open_positions, molnix, countries)
            deployments_messages, deployments_warnings, deployments_created = sync_deployments(deployments, molnix, countries)
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
