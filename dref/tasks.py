import logging
from datetime import timedelta
from enum import Enum
from typing import Optional

from celery import shared_task
from django.apps import apps
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from api.utils import get_model_name
from lang.tasks import translate_model_fields
from main.lock import RedisLockKey, redis_lock
from main.translation import TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME
from main.utils import logger_context
from notifications.notification import send_notification

from .models import (
    Dref,
    DrefFile,
    DrefSummary,
    IdentifiedNeed,
    NationalSocietyAction,
    PlannedIntervention,
    PlannedInterventionIndicators,
    ProposedAction,
    ProposedActionActivities,
    RiskSecurity,
    SourceInformation,
)
from .summary import DrefSummaryGenerator
from .utils import get_email_context

logger = logging.getLogger(__name__)

# The PROCESSING status has no TTL of its own (see comment in generate_dref_summary
# below), so a row can get stuck PROCESSING forever if a worker dies mid-generation.
# Treat it as stale past this, so a later trigger can take over.
PROCESSING_STALE_AFTER = timedelta(minutes=10)


class DrefSummaryGenerationResult(str, Enum):
    """Outcome of a ``generate_dref_summary`` run."""

    SUCCESS = "success"
    SOURCE_NOT_FOUND = "source_not_found"
    ALREADY_IN_PROGRESS = "already_in_progress"
    UP_TO_DATE = "up_to_date"
    FAILED = "failed"
    SUPERSEDED = "superseded"


@shared_task
def send_dref_email(dref_id, users_emails, new_or_updated=""):
    if not dref_id or not users_emails:
        return None

    instance = Dref.objects.get(id=dref_id)
    email_context = get_email_context(instance)
    email_subject = f"{new_or_updated} DREF: {instance.title}"
    email_body = render_to_string("email/dref/dref.html", email_context)
    email_type = f"{new_or_updated} DREF"

    send_notification(email_subject, users_emails, email_body, email_type)
    return email_context


# NOTE: Only the models directly related to Dref are included here.
# The task will translate the fields of these models and update
# `translation_module_original_language` to "en".
TRANSLATABLE_RELATED_MODELS = [
    DrefFile,
    NationalSocietyAction,
    IdentifiedNeed,
    PlannedIntervention,
    RiskSecurity,
    ProposedAction,
    ProposedActionActivities,
    PlannedInterventionIndicators,
    SourceInformation,
]


@shared_task(soft_time_limit=600, time_limit=630)
def generate_dref_summary(dref_id: int, overwrite: bool = False) -> DrefSummaryGenerationResult:
    """Generate and store the AI-assisted summaries for a DREF.

    Always (re)generates from whichever approved source is currently latest
    for the DREF (see ``get_latest_approved_source``), rather than a
    specific source passed in, so it self-corrects no matter which
    approval triggered it or the order concurrent runs execute in.
    """
    dref = Dref.objects.filter(id=dref_id).first()
    if not dref:
        logger.error("Dref not found for summary generation", extra=logger_context({"dref_id": dref_id}))
        return DrefSummaryGenerationResult.SOURCE_NOT_FOUND

    # The Redis lock only needs to guard the brief read-check-mark-PROCESSING
    # section below against a concurrent trigger for the same DREF (double-
    # approve, admin retrigger, ...); it is released before the LLM call.
    # The PROCESSING status written inside the lock is what actually blocks
    # a second run for as long as generation takes - unlike the lock, it has
    # no TTL, so it still holds even if generation outlives lock_expire.
    with redis_lock(key=RedisLockKey.DREF_SUMMARY, id=dref_id) as acquired:
        if not acquired:
            logger.warning(f"DREF summary generation already in progress for DREF ({dref_id}); skipping.")
            return DrefSummaryGenerationResult.ALREADY_IN_PROGRESS

        latest_source = DrefSummaryGenerator.get_latest_approved_source(dref)
        if not latest_source:
            logger.error(f"No approved source found for DREF ({dref_id}) summary")
            return DrefSummaryGenerationResult.SOURCE_NOT_FOUND
        source_type, source_obj = latest_source

        section_kwargs = DrefSummaryGenerator.get_section_kwargs(source_obj)
        source_hash = DrefSummaryGenerator.compute_source_hash(source_obj, section_kwargs=section_kwargs)
        summary_instance: Optional[DrefSummary] = DrefSummary.objects.filter(dref=dref).first()

        if (
            summary_instance
            and summary_instance.status == DrefSummary.SummaryStatus.PROCESSING
            and timezone.now() - summary_instance.updated_at < PROCESSING_STALE_AFTER
            and summary_instance.source == source_type
            and summary_instance.source_id == source_obj.id
        ):
            # Same source already in flight; a different one falls through to regenerate below.
            logger.warning(f"DREF summary already in progress for DREF ({dref_id}); skipping.")
            return DrefSummaryGenerationResult.ALREADY_IN_PROGRESS

        if (
            summary_instance
            and not overwrite
            and summary_instance.source_hash == source_hash
            and summary_instance.status == DrefSummary.SummaryStatus.SUCCESS
        ):
            logger.info(f"DREF summary up to date for DREF ({dref_id}); skipping generation.")
            return DrefSummaryGenerationResult.UP_TO_DATE

        if summary_instance is None:
            summary_instance = DrefSummary(dref=dref)

        try:
            summary_instance.source_hash = source_hash
            summary_instance.source = source_type
            summary_instance.source_id = source_obj.id
            summary_instance.status = DrefSummary.SummaryStatus.PROCESSING
            summary_instance.save()
        except Exception:
            logger.warning(f"Failed to mark DREF summary as processing for DREF ({dref_id})", exc_info=True)
            if summary_instance.pk:
                summary_instance.status = DrefSummary.SummaryStatus.FAILED
                summary_instance.save()
            return DrefSummaryGenerationResult.FAILED

    # Lock released. The (possibly slow) LLM call runs unlocked; the
    # PROCESSING status set above is what a concurrent trigger checks.
    own_marker = {
        "pk": summary_instance.pk,
        "source": source_type,
        "source_id": source_obj.id,
        "status": DrefSummary.SummaryStatus.PROCESSING,
    }
    try:
        logger.info(f"Generating DREF summaries for DREF ({dref_id}) from ({source_type.label}) ({source_obj.id})")
        results = DrefSummaryGenerator().generate_all(source_obj, section_kwargs=section_kwargs)
        with transaction.atomic():
            latest_summary_instance = DrefSummary.objects.select_for_update().filter(**own_marker).first()
            if latest_summary_instance is None:
                logger.warning(f"DREF summary run for DREF ({dref_id}) was superseded by a newer trigger; discarding result.")
                return DrefSummaryGenerationResult.SUPERSEDED
            for field_name, value in results.items():
                setattr(latest_summary_instance, field_name, value)
            latest_summary_instance.status = DrefSummary.SummaryStatus.SUCCESS
            latest_summary_instance.save()
        logger.info(f"Successfully generated DREF summaries for DREF ({dref_id})")
        transaction.on_commit(lambda: translate_model_fields.delay(get_model_name(DrefSummary), latest_summary_instance.pk))
        return DrefSummaryGenerationResult.SUCCESS
    except Exception:
        with transaction.atomic():
            latest_summary_instance = DrefSummary.objects.select_for_update().filter(**own_marker).first()
            if latest_summary_instance is None:
                logger.warning(f"DREF summary run for DREF ({dref_id}) failed but was already superseded; leaving it as is.")
            else:
                latest_summary_instance.status = DrefSummary.SummaryStatus.FAILED
                latest_summary_instance.save()
                logger.warning(f"DREF summary generation failed for DREF ({dref_id})", exc_info=True)
        return DrefSummaryGenerationResult.FAILED


