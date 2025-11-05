import logging

from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from django.db import models
from modeltranslation.translator import translator
from modeltranslation.utils import build_localized_fieldname

from dref.models import Dref, DrefFinalReport, DrefOperationalUpdate

logger = logging.getLogger(__name__)


def get_email_context(instance):
    from dref.serializers import DrefSerializer

    dref_data = DrefSerializer(instance).data
    email_context = {
        "id": dref_data["id"],
        "title": dref_data["title"],
        "frontend_url": settings.GO_WEB_URL,
    }
    return email_context


def get_dref_users():
    dref_users_qs = Dref.objects.annotate(
        created_user_list=ArrayAgg("created_by", filter=models.Q(created_by__isnull=False)),
        users_list=ArrayAgg("users", filter=models.Q(users__isnull=False)),
        op_users=models.Subquery(
            DrefOperationalUpdate.objects.filter(dref=models.OuterRef("id"))
            .order_by()
            .values("dref")
            .annotate(c=ArrayAgg("users", filter=models.Q(users__isnull=False)))
            .values("c")[:1]
        ),
        fr_users=models.Subquery(
            DrefFinalReport.objects.filter(dref=models.OuterRef("id"))
            .order_by()
            .values("dref")
            .annotate(c=ArrayAgg("users", filter=models.Q(users__isnull=False)))
            .values("c")[:1],
        ),
    ).values("id", "created_user_list", "users_list", "op_users", "fr_users")
    dref_users_list = []
    for dref in dref_users_qs:
        if dref["created_user_list"] is None:
            dref["created_user_list"] = []
        if dref["users_list"] is None:
            dref["users_list"] = []
        if dref["op_users"] is None:
            dref["op_users"] = []
        if dref["fr_users"] is None:
            dref["fr_users"] = []
        dref_users_list.append(
            dict(
                id=dref["id"],
                users=set(list(dref["created_user_list"] + dref["users_list"] + dref["op_users"] + dref["fr_users"])),
            )
        )
    return dref_users_list


def is_translation_complete(instance, target_lang="en", visited=None):
    if visited is None:
        visited = set()

    instance_id = id(instance)
    if instance_id in visited:
        return True

    visited.add(instance_id)

    if not _is_instance_translatable(instance):
        return False

    if not _check_instance_fields(instance, target_lang):
        return False
    if not _check_related_fields(instance, target_lang, visited):
        return False
    return True


def _is_instance_translatable(instance):
    """Check if instance has translation capability."""
    return bool(getattr(instance, "translation_module_original_language", None))


def _check_instance_fields(instance, target_lang):
    """Check translatable fields on the instance itself."""
    try:
        opts = translator.get_options_for_model(type(instance))
    except Exception as e:
        logger.warning(f"Failed to get translation options for {instance}: {e}")
        return False

    original_lang = getattr(instance, "translation_module_original_language", None)

    translatable_fields = getattr(opts, "fields", [])
    for field in translatable_fields:
        original_field = build_localized_fieldname(field, original_lang)
        target_field = build_localized_fieldname(field, target_lang)

        original_value = getattr(instance, original_field, None)
        translated_value = getattr(instance, target_field, None)

        if original_value and not translated_value:
            return False
    return True


def _check_related_fields(instance, target_lang, visited):
    """Check all related translatable fields."""
    for field in instance._meta.get_fields():
        if not field.is_relation or field.auto_created:
            continue

        try:
            related_value = getattr(instance, field.name, None)
        except Exception as e:
            logger.warning(f"Error accessing related field '{field.name}' on {instance}: {e}")
            continue
        if related_value is None:
            continue
        if not field.many_to_many:
            if hasattr(related_value, "translation_module_original_language"):
                if not is_translation_complete(related_value, target_lang, visited):
                    return False
        else:
            try:
                related_objects = related_value.all()
            except Exception as e:
                logger.warning(f"Error fetching M2M '{field.name}' for {instance}: {e}")
                continue

            for related_obj in related_objects:
                if hasattr(related_obj, "translation_module_original_language"):
                    if not is_translation_complete(related_obj, target_lang, visited):
                        return False

    return True
