import strawberry
import strawberry_django

from .models import District, Admin2


@strawberry_django.ordering.order(District)
class DistrictOrder:
    id: strawberry.auto


@strawberry_django.ordering.order(Admin2)
class Admin2Order:
    id: strawberry.auto
