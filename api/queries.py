import strawberry
import strawberry_django

from main.context import Info
from utils.paginations import CountList, pagination_field

from .filters import Admin2Filter, DistrictFilter
from .orders import Admin2Order, DistrictOrder
from .types import Admin2Type, CountryType, DistrictType


@strawberry.type
class PublicQuery:

    Countries: CountList[CountryType] = pagination_field(
        pagination=True,
    )

    @strawberry_django.field
    async def country(self, info: Info, pk: strawberry.ID) -> CountryType | None:
        return await CountryType.get_queryset(None, None, info).filter(pk=pk).afirst()

    Districts: CountList[DistrictType] = pagination_field(
        pagination=True,
        filters=DistrictFilter,
        order=DistrictOrder,
    )

    @strawberry_django.field
    async def district(self, info: Info, pk: strawberry.ID) -> DistrictType | None:
        return await DistrictType.get_queryset(None, None, info).filter(pk=pk).afirst()

    Admin2s: CountList[Admin2Type] = pagination_field(
        pagination=True,
        filters=Admin2Filter,
        order=Admin2Order,
    )

    @strawberry_django.field
    async def admin2(self, info: Info, pk: strawberry.ID) -> Admin2Type | None:
        return await Admin2Type.get_queryset(None, None, info).filter(pk=pk).afirst()


@strawberry.type
class PrivateQuery:
    noop: strawberry.ID = strawberry.ID("noop")
