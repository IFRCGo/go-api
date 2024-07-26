import strawberry
from strawberry.django.views import AsyncGraphQLView

# Imported to make sure strawberry custom modules are loadded first
import utils.transformers  # noqa
from api import queries as user_queries

from .context import GraphQLContext
from .dataloaders import GlobalDataLoader

# from .enums import AppEnumCollection, AppEnumCollectionData
from .gqpermissions import IsAuthenticated


class CustomAsyncGraphQLView(AsyncGraphQLView):
    async def get_context(self, *args, **kwargs) -> GraphQLContext:
        return GraphQLContext(
            *args,
            **kwargs,
            dl=GlobalDataLoader(),
        )


@strawberry.type
class PublicQuery(
    user_queries.PublicQuery,
):
    id: strawberry.ID = strawberry.ID("public")


@strawberry.type
class PrivateQuery(
    user_queries.PrivateQuery,
):
    id: strawberry.ID = strawberry.ID("private")


@strawberry.type
class PublicMutation:
    id: strawberry.ID = strawberry.ID("public")


@strawberry.type
class PrivateMutation:
    id: strawberry.ID = strawberry.ID("private")


@strawberry.type
class Query:
    public: PublicQuery = strawberry.field(resolver=lambda: PublicQuery())
    private: PrivateQuery = strawberry.field(permission_classes=[IsAuthenticated], resolver=lambda: PrivateQuery())
    # zol enums: AppEnumCollection = strawberry.field(resolver=lambda: AppEnumCollectionData())


@strawberry.type
class Mutation:
    public: PublicMutation = strawberry.field(resolver=lambda: PublicMutation())
    private: PrivateMutation = strawberry.field(resolver=lambda: PrivateMutation(), permission_classes=[IsAuthenticated])


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
)
