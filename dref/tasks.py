import logging

from celery import shared_task
from django.apps import apps
from django.db import transaction
from django.template.loader import render_to_string

from api.utils import get_model_name
from lang.tasks import translate_model_fields
from main.translation import TRANSLATOR_ORIGINAL_LANGUAGE_FIELD_NAME
from main.utils import logger_context
from notifications.notification import send_notification

from .models import (
    Dref,
    DrefFile,
    DrefFinalReport,
    DrefOperationalUpdate,
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


def _resolve_source_model(source_model_name):
    """Map a ``DrefSummary.SourceModel`` choice to its model class."""
    if source_model_name == DrefSummary.SourceModel.DREF:
        return Dref
    elif source_model_name == DrefSummary.SourceModel.DREF_OPERATIONAL_UPDATE:
        return DrefOperationalUpdate
    elif source_model_name == DrefSummary.SourceModel.DREF_FINAL_REPORT:
        return DrefFinalReport
    return None


@shared_task
def generate_dref_summary(source_model_name, source_id, overwrite=False):
    """Generate and store the AI-assisted summaries for a DREF.

    The DREF is derived from the source document, so the source (a Dref,
    DrefOperationalUpdate or DrefFinalReport) is the single source of truth for
    what the summary is built from.
    """
    source_model = _resolve_source_model(source_model_name)
    if source_model is None:
        logger.error(
            "Could not resolve source model for DREF summary",
            extra=logger_context({"source_model_name": source_model_name, "source_id": source_id}),
        )
        return False
    source_doc = source_model.objects.filter(id=source_id).first()
    if not source_doc:
        logger.error(
            "Source document not found for DREF summary",
            extra=logger_context({"source_model_name": source_model_name, "source_id": source_id}),
        )
        return False

    # Derive the DREF from the source: the Dref is its own source, while
    # DrefOperationalUpdate and DrefFinalReport both point back via ``dref``.
    dref = source_doc if isinstance(source_doc, Dref) else source_doc.dref
    if not dref:
        logger.error(
            "DREF not found for summary generation",
            extra=logger_context({"source_model_name": source_model_name, "source_id": source_id}),
        )
        return False
    dref_id = dref.id
    source_id = source_doc.id

    generator = DrefSummaryGenerator()
    source_hash = generator.compute_source_hash(source_doc)

    summary_instance = DrefSummary.objects.filter(dref=dref).first()
    if (
        summary_instance
        and not overwrite
        and summary_instance.source_hash == source_hash
        and summary_instance.status == DrefSummary.SummaryStatus.SUCCESS
    ):
        logger.info(f"DREF summary up to date for DREF ({dref_id}); skipping generation.")
        return True

    if summary_instance is None:
        summary_instance = DrefSummary(dref=dref)
    summary_instance.source_hash = source_hash
    summary_instance.source_model_name = source_model_name
    summary_instance.source_id = source_id
    summary_instance.status = DrefSummary.SummaryStatus.PROCESSING
    summary_instance.save()

    try:
        logger.info(f"Generating DREF summaries for DREF ({dref_id}) from ({source_model_name}) ({source_id})")
        results = generator.generate_all(source_doc)
        for field_name, value in results.items():
            setattr(summary_instance, field_name, value)
        summary_instance.status = DrefSummary.SummaryStatus.SUCCESS
        summary_instance.save()
        logger.info(f"Successfully generated DREF summaries for DREF ({dref_id})")
        transaction.on_commit(lambda: translate_model_fields.delay(get_model_name(DrefSummary), summary_instance.pk))
        return True
    except Exception:
        summary_instance.status = DrefSummary.SummaryStatus.FAILED
        summary_instance.save()
        logger.warning(f"DREF summary generation failed for DREF ({dref_id})", exc_info=True)
        return False


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
