import datetime
import json
import typing
from collections import defaultdict
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper

import requests
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models, router
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import exceptions
from rest_framework.negotiation import DefaultContentNegotiation
from reversion.models import Version
from reversion.revisions import _get_options


def is_tableau(request):
    """Checking the request for the 'tableau' parameter
    (used mostly for switching to the *TableauSerializers)
    """
    return request.GET.get("tableau", "false").lower() == "true"


def get_merged_items_by_fields(items, fields, seperator=", "):
    """
    For given array and fields:
    input: [{'name': 'name 1', 'age': 2}, {'name': 'name 2', 'height': 32}], ['name', 'age']
    output: {'name': 'name 1, name 2', 'age': '2, '}
    """
    data = defaultdict(list)
    for item in items:
        for field in fields:
            value = getattr(item, field, None)
            if value is not None:
                data[field].append(str(value))
    return {field: seperator.join(data[field]) for field in fields}


class DownloadFileManager:
    """
    Convert Appeal API datetime into django datetime
    Parameters
    ----------
      url : str
    Return: TemporaryFile
    On close: Close and Delete the file
    """

    def __init__(self, url, dir="/tmp/", **kwargs):
        self.url = url
        self.downloaded_file = None
        # NamedTemporaryFile attributes
        self.named_temporary_file_args = {
            "dir": dir,
            **kwargs,
        }

    def __enter__(self) -> _TemporaryFileWrapper:
        file = NamedTemporaryFile(delete=True, **self.named_temporary_file_args)
        with requests.get(self.url, stream=True) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=8192):
                file.write(chunk)
        file.flush()
        self.downloaded_file = file
        return self.downloaded_file

    def __exit__(self, *_):
        if self.downloaded_file:
            self.downloaded_file.close()


class DjangoReversionDataFixHelper:
    @staticmethod
    def _get_content_type(content_type_model: typing.Type[ContentType], model: typing.Type[models.Model], using):
        version_options = _get_options(model)
        return content_type_model.objects.db_manager(using).get_for_model(
            model,
            for_concrete_model=version_options.for_concrete_model,
        )

    @classmethod
    def get_for_model(
        cls,
        content_type_model: typing.Type[ContentType],
        version_model: typing.Type[Version],
        model: typing.Type[models.Model],
    ):
        model_db = router.db_for_write(model)
        content_type = cls._get_content_type(content_type_model, model, version_model.objects.db)
        return version_model.objects.filter(
            content_type=content_type,
            db=model_db,
        )

    @classmethod
    def _date_field_adjust(
        cls,
        content_type_model: typing.Type[ContentType],
        version_model: typing.Type[Version],
        model: typing.Type[models.Model],
        fields: typing.List[str],
        parser: typing.Callable,
        renderer: typing.Callable,
    ):
        updated_versions = []
        for version in cls.get_for_model(content_type_model, version_model, model):
            updated_serialized_data = json.loads(version.serialized_data)
            has_changed = False
            for field in fields:
                _value = updated_serialized_data[0]["fields"].get(field)
                if _value is None:
                    continue
                updated_value = parser(_value)
                if updated_value is None:
                    # For other format, parser should return None
                    continue
                updated_serialized_data[0]["fields"][field] = renderer(updated_value)
                has_changed = True
            if has_changed:
                version.serialized_data = json.dumps(updated_serialized_data)
                updated_versions.append(version)

        version_model.objects.bulk_update(updated_versions, fields=("serialized_data",))

    @classmethod
    def date_fields_to_datetime(
        cls,
        content_type_model: typing.Type[ContentType],
        version_model: typing.Type[Version],
        model: typing.Type[models.Model],
        fields: typing.List[str],
    ):
        return cls._date_field_adjust(
            content_type_model,
            version_model,
            model,
            fields,
            parse_date,
            lambda x: datetime.datetime.combine(x, datetime.datetime.min.time()).isoformat(),
        )

    @classmethod
    def datetime_fields_to_date(
        cls,
        content_type_model: typing.Type[ContentType],
        version_model: typing.Type[Version],
        model: typing.Type[models.Model],
        fields: typing.List[str],
    ):
        return cls._date_field_adjust(
            content_type_model,
            version_model,
            model,
            fields,
            parse_datetime,
            lambda x: x.date().isoformat(),
        )


class SpreadSheetContentNegotiation(DefaultContentNegotiation):
    MEDIA_TYPES = [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/html",  # To allow download from browser
    ]

    def select_renderer(self, request, renderers, format_suffix):
        accepts = self.get_accept_list(request)
        if not set(self.MEDIA_TYPES).intersection(set(accepts)):
            raise exceptions.NotAcceptable(available_renderers=renderers)
        if settings.TESTING:  # NOTE: Quick hack to test permission of the views
            return super().select_renderer(request, renderers, format_suffix)
        return (None, self.MEDIA_TYPES[0])


def pretty_seconds(seconds):
    return datetime.timedelta(seconds=seconds)


def logger_context(data):
    """
    This function is used to use a unique key to pass logging context to sentry and console
    Check main.settings.py::log_render_extra_context
    """
    return {"context": data}
