import json
from django.db import transaction
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from reversion.models import Revision, Version
from reversion.signals import post_revision_commit
from api.models import ReversionDifferenceLog, User, Country, Event
from deployments.models import DeployedPerson
from per.models import Form
from middlewares.middlewares import get_username


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
    obj_name = ''

    if (
        otype == 'api.countrysnippet' or
        otype == 'countrysnippet'
    ):
        obj_name = obj['snippet']
    elif (
        otype == 'api.emergencyoperationsdataset' or
        otype == 'api.emergencyoperationsea' or
        otype == 'api.emergencyoperationsfr' or
        otype == 'api.emergencyoperationspeoplereached' or
        otype == 'emergencyoperationsdataset' or
        otype == 'emergencyoperationsea' or
        otype == 'emergencyoperationsfr' or
        otype == 'emergencyoperationspeoplereached'
    ):
        obj_name = obj['raw_file_name']
    elif (
        otype == 'api.fieldreport' or
        otype == 'fieldreport'
    ):
        obj_name = obj['summary']
    elif (
        otype == 'api.gdacsevent' or
        otype == 'gdacsevent'
    ):
        obj_name = obj['title']
    elif (
        otype == 'api.situationreporttype' or
        otype == 'situationreporttype'
    ):
        obj_name = obj['type']
    elif (
        otype == 'api.profile' or
        otype == 'profile'
    ):
        usr = User.objects.get(pk=obj['user_id'])
        obj_name = usr.username if usr else obj['user_id']
    elif (
        otype == 'deployments.eruowner' or
        otype == 'deployments.erureadiness' or
        otype == 'eruowner' or
        otype == 'erureadiness'
    ):
        ns_country = Country.objects.get(pk=obj['national_society_country_id'])
        obj_name = '{} ({})'.format(ns_country.society_name,
                                 ns_country.name) if ns_country else obj['national_society_country_id']
    elif (
        otype == 'deployments.partnersocietyactivities' or
        otype == 'partnersocietyactivities'
    ):
        obj_name = obj['activity']
    elif (
        otype == 'deployments.partnersocietydeployment' or
        otype == 'deployments.personnel' or
        otype == 'partnersocietydeployment' or
        otype == 'personnel'
    ):
        dep_person = DeployedPerson.objects.get(pk=obj['deployedperson_ptr_id'])
        obj_name = dep_person.name if dep_person else obj['deployedperson_ptr_id']
    elif (
        otype == 'deployments.personneldeployment' or
        otype == 'personneldeployment'
    ):
        country = Country.objects.get(pk=obj['country_deployed_to_id'])
        event = Event.objects.get(pk=obj['event_deployed_to_id'])
        obj_name = '{} - {}'.format(country.name, event.name) if country and event else country.name
    elif (
        otype == 'notifications.subscription' or
        otype == 'subscription'
    ):
        usr = User.objects.get(pk=obj['user_id'])
        # TODO: add sub-type (RecordType) later if needed
        obj_name = usr.username
    elif (
        otype == 'notifications.surgealert' or
        otype == 'surgealert'
    ):
        obj_name = obj['operation']
    elif (
        otype == 'per.formdata' or
        otype == 'formdata'
    ):
        form = Form.objects.get(pk=obj['form_id'])
        obj_name = form.name if form else None
    elif (
        otype == 'per.nsphase' or
        otype == 'nsphase'
    ):
        country = Country.objects.get(pk=obj['country_id'])
        obj_name = country.name if country else obj['country_id']
    elif (
        otype == 'per.overview' or
        otype == 'per.workplan' or
        otype == 'overview' or
        otype == 'workplan'
    ):
        country = Country.objects.get(pk=obj['country_id'])
        obj_name = country.society_name if country else None
    elif (
        otype == 'registrations.pending' or
        otype == 'pending'
    ):
        usr = User.objects.get(pk=obj['user_id'])
        obj_name = usr.username
    else:
        obj_name = obj.get('name', '')

    return obj_name


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
    transaction.on_commit(lambda: create_global_reversion_log(versions, revision))


@receiver(pre_delete)
def log_deletion(sender, instance, using, **kwargs):
    model_name = None
    instance_type = instance.__class__.__name__

    # Gets the username from the request with a middleware helper
    usr = get_username()

    for key, value in MODEL_TYPES.items():
        if value == instance_type:
            model_name = key

    ReversionDifferenceLog.objects.create(
        action='Deleted',
        username=usr,
        object_id=instance.pk,
        object_name=get_object_name(model_name, instance.__dict__) if model_name else get_object_name(instance._meta.model_name, instance.__dict__),
        object_type=MODEL_TYPES[model_name] if model_name else instance_type
    )