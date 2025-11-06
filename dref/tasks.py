import logging

from celery import shared_task
from django.apps import apps
from django.template.loader import render_to_string

from api.utils import get_model_name
from lang.tasks import translate_model_fields
from notifications.notification import send_notification

from .models import Dref
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


def _translate_related_objects(instance, visited=None):
    if visited is None:
        visited = set()

    instance_id = id(instance)
    if instance_id in visited:
        return
    visited.add(instance_id)

    for field in instance._meta.get_fields():
        if not field.is_relation or field.auto_created:
            continue

        try:
            related_value = getattr(instance, field.name, None)
            if related_value is None:
                continue

            # Handle related objects
            if not field.many_to_many:
                if hasattr(related_value, "translation_module_original_language"):
                    model_name = get_model_name(type(related_value))
                    translate_model_fields(model_name, related_value.pk)
                    _translate_related_objects(related_value, visited)

            # Handle multiple related objects
            else:
                for related_obj in related_value.all():
                    if hasattr(related_obj, "translation_module_original_language"):
                        model_name = get_model_name(type(related_obj))
                        translate_model_fields(model_name, related_obj.pk)
                        _translate_related_objects(related_obj, visited)

        except Exception as e:
            logger.warning(f"Error processing field {field.name}: {e}")
            continue
