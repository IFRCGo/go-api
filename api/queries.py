import strawberry
import strawberry_django

from main.context import Info
from utils.paginations import CountList, pagination_field

from .filters import DistrictFilter
from .orders import DistrictOrder
from .types import DistrictType


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


@strawberry.type
class PrivateQuery:
    noop: strawberry.ID = strawberry.ID("noop")
