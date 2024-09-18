import strawberry
import strawberry_django

from .models import Appeal


@strawberry_django.ordering.order(Appeal)
class AppealOrder:
    id: strawberry.auto
    name: strawberry.auto
    created_at: strawberry.auto
