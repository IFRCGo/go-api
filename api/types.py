import typing

import strawberry
import strawberry_django
from django.db import models

from main.context import Info
from utils.common import get_queryset_for_model
from utils.types import PolygonScalar, string_field

from .models import District, Admin2


@strawberry_django.type(District)
class DistrictType:
    id: strawberry.ID
    name = string_field(District.name)
    bbox: PolygonScalar | None

    if typing.TYPE_CHECKING:
        country_id = District.country_id
        pk = District.pk
    else:
        country_id: strawberry.ID

    @staticmethod
    def get_queryset(_, queryset: models.QuerySet, info: Info | None):
        return get_queryset_for_model(District, queryset).defer("centroid")


@strawberry_django.type(Admin2)
class Admin2Type:
    id: strawberry.ID
    name = string_field(Admin2.name)
    created_at = string_field(Admin2.created_at)
    bbox: PolygonScalar | None

    if typing.TYPE_CHECKING:
        admin1_id = Admin2.admin1_id
        pk = Admin2.pk
    else:
        admin1_id: strawberry.ID

    @staticmethod
    def get_queryset(_, queryset: models.QuerySet, info: Info | None):
        return get_queryset_for_model(Admin2, queryset).defer("centroid")