@shared_task
def process_dref_translation(model_name, instance_pk):
    """
    Task to translate  model instance and its related objects
    """
    instance = None
    try:
        model = apps.get_model(model_name)
        instance = model.objects.get(pk=instance_pk)
        logger.info(f"Starting translation for model: ({model_name}) ID: ({instance_pk})")
        translate_model_fields(model_name, instance_pk)
        logger.info(f"Translating related objects for model: ({model_name}) ID: ({instance_pk})")
        _translate_related_objects(instance)
        instance.status = Dref.Status.FINALIZED
        instance.translation_module_original_language = "en"
        instance.save(update_fields=["status", "translation_module_original_language"])
        logger.info(f"Successfully finalized: ({model_name}) ID: ({instance_pk})")
    except Exception:
        if instance is not None:
            instance.status = Dref.Status.FAILED
            instance.save(update_fields=["status"])
        logger.warning(f"Translation failed for model: ({model_name}) ID: ({instance_pk})", exc_info=True)
        return False


def _translate_related_objects(
    instance,
    visited=None,
    auto_translate=True,
    language="en",
):
    """
    Sync the relateable translation fields for the given model instance.
    This function ensures that the translation fields are updated correctly
    based on the current language settings.

    Args:
        instance: The model instance whose related objects need to be translated.
        visited: A set to keep track of visited instances to avoid infinite recursion.
        auto_translate: A boolean indicating whether to auto-translate related objects.
        language: The language code to set for the original language field.

    """

    if visited is None:
        visited = set()

    instance_id = id(instance)
    if instance_id in visited:
        return
    visited.add(instance_id)

    for field in instance._meta.get_fields():
        if not field.is_relation or field.auto_created:
            continue

        related_model = field.related_model
        if related_model not in TRANSLATABLE_RELATED_MODELS:
            continue

        related_value = getattr(instance, field.name, None)
        if related_value is None:
            continue

        if not field.many_to_many:
            if hasattr(related_value, TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME):
                model_name = get_model_name(type(related_value))
                if auto_translate:
                    translate_model_fields(model_name, related_value.id)
                related_value.translation_module_original_language = language
                related_value.save(update_fields=["translation_module_original_language"])
                _translate_related_objects(related_value, visited, auto_translate, language)
        else:
            for related_obj in related_value.all():
                if hasattr(related_obj, TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME):
                    model_name = get_model_name(type(related_obj))
                    if auto_translate:
                        translate_model_fields(model_name, related_obj.id)
                    related_obj.translation_module_original_language = language
                    related_obj.save(update_fields=["translation_module_original_language"])
                    _translate_related_objects(related_obj, visited, auto_translate, language)
