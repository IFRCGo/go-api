import hashlib
import json
import typing

from django.contrib.auth.models import Permission
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q


def filter_per_queryset_by_user_access(user, queryset):
    if user.is_superuser or user.has_perm("api.per_core_admin"):
        return queryset
    # Check if country admin
    per_admin_country_id = [
        codename.replace("per_country_admin_", "")
        for codename in Permission.objects.filter(
            group__user=user,
            codename__startswith="per_country_admin_",
        ).values_list("codename", flat=True)
    ]
    per_admin_region_id = [
        codename.replace("per_region_admin_", "")
        for codename in Permission.objects.filter(
            group__user=user,
            codename__startswith="per_region_admin_",
        ).values_list("codename", flat=True)
    ]
    if len(per_admin_country_id) or len(per_admin_region_id):
        return queryset.filter(
            Q(created_by=user) | Q(country__in=per_admin_country_id) | Q(country__region__in=per_admin_region_id)
        ).distinct()
    # Normal access
    return queryset.filter(created_by=user)


class CacheHelper:
    @staticmethod
    def calculate_md5_str(string):
        hash_md5 = hashlib.md5()
        hash_md5.update(string)
        return hash_md5.hexdigest()

    @classmethod
    def generate_hash(cls, value: typing.Union[None, str, dict]) -> str:
        if value is None:
            return ""
        hashable = None
        if isinstance(value, str):
            hashable = value
        elif isinstance(value, dict):
            hashable = json.dumps(
                value,
                sort_keys=True,
                indent=2,
                cls=DjangoJSONEncoder,
            ).encode("utf-8")
        else:
            raise Exception(f"Invalid Type: {type(value)}")
        return cls.calculate_md5_str(hashable)
