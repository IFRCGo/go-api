import json
from api.indexes import ES_PAGE_NAME
from api.esconnection import ES_CLIENT
from django.db import transaction
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from elasticsearch.helpers import bulk
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


def create_global_reversion_log(versions, revision):
    for version in versions:
        ver_data = json.loads(version.serialized_data)
        # try to map model name coming from Reversion to more readable model names (dict above)
        model_name = MODEL_TYPES.get(ver_data[0]['model'], ver_data[0]['model'])
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
                username=revision.user.username if revision.user else '',
                object_id=version.object_id,
                object_name=str(version) if len(str(version)) <= 200 else str(version)[:200] + '...',
                object_type=model_name
            )
        elif not previous_version:
            ReversionDifferenceLog.objects.create(
                action=action_happened,
                username=revision.user.username if revision.user else '',
                object_id=version.object_id,
                object_name=str(version) if len(str(version)) <= 200 else str(version)[:200] + '...',
                object_type=model_name,
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
                username=revision.user.username if revision.user else '',
                object_id=version.object_id,
                object_name=str(version) if len(str(version)) <= 200 else str(version)[:200] + '...',
                object_type=model_name,
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

    # Creates a ReversionDifferenceLog record which is used for the "global" log
    ReversionDifferenceLog.objects.create(
        action='Deleted',
        username=usr,
        object_id=instance.pk,
        object_name=str(instance) if len(str(instance)) <= 200 else str(instance)[:200] + '...',
        object_type=MODEL_TYPES.get(model_name, instance_type) if model_name else instance_type
    )

    # ElasticSearch to also delete the index if a record was deleted
    if hasattr(instance, 'es_id'):
        bulk(client=ES_CLIENT , actions=[{
            '_op_type': 'delete',
            '_index': ES_PAGE_NAME,
            '_type': 'page',
            '_id': instance.es_id()
        }])