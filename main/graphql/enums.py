import dataclasses
import typing

import strawberry

from api.enums import enum_map as api_enum_map

ENUM_TO_STRAWBERRY_ENUM_MAP: dict[str, typing.Union[type, typing.Annotated]] = {
    **api_enum_map,
}


class AppEnumData:
    def __init__(self, enum):
        self.enum = enum

    @property
    def key(self):
        return self.enum

    @property
    def label(self):
        return str(self.enum.label)


def generate_app_enum_collection_data(name):
    def _get_enum_type(enum):
        if typing.get_origin(enum) is typing.Annotated:
            return typing.get_args(enum)[1]
        return enum

    params = {
        field_name: [
            AppEnumData(e)
            for e in _get_enum_type(enum)  # type: ignore[reportGeneralTypeIssues]
        ]
        for field_name, enum in ENUM_TO_STRAWBERRY_ENUM_MAP.items()
    }
    return type(name, (), params)


AppEnumCollectionData = generate_app_enum_collection_data("AppEnumCollectionData")


def generate_type_for_enum(name, Enum):
    return strawberry.type(
        dataclasses.make_dataclass(
            f"AppEnumCollection{name}",
            [
                ("key", Enum),
                ("label", str),
            ],
        )
    )


def _enum_type(name, Enum):
    EnumType = generate_type_for_enum(name, Enum)

    @strawberry.field
    def _field() -> list[EnumType]:  # type: ignore[reportGeneralTypeIssues]
        return [
            EnumType(
                key=e,
                label=e.label,
            )
            for e in Enum
        ]

    return list[EnumType], _field


def generate_type_for_enums():
    enum_fields = [
        (
            enum_field_name,
            *_enum_type(enum_field_name, enum),
        )
        for enum_field_name, enum in ENUM_TO_STRAWBERRY_ENUM_MAP.items()
    ]
    return strawberry.type(
        dataclasses.make_dataclass(
            "AppEnumCollection",
            enum_fields,
        )
    )


AppEnumCollection = generate_type_for_enums()
