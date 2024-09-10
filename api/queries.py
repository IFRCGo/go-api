import strawberry
import strawberry_django

from main.context import Info
from utils.paginations import CountList, pagination_field

from .filters import DistrictFilter, Admin2Filter
from .orders import DistrictOrder, Admin2Order
from .types import DistrictType, Admin2Type


@strawberry.type
class PublicQuery:

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
