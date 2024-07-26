import typing

import strawberry
import strawberry_django
from django.db import models

from main.context import Info
from utils.common import get_queryset_for_model
from utils.types import PolygonScalar, string_field

from .models import District


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
