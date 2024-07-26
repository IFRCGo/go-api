import strawberry
import strawberry_django

from .models import District


@strawberry_django.ordering.order(District)
class DistrictOrder:
    id: strawberry.auto
