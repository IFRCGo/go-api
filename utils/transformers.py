import dataclasses
import datetime
import decimal
import typing
from collections import OrderedDict
from functools import singledispatch
from importlib import import_module

import strawberry
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string
from rest_framework import fields as drf_fields
from rest_framework import serializers
from strawberry.annotation import StrawberryAnnotation
from strawberry.file_uploads import Upload as StrawberryUploadField
from strawberry.types import get_object_definition
from strawberry.types.field import StrawberryField
from strawberry_django.type import _process_type

from . import types
from .enums import get_enum_name_from_django_field
from .serializers import IntegerIDField, StringIDField

"""
XXX:
- This is a experimental transformer which translates DRF -> Strawberry Input Type
- Also overwrites some modules
"""


@singledispatch
def get_strawberry_type_from_serializer_field(field):
    raise ImproperlyConfigured(
        "Don't know how to convert the serializer field %s (%s) " "to strawberry type" % (field, field.__class__)
    )


@get_strawberry_type_from_serializer_field.register(serializers.ListField)
@get_strawberry_type_from_serializer_field.register(serializers.ListSerializer)
@get_strawberry_type_from_serializer_field.register(serializers.MultipleChoiceField)  # type: ignore[reportArgumentType]
def convert_list_serializer_to_field(field):
    child_type = get_strawberry_type_from_serializer_field(field.child)
    return list[child_type]


@get_strawberry_type_from_serializer_field.register(serializers.Serializer)
@get_strawberry_type_from_serializer_field.register(serializers.ModelSerializer)  # type: ignore[reportArgumentType]
def convert_serializer_to_field(_):
    return strawberry.field


@get_strawberry_type_from_serializer_field.register(serializers.ManyRelatedField)  # type: ignore[reportArgumentType]
def convert_serializer_field_to_many_related_id(_):
    return list[strawberry.ID]


@get_strawberry_type_from_serializer_field.register(serializers.PrimaryKeyRelatedField)
@get_strawberry_type_from_serializer_field.register(IntegerIDField)
@get_strawberry_type_from_serializer_field.register(StringIDField)  # type: ignore[reportArgumentType]
def convert_serializer_field_to_id(_):
    return strawberry.ID


@get_strawberry_type_from_serializer_field.register(serializers.JSONField)
@get_strawberry_type_from_serializer_field.register(serializers.DictField)  # type: ignore[reportArgumentType]
def convert_serializer_field_to_generic_scalar(_):
    return types.GenericScalar


@get_strawberry_type_from_serializer_field.register(serializers.Field)  # type: ignore[reportArgumentType]
def convert_serializer_field_to_string(field):
    return str


@get_strawberry_type_from_serializer_field.register(serializers.IntegerField)  # type: ignore[reportArgumentType]
def convert_serializer_field_to_int(_):
    return int


@get_strawberry_type_from_serializer_field.register(serializers.BooleanField)  # type: ignore[reportArgumentType]
def convert_serializer_field_to_bool(_):
    return bool


@get_strawberry_type_from_serializer_field.register(serializers.FloatField)  # type: ignore[reportArgumentType]
def convert_serializer_field_to_float(_):
    return float


@get_strawberry_type_from_serializer_field.register(serializers.DecimalField)  # type: ignore[reportArgumentType]
def convert_serializer_field_to_decimal(_):
    return decimal.Decimal


@get_strawberry_type_from_serializer_field.register(serializers.DateTimeField)  # type: ignore[reportArgumentType]
def convert_serializer_field_to_datetime_time(_):
    return datetime.datetime


@get_strawberry_type_from_serializer_field.register(serializers.DateField)  # type: ignore[reportArgumentType]
def convert_serializer_field_to_date_time(_):
    return datetime.date


@get_strawberry_type_from_serializer_field.register(serializers.TimeField)  # type: ignore[reportArgumentType]
def convert_serializer_field_to_time(_):
    return datetime.time


@get_strawberry_type_from_serializer_field.register(serializers.FileField)  # type: ignore[reportArgumentType]
def convert_serializer_field_to_file_field(_):
    return StrawberryUploadField


@get_strawberry_type_from_serializer_field.register(serializers.ChoiceField)
def convert_serializer_field_to_enum(field):
    ENUM_TO_STRAWBERRY_ENUM_MAP: dict[str, type] = import_string(settings.STRAWBERRY_ENUM_TO_STRAWBERRY_ENUM_MAP)

    # Try normal TextChoices/IntegerChoices enum
    custom_name = get_enum_name_from_django_field(field)
    if custom_name not in ENUM_TO_STRAWBERRY_ENUM_MAP:
        # Try django_enumfield (NOTE: Let's try to avoid this)
        custom_name = type(list(field.choices.values())[-1]).__name__
    if custom_name is None:
        raise Exception(f"Enum name generation failed for {field=}")
    return ENUM_TO_STRAWBERRY_ENUM_MAP[custom_name]


convert_serializer_to_type_cache = {}


