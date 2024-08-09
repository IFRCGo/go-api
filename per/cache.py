import hashlib
import json
import typing

import django_filters
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Prefetch

from per.models import (
    OpsLearningCacheResponse,
    OpsLearningComponentCacheResponse,
    OpsLearningSectorCacheResponse,
)


class OpslearningSummaryCacheHelper:
    @staticmethod
    def calculate_md5_str(string):
        hash_md5 = hashlib.md5()
        hash_md5.update(string)
        return hash_md5.hexdigest()

    @classmethod
    def generate_hash(cls, value: typing.Union[None, str, dict]) -> str:
        # TODO: Use OrderedDict
        if value is None:
            return ""
        hashable = None
        if isinstance(value, str):
            hashable = value.encode("utf-8")
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

    @classmethod
    def get_or_create(
        self,
        request,
        filter_sets: typing.List[django_filters.FilterSet],
    ):
        filter_data = {
            key: value
            for key, value in request.query_params.items()
            if key in [field for filter_set in filter_sets for field in filter_set.get_filters()]
        }
        hash_value = self.generate_hash(filter_data)
        # Check if the summary is already cached
        # NOTE: count for the related components and sectors are prefetched
        ops_learning_summary, created = OpsLearningCacheResponse.objects.prefetch_related(
            "used_ops_learning",
            Prefetch(
                "ops_learning_component",
                queryset=OpsLearningComponentCacheResponse.objects.select_related(
                    "component",
                ).annotate(count=Count("used_ops_learning")),
            ),
            Prefetch(
                "ops_learning_sector",
                queryset=OpsLearningSectorCacheResponse.objects.select_related(
                    "sector",
                ).annotate(count=Count("used_ops_learning")),
            ),
        ).get_or_create(
            used_filters_hash=hash_value,
            used_filters=filter_data,
            defaults={"status": OpsLearningCacheResponse.Status.PENDING},
        )
        return ops_learning_summary, filter_data
