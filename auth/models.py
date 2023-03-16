from typing import Optional
from enum import Enum, auto, unique

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from api.models import Country, Region


# DREF
class DREFRoles(models.IntegerChoices):
    ADMIN = 0, "Admin"
    COORDINATOR = 100, "Coordinator"


@unique
class DREFPermissions(Enum):
    VIEW = auto()  # View can also export
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()
    PUBLISH = auto()
    APPROVE = auto()

    @staticmethod
    def get_for_role(role: DREFRoles):
        # TODO: assign appropriate permissions and roles
        if role == DREFRoles.ADMIN:
            return [
                DREFPermissions.VIEW,
                DREFPermissions.CREATE,
                DREFPermissions.UPDATE,
                DREFPermissions.DELETE,
            ]
        elif role == DREFRoles.COORDINATOR:
            return [
                DREFPermissions.VIEW,
                DREFPermissions.CREATE,
            ]
        return []


# 3W
class THREE_WRoles(models.IntegerChoices):
    ADMIN = 0, "Admin"
    COORDINATOR = 100, "Coordinator"


@unique
class THREE_WPermissions(Enum):
    VIEW = auto()
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()

    @staticmethod
    def get_for_role(role: THREE_WRoles):
        # TODO: assign appropriate permissions and roles
        if role == THREE_WRoles.ADMIN:
            return [
                THREE_WPermissions.VIEW,
                THREE_WPermissions.CREATE,
                THREE_WPermissions.UPDATE,
                THREE_WPermissions.DELETE,
            ]
        elif role == THREE_WRoles.COORDINATOR:
            return [
                THREE_WPermissions.VIEW,
                THREE_WPermissions.CREATE,
            ]
        return []


class UserPermission(models.Model):
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    # NOTE: Country and Region are mutually exclusive.. XXX: Should we create seperate ones?
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, null=True, blank=True)

    # Module specific roles
    dref_role = models.PositiveSmallIntegerField(choices=DREFRoles)
    three_w_role = models.PositiveSmallIntegerField(choices=THREE_WRoles)

    region_id: Optional[int]
    country_id: Optional[int]

    def clean(self):
        if all([
            self.country_id is not None,
            self.region_id is not None,
        ]):
            raise ValidationError(_('Country and Region are mutually exclusive.'))
