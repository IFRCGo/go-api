import json
from django.db import transaction
from django.dispatch import receiver
from reversion.models import Revision, Version
from reversion.signals import post_revision_commit
from api.models import ReversionDifferenceLog, User, Country, Event
from deployments.models import DeployedPerson
from per.models import Form
#from notifications.models import RecordType

# Copied from Stackoverflow
# def clear_versions(versions, revision):
#     count = 0
#     for version in versions:
#         previous_version = Version.objects.filter(
#             object_id=version.object_id,
#             content_type_id=version.content_type_id,
#             id__lt=version.id,
#         ).first()
#         if not previous_version:
#             continue
#         if previous_version._local_field_dict == version._local_field_dict:
#             version.delete()
#             count += 1
#         if len(versions_ids) == count:
#             revision.delete()


MODEL_TYPES = {
    'api.action': 'Action',
    'api.appeal': 'Appeal',
    'api.appealdocument': 'Appeal Document',
    'api.country': 'Country',
    'api.cronjob': 'CronJob',
    'api.district': 'District',
    'api.emergencyoperationsdataset': 'Emergency Operations Dataset',
    'api.emergencyoperationsea': 'Emergency Operations Emergency Appeals',
    'api.emergencyoperationsfr': 'Emergency Operations Final Reports',
    'api.emergencyoperationspeoplereached': 'Emergency Operations People Reached',
    'api.event': 'Emergency',
    'api.fieldreport': 'Field Report',
    'api.gdacsevent': 'GDACS Event',
    'api.profile': 'User Profile',
    'api.region': 'Region',
    'api.situationreport': 'Situation Report',
    'api.situationreporttype': 'Situation Report Type',
    'deployments.eruowner': 'ERU Owner',
    'deployments.erureadiness': 'ERU Readiness',
    'deployments.partnersocietyactivities': 'Partner society activity',
    'deployments.partnersocietydeployment': 'Partner society deployment',
    'deployments.personnel': 'Personnel',
    'deployments.personneldeployment': 'Personnel Deployment',
    'deployments.project': 'Project',
    'deployments.regionalproject': 'Regional project',
    'notifications.subscription': 'Subscription',
    'notifications.surgealert': 'Surge alert',
    'per.form': 'PER Form',
    'per.formdata': 'PER Form Data',
    'per.nicedocument': 'PER Document',
    'per.nsphase': 'PER NS Phase',
    'per.overview': 'PER General Overview',
    'per.workplan': 'PER Work Plan',
    'registrations.pending': 'Pending registration',
}


def get_object_name(otype, obj):
    oname = ''
    if (
        otype == 'api.emergencyoperationsdataset' or
        otype == 'api.emergencyoperationsea' or
        otype == 'api.emergencyoperationsfr' or
        otype == 'api.emergencyoperationspeoplereached'
    ):
        oname = obj['raw_file_name']
    elif otype == 'api.fieldreport':
        oname = obj['summary']
    elif otype == 'api.gdacsevent':
        oname = obj['title']
    elif otype == 'api.situationreporttype':
        oname = obj['type']
    elif otype == 'api.profile':
        usr = User.objects.get(pk=obj['user_id'])
        oname = usr.username if usr else obj['user_id']
    elif (
        otype == 'deployments.eruowner' or
        otype == 'deployments.erureadiness'
    ):
        ns_country = Country.objects.get(pk=obj['national_society_country_id'])
        oname = '{} ({})'.format(ns_country.society_name,
                                 ns_country.name) if ns_country else obj['national_society_country_id']
    elif otype == 'deployments.partnersocietyactivities':
        oname = obj['activity']
    elif (
        otype == 'deployments.partnersocietydeployment' or
        otype == 'deployments.personnel'
    ):
        dep_person = DeployedPerson.objects.get(pk=obj['deployedperson_ptr_id'])
        oname = dep_person.name if dep_person else obj['deployedperson_ptr_id']
    elif otype == 'deployments.personneldeployment':
        country = Country.objects.get(pk=obj['country_deployed_to_id'])
        event = Event.objects.get(pk=obj['event_deployed_to_id'])
        oname = '{} - {}'.format(country.name, event.name) if country and event else country.name
    elif otype == 'notifications.subscription':
        usr = User.objects.get(pk=obj['user_id'])
        # TODO: add sub-type (RecordType) later if needed
        oname = usr.username
    elif otype == 'notifications.surgealert':
        oname = obj['operation']
    elif otype == 'per.formdata':
        form = Form.objects.get(pk=obj['form_id'])
        oname = form.name if form else None
    elif otype == 'per.nsphase':
        country = Country.objects.get(pk=obj['country_id'])
        oname = country.name if country else obj['country_id']
    elif (
        otype == 'per.overview' or
        otype == 'per.workplan'
    ):
        country = Country.objects.get(pk=obj['country_id'])
        oname = country.society_name if country else None
    elif otype == 'registrations.pending':
        usr = User.objects.get(pk=obj['user_id'])
        oname = usr.username
    else:
        oname = obj['name']

    return oname


def create_global_reversion_log(versions, revision):
    for version in versions:
        ver_data = json.loads(version.serialized_data)
        model_name = ver_data[0]['model']
        action_happened = 'Added' if 'Added' in revision.comment else 'Changed'

        previous_version = Version.objects.filter(
            object_id=version.object_id,
            content_type_id=version.content_type_id,
            id__lt=version.id,
        ).first()

        # if the record already existed in the DB but didn't have an initial/previous reversion record
        if not previous_version and action_happened == 'Added':
            ReversionDifferenceLog.objects.create(
                action=action_happened,
                username=revision.user.username,
                object_id=version.object_id,
                object_name=get_object_name(model_name, version._local_field_dict),
                object_type=MODEL_TYPES[model_name]
            )
        elif not previous_version:
            ReversionDifferenceLog.objects.create(
                action=action_happened,
                username=revision.user.username,
                object_id=version.object_id,
                object_name=get_object_name(model_name, version._local_field_dict),
                object_type=MODEL_TYPES[model_name],
                changed_to=revision.comment.replace('Changed ', '').replace('.', '').split(' and ')
            )
        elif previous_version._local_field_dict != version._local_field_dict:
            import pdb
            pdb.set_trace()
            changes_from = []
            changes_to = []
            for key, value in version._local_field_dict.items():
                if previous_version._local_field_dict[key] != value:
                    changes_from.append('{}: {}'.format(key, previous_version._local_field_dict[key]))
                    changes_to.append('{}: {}'.format(key, value))

            ReversionDifferenceLog.objects.create(
                action=action_happened,
                username=revision.user.username,
                object_id=version.object_id,
                object_name=get_object_name(model_name, version._local_field_dict),
                object_type=MODEL_TYPES[model_name],
                changed_from=changes_from,
                changed_to=changes_to
            )


@receiver(post_revision_commit)
def post_revision_commit_receiver(sender, revision, versions, **kwargs):
    # transaction.on_commit(lambda: clear_versions(versions, revision))
    transaction.on_commit(lambda: create_global_reversion_log(versions, revision))
