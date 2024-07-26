from __future__ import annotations

from functools import cached_property
from typing import Any, Callable, Generic, Type, TypeVar

import strawberry
from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import models
from strawberry.types import Info
from strawberry_django.fields.field import StrawberryDjangoField
from strawberry_django.filters import apply as apply_filters
from strawberry_django.ordering import apply as apply_orders
from strawberry_django.pagination import (
    OffsetPaginationInput,
    StrawberryDjangoPagination,
)
from strawberry_django.resolvers import django_resolver
from strawberry_django.utils.typing import unwrap_type


def process_pagination(pagination: OffsetPaginationInput):
    """
    Mutate pagination object to make sure limit are under given threshold
    """
    if pagination is strawberry.UNSET or pagination is None:
        pagination = OffsetPaginationInput(
            offset=0,
            limit=settings.STRAWBERRY_DEFAULT_PAGINATION_LIMIT,
        )
    if pagination.limit == -1:
        pagination.limit = settings.STRAWBERRY_DEFAULT_PAGINATION_LIMIT
    pagination.limit = min(pagination.limit, settings.STRAWBERRY_MAX_PAGINATION_LIMIT)
    return pagination


def apply_pagination(pagination, queryset):
    pagination = process_pagination(pagination)
    start = pagination.offset
    stop = start + pagination.limit
    return queryset[start:stop]


class CountBeforePaginationMonkeyPatch(StrawberryDjangoPagination):
    def get_queryset(
        self,
        queryset: models.QuerySet[Any],
        info,
        pagination=strawberry.UNSET,
        **kwargs,
    ) -> models.QuerySet:
        queryset = apply_pagination(pagination, queryset)
        return super(StrawberryDjangoPagination, self).get_queryset(
            queryset,
            info,
            **kwargs,
        )


StrawberryDjangoPagination.get_queryset = CountBeforePaginationMonkeyPatch.get_queryset  # type: ignore[reportGeneralTypeIssues]
OffsetPaginationInput.limit = 1  # TODO: This is not working

DjangoModelTypeVar = TypeVar("DjangoModelTypeVar")


@strawberry.type
class CountList(Generic[DjangoModelTypeVar]):
    limit: int
    offset: int
    queryset: strawberry.Private[
        models.QuerySet[DjangoModelTypeVar] | list[DjangoModelTypeVar]  # type: ignore[reportGeneralTypeIssues]
    ]
    get_count: strawberry.Private[Callable]

    @strawberry.field
    async def count(self) -> int:
        return await self.get_count()

    @strawberry.field
    async def items(self) -> list[DjangoModelTypeVar]:
        queryset = self.queryset
        if type(queryset) in [list, tuple]:
            return list(queryset)
        return [d async for d in queryset]  # type: ignore[reportGeneralTypeIssues]


class StrawberryDjangoCountList(StrawberryDjangoField):
    @cached_property
    def is_list(self) -> bool:
        return True

    @cached_property
    def django_model(self) -> type[models.Model] | None:
        super().django_model
        # Hack to get the nested type of `CountList` to register
        # as the type of this field
        items_type = [
            f.type
            for f in self.type.__strawberry_definition__.fields  # type: ignore[reportGeneralTypeIssues]
            if f.name == "items"
        ]
        if len(items_type) > 0:
            type_ = unwrap_type(items_type[0])
            self._base_type = type_
            return type_.__strawberry_django_definition__.model  # type: ignore[reportGeneralTypeIssues]
        return None

    def get_result(
        self,
        source: models.Model | None,
        info: Any,
        args: list[Any],
        kwargs: dict[str, Any],
    ):
        return self.resolver(source, info, args, kwargs)

    def resolver(
        self,
        source: Any,
        info: Info | None,
        args: list[Any],
        kwargs: dict[str, Any],
    ) -> Any:
        pk: int = kwargs.get("pk", strawberry.UNSET)
        filters: Type = kwargs.get("filters", strawberry.UNSET)
        order: Type = kwargs.get("order", strawberry.UNSET)
        pagination: OffsetPaginationInput = kwargs.get("pagination", strawberry.UNSET)

        if self.django_model is None or self._base_type is None:
            # This needs to be fixed by developers
            raise Exception("django_model should be defined!!")

        queryset = self.django_model.objects.all()

        type_ = self._base_type
        type_ = unwrap_type(type_)
        get_queryset = getattr(type_, "get_queryset", None)
        if get_queryset:
            queryset = get_queryset(type_, queryset, info)

        queryset = apply_filters(filters, queryset, info, pk)

        queryset = apply_orders(order, queryset, info=info)
        # Add a default order_by id if there is none defined/used
        if not queryset.query.order_by:
            queryset = queryset.order_by("-pk")

        _current_queryset = queryset._chain()  # type: ignore[reportGeneralTypeIssues]

        @sync_to_async
        def get_count():
            return _current_queryset.values("pk").count()

        pagination = process_pagination(pagination)

        queryset = self.apply_pagination(queryset, pagination)
        return CountList[self._base_type](  # type: ignore[reportGeneralTypeIssues]
            get_count=get_count,
            queryset=queryset,
            limit=pagination.limit,
            offset=pagination.offset,
        )


def pagination_field(
    resolver=None,
    *,
    name=None,
    field_name=None,
    filters=strawberry.UNSET,
    default=strawberry.UNSET,
    **kwargs,
) -> Any:
    field_ = StrawberryDjangoCountList(
        python_name=None,
        graphql_name=name,
        type_annotation=None,
        filters=filters,
        django_name=field_name,
        default=default,
        **kwargs,
    )
    if resolver:
        resolver = django_resolver(resolver)
        return field_(resolver)
    return field_
