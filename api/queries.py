import strawberry
import strawberry_django

from main.graphql.context import Info
from utils.strawberry.paginations import CountList, pagination_field

from .filters import AppealFilter
from .orders import AppealOrder
from .types import AppealType


@strawberry.type
class PrivateQuery:
    # Paginated ----------------------------
    appeals: CountList[AppealType] = pagination_field(
        pagination=True,
        filters=AppealFilter,
        order=AppealOrder,
    )

    # Single ----------------------------
    @strawberry_django.field
    async def appeal(self, info: Info, pk: strawberry.ID) -> AppealType | None:
        return await AppealType.get_queryset(None, None, info).filter(pk=pk).afirst()