def convert_serializer_to_type(serializer_class, name=None, partial=False):
    """
    graphene_django.rest_framework.serializer_converter.convert_serializer_to_type
    """
    # Generate naming
    ref_name = name
    if ref_name is None:
        serializer_name = serializer_class.__name__
        serializer_name = "".join("".join(serializer_name.split("ModelSerializer")).split("Serializer"))
        ref_name = f"{serializer_name}NestInputType"
        if partial:
            ref_name = f"{serializer_name}NestUpdateInputType"

    cached_type = convert_serializer_to_type_cache.get(ref_name, None)
    if cached_type:
        return cached_type

    ret_type = generate_type_for_serializer(ref_name, serializer_class, partial=partial)
    convert_serializer_to_type_cache[ref_name] = ret_type
    return ret_type


def convert_serializer_field(field, convert_choices_to_enum=True, force_optional=False):
    """
    Converts a django rest frameworks field to a graphql field
    and marks the field as required if we are creating an type
    and the field itself is required
    """

    kwargs = {
        "description": field.help_text,  # XXX: NOT WORKING
        "python_name": field.field_name,
        "graphql_name": field.field_name,
    }
    is_required = field.required and not force_optional
    if field.default != drf_fields.empty:
        if field.default.__class__.__hash__ is None:  # Mutable
            kwargs["default_factory"] = lambda: field.default  # type: ignore[reportGeneralTypeIssues] FIXME
        else:
            kwargs["default"] = field.default
    else:
        kwargs["default"] = dataclasses.MISSING

    if isinstance(field, serializers.ChoiceField) and not convert_choices_to_enum:
        graphql_type = str
    else:
        graphql_type = get_strawberry_type_from_serializer_field(field)
        # if graphql_type == str:
        #   is_required = not field.null and not field.blank
        #   kwargs['parse_value'] -> null -> '' -- when not is_required
        #   XXX: does UNSET has any issue here?

    # if it is a tuple or a list it means that we are returning
    # the graphql type and the child type
    if isinstance(graphql_type, (list, tuple)):
        kwargs["of_type"] = graphql_type[1]
        graphql_type = graphql_type[0]

    if isinstance(field, serializers.Serializer):
        pass
    elif isinstance(field, serializers.ListSerializer):
        field = field.child
        of_type = convert_serializer_to_type(field.__class__, partial=force_optional)
        graphql_type = list[of_type]

    if not is_required:
        if "default" not in kwargs or "default_factory" not in kwargs:
            kwargs["default"] = strawberry.UNSET
        graphql_type = typing.Optional[graphql_type]

    return graphql_type, StrawberryField(
        type_annotation=StrawberryAnnotation(
            annotation=graphql_type,
        ),
        **kwargs,
    )


def fields_for_serializer(
    serializer,
    only_fields,
    exclude_fields,
    convert_choices_to_enum=True,
    partial=False,
):
    """
    NOTE: Same as the original definition. Needs overriding to
    handle relative import of convert_serializer_field
    """
    fields = OrderedDict()
    for name, field in serializer.fields.items():
        is_not_in_only = only_fields and name not in only_fields
        is_excluded = name in exclude_fields
        if is_not_in_only or is_excluded:
            continue
        fields[name] = convert_serializer_field(
            field,
            convert_choices_to_enum=convert_choices_to_enum,
            force_optional=partial,
        )
    return fields


def generate_type_for_serializer(
    name: str,
    serializer_class,
    partial=False,
) -> type:
    """
    Don't use this directly, use convert_serializer_to_type instead
    """
    data_members = fields_for_serializer(
        serializer_class(),
        only_fields=[],
        exclude_fields=[],
        partial=partial,
    )
    defaults_model_fields = [
        (name, _type, field)
        for name, (_type, field) in data_members.items()
        if (field.default is not dataclasses.MISSING or field.default_factory is not dataclasses.MISSING)
    ]
    non_defaults_model_fields = [
        (name, _type, field)
        for name, (_type, field) in data_members.items()
        if (field.default is dataclasses.MISSING and field.default_factory is dataclasses.MISSING)
    ]
    return strawberry.input(
        dataclasses.make_dataclass(
            name,
            [
                *non_defaults_model_fields,
                *defaults_model_fields,
            ],
        )
    )


# Custom GraphQL type generation logics


class MonkeyPatch:
    @classmethod
    def _process_type(
        cls,
        *args,
        **kwargs,
    ):
        """
        For field with <field>_id, let's use ID instead of object while rendering.
        For eg:
            For field: `member_id: strawberry.ID`, where `member` is a ForeignKey
                Previous behaviour:
                    member_id gives value "Member object (1)" == str(obj.member)
                New behaviour:
                    member_id gives value "1" == str(obj.member_id)
        NOTE: This doesn't work with Mixin
        """
        response = _process_type(*args, **kwargs)
        # Custom Logic
        obj_definition = get_object_definition(response)
        assert obj_definition is not None
        for field in obj_definition.fields:
            if field.name.endswith("_id"):
                field.django_name = field.name  # type: ignore[reportGeneralTypeIssues] FIXME
        return response


import_module("strawberry_django.type")._process_type = MonkeyPatch._process_type  # type: ignore[reportGeneralTypeIssues]
