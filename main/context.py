from dataclasses import dataclass

from strawberry.django.context import StrawberryDjangoContext
from strawberry.types import Info as _Info

from .dataloaders import GlobalDataLoader


@dataclass
class GraphQLContext(StrawberryDjangoContext):
    dl: GlobalDataLoader


# NOTE: This is for type support only, is there a better way?
class Info(_Info):
    context: GraphQLContext  # type: ignore[reportIncompatibleMethodOverride]
