from django.db import models
from django.conf import settings
from enumfields import Enum, IntEnum, EnumIntegerField, EnumField
from api.models import Country, District


class ProgrammeTypes(IntEnum):
    BILATERAL = 0
    MULTILATERAL = 1

class Sectors(IntEnum):
    WASH = 0

class Statuses(IntEnum):
    IN_PROGRESS = 0
    COMPLETED = 1

class Currencies(Enum):
    SWISS_FRANC = 'CHF'
    EURO = 'EUR'
    US_DOLLAR = 'USD'

class Project(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL) # user who created this project
    reporting_ns = models.ForeignKey(Country, on_delete=models.CASCADE) # this is the national society that is reporting the project
    project_district = models.ForeignKey(District, on_delete=models.CASCADE) # this is the district where the project is actually taking place
    name = models.TextField()
    programme_type = EnumIntegerField(ProgrammeTypes)
    sector = EnumIntegerField(Sectors)
    start_date = models.DateField()
    end_date = models.DateField()
    budget_amount = models.IntegerField()
    budget_currency = EnumField(Currencies, max_length=4)
    status = EnumIntegerField(Statuses)

    def __str__(self):
        return self.name
