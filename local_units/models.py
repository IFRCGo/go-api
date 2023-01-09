from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _

from api.models import Country


class LocalUnit(models.Model):
    unique_id = models.CharField(max_length=6, verbose_name=_('Unique ID'))
    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, verbose_name=_('Country'),
        related_name='local_unit_country', null=True
    )
    national_society_name = models.CharField(
        max_length=255,
        verbose_name=_('National Society Name')
    )
    local_branch_name = models.CharField(
        max_length=255,
        verbose_name=_('Branch name in local language')
    )
    english_branch_name = models.CharField(
        max_length=255,
        verbose_name=_('Branch name in English')
    )
    branch_level = models.IntegerField(
        verbose_name=_('Branch Level'),
        validators=[
            MaxValueValidator(10),
            MinValueValidator(1)
        ]
    )
    branch_type_name = models.CharField(
        max_length=100,
        verbose_name=_('Branch type name')
    )
    created_at = models.DateTimeField(
        verbose_name=_('Created at'),
        auto_now=True
    )
    modified_at = models.DateTimeField(
        verbose_name=_('Updated at'),
        auto_now=True
    )
    draft = models.BooleanField(default=False, verbose_name=_('Draft'))
    validated = models.BooleanField(default=True, verbose_name=_('Validated'))
    source = models.CharField(max_length=255, verbose_name=_('Source'))
    address_loc = models.CharField(max_length=500, verbose_name=_('Address in local language'))
    address_en = models.CharField(max_length=500, verbose_name=_('Address in English'))
    city_loc = models.CharField(max_length=255, verbose_name=_('City in local language'))
    city_en = models.CharField(max_length=255, verbose_name=_('City in English'))
    focal_person_loc = models.CharField(max_length=255, verbose_name=_('Focal person for local language'))
    focal_person_en = models.CharField(max_length=255, verbose_name=_('Focal person for English'))
    postcode = models.CharField(max_length=10, verbose_name=_('Postal code'))
    phone = models.CharField(max_length=20, verbose_name=_('Telephone'))
    link = models.CharField(max_length=255, verbose_name=_('Social link'))
    location = models.PointField()
