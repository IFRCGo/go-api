import logging
import typing
from dataclasses import is_dataclass

import strawberry
from strawberry.types import Info
from strawberry.utils.str_converters import to_camel_case

from utils.common import to_snake_case

logger = logging.getLogger(__name__)

ResultTypeVar = typing.TypeVar("ResultTypeVar")


ARRAY_NON_MEMBER_ERRORS = "nonMemberErrors"

# generalize all the CustomErrorType
CustomErrorType = strawberry.scalar(
    typing.NewType("CustomErrorType", object),
    description="A generic type to return error messages",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)


def process_input_data(data) -> dict | list:
    """
    Return dict from Strawberry Input Object
    """
    # TODO: Write test
    if type(data) in [tuple, list]:
        return [process_input_data(datum) for datum in data]
    native_dict = {}
    for key, value in data.__dict__.items():
        if value == strawberry.UNSET:
            continue
        if isinstance(value, list):
            _list_value = []
            for _value in value:
                if is_dataclass(_value):
                    _list_value.append(process_input_data(_value))
                else:
                    _list_value.append(_value)
            native_dict[key] = _list_value
            continue
        if is_dataclass(value):
            native_dict[key] = process_input_data(value)
        else:
            native_dict[key] = value
    return native_dict


@strawberry.type
class ArrayNestedErrorType:
    client_id: str
    messages: typing.Optional[str]
    object_errors: typing.Optional[list[typing.Optional[CustomErrorType]]]

    def keys(self):
        return ["client_id", "messages", "object_errors"]

    def __getitem__(self, key):
        key = to_snake_case(key)
        if key in ("object_errors",) and getattr(self, key):
            return [dict(each) for each in getattr(self, key)]
        return getattr(self, key)


@strawberry.type
class _CustomErrorType:
    field: str
    client_id: str | None = None
    messages: typing.Optional[str]
    object_errors: typing.Optional[list[typing.Optional[CustomErrorType]]]
    array_errors: typing.Optional[list[typing.Optional[ArrayNestedErrorType]]]

    DEFAULT_ERROR_MESSAGE = "Something unexpected has occurred. Please contact an admin to fix this issue."

    @staticmethod
    def generate_message(message: str = DEFAULT_ERROR_MESSAGE) -> CustomErrorType:
        return CustomErrorType(
            [
                dict(
                    field="nonFieldErrors",
                    messages=message,
                    object_errors=None,
                    array_errors=None,
                )
            ]
        )

    def keys(self):
        return ["field", "client_id", "messages", "object_errors", "array_errors"]

    def __getitem__(self, key):
        key = to_snake_case(key)
        if key in ("object_errors", "array_errors") and getattr(self, key):
            return [dict(each) for each in getattr(self, key)]
        return getattr(self, key)


def serializer_error_to_error_types(errors: dict, initial_data: dict | None = None) -> list:
    initial_data = initial_data or dict()
    node_client_id = initial_data.get("client_id")
    error_types = list()
    for field, value in errors.items():
        if isinstance(value, dict):
            error_types.append(
                _CustomErrorType(
                    client_id=node_client_id,
                    field=to_camel_case(field),
                    object_errors=value,  # type: ignore[reportGeneralTypeIssues]
                    array_errors=None,
                    messages=None,
                )
            )
        elif isinstance(value, list):
            if isinstance(value[0], str):
                if isinstance(initial_data.get(field), list):
                    # we have found an array input with top level error
                    error_types.append(
                        _CustomErrorType(
                            client_id=node_client_id,
                            field=to_camel_case(field),
                            array_errors=[
                                ArrayNestedErrorType(
                                    client_id=ARRAY_NON_MEMBER_ERRORS,
                                    messages="".join(str(msg) for msg in value),
                                    object_errors=None,
                                )
                            ],
                            messages=None,
                            object_errors=None,
                        )
                    )
                else:
                    error_types.append(
                        _CustomErrorType(
                            client_id=node_client_id,
                            field=to_camel_case(field),
                            messages=", ".join(str(msg) for msg in value),
                            object_errors=None,
                            array_errors=None,
                        )
                    )
            elif isinstance(value[0], dict):
                array_errors = []
                for pos, array_item in enumerate(value):
                    if not array_item:
                        # array item might not have error
                        continue
                    # fetch array.item.client_id from the initial data
                    array_client_id = initial_data[field][pos].get("client_id", f"NOT_FOUND_{pos}")
                    array_errors.append(
                        ArrayNestedErrorType(
                            client_id=array_client_id,
                            object_errors=serializer_error_to_error_types(array_item, initial_data[field][pos]),
                            messages=None,
                        )
                    )
                error_types.append(
                    _CustomErrorType(
                        client_id=node_client_id,
                        field=to_camel_case(field),
                        array_errors=array_errors,
                        object_errors=None,
                        messages=None,
                    )
                )
        else:
            # fallback
            error_types.append(
                _CustomErrorType(
                    field=to_camel_case(field),
                    messages=" ".join(str(msg) for msg in value),
                    array_errors=None,
                    object_errors=None,
                )
            )
    return error_types


def mutation_is_not_valid(serializer) -> CustomErrorType | None:
    """
    Checks if serializer is valid, if not returns list of errorTypes
    """
    if not serializer.is_valid():
        errors = serializer_error_to_error_types(serializer.errors, serializer.initial_data)
        return CustomErrorType([dict(each) for each in errors])
    return None


@strawberry.type
class MutationResponseType(typing.Generic[ResultTypeVar]):
    ok: bool = True
    errors: typing.Optional[CustomErrorType] = None
    result: typing.Optional[ResultTypeVar] = None


@strawberry.type
class BulkBasicMutationResponseType(typing.Generic[ResultTypeVar]):
    errors: typing.Optional[list[CustomErrorType]] = None
    results: typing.Optional[list[ResultTypeVar]] = None


@strawberry.type
class BulkMutationResponseType(typing.Generic[ResultTypeVar]):
    errors: typing.Optional[list[CustomErrorType]] = None
    results: typing.Optional[list[ResultTypeVar]] = None
    deleted: typing.Optional[list[ResultTypeVar]] = None


@strawberry.type
class MutationEmptyResponseType:
    ok: bool = True
    errors: typing.Optional[CustomErrorType] = None


def get_serializer_context(info: Info):
    return {
        "graphql_info": info,
        "request": info.context.request,
        "active_project": info.context.active_project,
    }


def generate_error_message(message: str = _CustomErrorType.DEFAULT_ERROR_MESSAGE) -> CustomErrorType:
    return _CustomErrorType.generate_message(message)
