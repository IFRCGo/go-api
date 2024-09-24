import typing
from asgiref.sync import sync_to_async
from django.utils.functional import cached_property
from strawberry.dataloader import DataLoader
from utils.strawberry.dataloaders import load_model_objects

from .models import Country, DisasterType

if typing.TYPE_CHECKING:
    from .types import CountryType, DisasterTypeType


def load_country(keys: list[int]) -> list["CountryType"]:
    return load_model_objects(Country, keys)  # type: ignore[reportReturnType]


def load_disaster_type(keys: list[int]) -> list["DisasterTypeType"]:
    return load_model_objects(DisasterType, keys)  # type: ignore[reportReturnType]


class ApiDataLoader:
    @cached_property
    def load_country(self):
        return DataLoader(load_fn=sync_to_async(load_country))

    @cached_property
    def load_disaster_type(self):
        return DataLoader(load_fn=sync_to_async(load_disaster_type))
