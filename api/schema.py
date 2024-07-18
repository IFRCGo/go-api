from typing import List

import strawberry
import strawberry_django

from .types import Country  # CountryInput,; CountryPartialInput,

# from strawberry_django import auth, mutations


@strawberry.type
class Query:
    country: Country = strawberry_django.field()
    countries: List[Country] = strawberry_django.field()


schema = strawberry.Schema(query=Query)
