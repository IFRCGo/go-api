import hashlib
import json
import typing

import django_filters
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction

from per.models import OpsLearningCacheResponse
from per.task import generate_summary


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
        ops_learning_summary = OpsLearningCacheResponse.objects.filter(used_filters_hash=hash_value).first()
        if ops_learning_summary:
            return ops_learning_summary
        # Create a new summary and cache it
        return transaction.on_commit(lambda: generate_summary.delay(filter_data, hash_value))
