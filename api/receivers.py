import json
from datetime import datetime

from django.db import transaction
from django.db.models import Q
from django.db.models.signals import pre_delete, pre_save, post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from reversion.models import Version
from reversion.signals import post_revision_commit
from api.models import ReversionDifferenceLog, Event, Country, FieldReport
from middlewares.middlewares import get_username
from utils.elasticsearch import create_es_index, update_es_index, delete_es_index
from utils.erp import push_fr_data
from api.logger import logger
from .models import Appeal, AppealHistory, AppealFilter
from main.suspend_receivers import suspendingreceiver


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
                if key not in previous_version._local_field_dict:
                    previous_version._local_field_dict[key] = ''
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
    delete_es_index(instance)


# NOTE: Adding this to disable indexing in testcases
@suspendingreceiver(pre_save)
def remove_child_events_from_es(sender, instance, using, **kwargs):
    ''' Handle Emergency Elasticsearch indexes '''
    model = instance.__class__.__name__
    try:
        if model == 'Event':
            curr_record = Event.objects.filter(id=instance.id).first()
            # If new record, do nothing, index_and_notify should handle it
            if curr_record is None:
                return

            if curr_record.parent_event is None and instance.parent_event:
                # Delete ES record if Emergency became a child
                delete_es_index(instance)
            elif curr_record.parent_event and instance.parent_event is None:
                # Add back ES record if Emergency became a parent (index_elasticsearch.py)
                create_es_index(instance)
        elif model == 'Country':
            curr_record = Country.objects.filter(id=instance.id).first()
            if instance.in_search:
                if not curr_record:
                    create_es_index(instance)
                else:
                    if not curr_record.in_search and instance.in_search:
                        create_es_index(instance)
                    elif curr_record.in_search and not instance.in_search:
                        delete_es_index(instance)
                    else:
                        update_es_index(instance)
            else:
                delete_es_index(instance)
    except Exception as ex:
        logger.error(f'Failed to index a Country, error: {str(ex)[:512]}')


# Needs post_save because if a new Field Report is not mapped to an Emergency it will create one
@receiver(post_save)
def handle_fr_for_erp(sender, instance, using, **kwargs):
    '''
    If a Field Report is created/updated and Request for International
    Assisstance is checked for any of the Event's Field Reports then
    update ERP with the data, calling a middleware microservice
    '''

    if isinstance(instance, FieldReport):
        # TODO: maybe add a check, and only send request if anything has changed
        if instance.ns_request_assistance:
            push_fr_data(instance)
            return

        req_ass_exists = FieldReport.objects.filter(
            Q(event_id=instance.event_id) & Q(ns_request_assistance=True)
        ).exists()
        if not instance.ns_request_assistance and req_ass_exists:
            # If assistance request was dropped, set retired to yes
            push_fr_data(instance, retired=True)
            return


@receiver(post_save, sender=Appeal)
def add_update_appeal_history(sender, instance, created, **kwargs):
    fields_watched = [
        field.name for field in AppealHistory._meta.get_fields()
        if field.name not in ['id', 'appeal', 'valid_from', 'valid_to', 'aid', 'amount_funded']
    ]
    now = timezone.now()
    changed = False

    if created:  # Appeal Insert
        AppealHistory.objects.create(
            aid=instance.aid,
            num_beneficiaries=instance.num_beneficiaries,
            amount_requested=instance.amount_requested,
            amount_funded=instance.amount_funded,
            valid_from=now,
            # TODO: use coalesce to fill valid_to instead of defining here.
            valid_to=datetime(2200, 1, 1, tzinfo=timezone.utc),
            start_date=instance.start_date,
            end_date=instance.end_date,
            appeal=instance,
            atype=instance.atype,
            country=instance.country,
            region=instance.region,
            dtype=instance.dtype,
            needs_confirmation=instance.needs_confirmation,
            status=instance.status,
            code=instance.code,
            triggering_amount=instance.triggering_amount
        )

    else:
        # Appeal Update
        appeal = Appeal.objects.get(code=instance.code)
        appeal_history = AppealHistory.objects.filter(aid=instance.aid).order_by('id').last()
        for field in fields_watched:
            if appeal_history and getattr(appeal, field) != getattr(appeal_history, field):
                # Watched fields are not changed
                changed = True

        if not changed:
            # Watched fields are not changed
            return

        appeal_history.valid_to = now
        appeal_history.save()

        # Create a new appeal history if changed
        AppealHistory.objects.create(
            aid=instance.aid,
            num_beneficiaries=instance.num_beneficiaries,
            amount_requested=instance.amount_requested,
            amount_funded=instance.amount_funded,
            valid_from=now,
            # TODO: use coalesce to fill valid_to instead of defining here.
            valid_to=datetime(2200, 1, 1, tzinfo=timezone.utc),
            start_date=instance.start_date,
            end_date=instance.end_date,
            appeal=instance,
            atype=instance.atype,
            country=instance.country,
            region=instance.region,
            dtype=instance.dtype,
            needs_confirmation=instance.needs_confirmation,
            status=instance.status,
            code=instance.code,
            triggering_amount=instance.triggering_amount
        )


@receiver(post_delete, sender=Appeal)
def remove_appeal_filter(sender, instance, using, **kwargs):
    appealFilter = AppealFilter.objects.get(name='ingestAppealFilter')
    lstCodesToSkip = appealFilter.value.split(",")
    if instance.code not in lstCodesToSkip:
        lstCodesToSkip.append(instance.code)

    appealFilter.value = ",".join(lstCodesToSkip)
    appealFilter.save()
