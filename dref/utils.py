from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from django.db import models
from django.utils import translation
from modeltranslation.translator import translator

from dref.models import Dref, DrefFinalReport, DrefOperationalUpdate


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


def is_translation_complete(instance, target_lang="en"):
    """
    Check all translatable fields of a instance have been
    translated to the target language.
    """
    original_lang = getattr(instance, "translation_module_original_language", None)
    if not original_lang:
        return False
    try:
        opts = translator.get_options_for_model(type(instance))
    except Exception:
        return True
    for field in getattr(opts, "fields", []):
        with translation.override(original_lang):
            original_value = getattr(instance, field, None)

        with translation.override(target_lang):
            translated_value = getattr(instance, field, None)
        if not original_value:
            continue
        if not translated_value:
            return False

    return True
