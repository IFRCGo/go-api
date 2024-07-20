from typing import List

import strawberry
import strawberry_django as s
from strawberry.schema.config import StrawberryConfig
from strawberry_django.optimizer import DjangoOptimizerExtension

from .types import Country, CountryInput, CountryPartialInput

# from strawberry_django import auth, mutations


@strawberry.type
class Query:
    country: Country = s.field()
    countries: List[Country] = s.field()


@strawberry.type
class Mutation:
    create_Country: Country = s.mutations.create(CountryInput)
    create_Countrys: List[Country] = s.mutations.create(CountryInput)
    update_Countrys: List[Country] = s.mutations.update(CountryPartialInput)
    delete_Countrys: List[Country] = s.mutations.delete()


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        DjangoOptimizerExtension,
    ],
    config=StrawberryConfig(auto_camel_case=False),
)
