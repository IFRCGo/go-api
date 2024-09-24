import typing
from django.db import models


DjangoModel = typing.TypeVar("DjangoModel", bound=models.Model)


# -- Helper
def load_model_objects(
    Model: typing.Type[DjangoModel],
    keys: list[int],
) -> list[DjangoModel]:
    qs = Model.objects.filter(id__in=keys)
    _map = {obj.pk: obj for obj in qs}
    return [_map[key] for key in keys]
