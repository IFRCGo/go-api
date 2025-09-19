import logging

from celery import shared_task
from django.apps import apps as django_apps
from django.template.loader import render_to_string

from lang.tasks import ModelTranslator
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


@shared_task()
def translate_fields_to_english(model_name: str, pk: int) -> None:
    model = django_apps.get_model(model_name)
    obj = model.objects.get(pk=pk)
    try:
        ModelTranslator().translate_model_fields_to_english(obj)
        obj.status = Dref.Status.FINALIZED
        obj.translation_module_original_language = "en"
        obj.save(update_fields=["status", "translation_module_original_language"])
    except Exception as exc:
        obj.status = Dref.Status.DRAFT
        obj.save(update_fields=["status"])
        logger.warning(f"Translation failed for '{model_name} {pk}': {exc}", exc_info=True)
        raise exc
