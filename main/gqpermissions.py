import typing

from asgiref.sync import sync_to_async
from strawberry.permission import BasePermission
from strawberry.types import Info


class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    @sync_to_async
    def has_permission(self, source: typing.Any, info: Info, **_) -> bool:
        user = info.context.request.user
        return bool(user and user.is_authenticated)
