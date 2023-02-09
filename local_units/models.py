from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _

from api.models import Country


class LocalUnitType(models.Model):
    level = models.IntegerField(
        verbose_name=_('Level'),
        validators=[
            MaxValueValidator(10),
            MinValueValidator(0)
        ]
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name')
    )

    def __str__(self):
        return f'{self.name} ({self.level})'


class LocalUnit(models.Model):
    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, verbose_name=_('Country'),
        related_name='local_unit_country', null=True
    )
    type = models.ForeignKey(
        LocalUnitType, on_delete=models.SET_NULL, verbose_name=_('Type'),
        related_name='local_unit_type', null=True
    )
    local_branch_name = models.CharField(
        max_length=255,
        verbose_name=_('Branch name in local language')
    )
    english_branch_name = models.CharField(
        max_length=255,
        verbose_name=_('Branch name in English')
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
    source_en = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_('Source in Local Language')
    )
    source_loc = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_('Source in English')
    )
    address_loc = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_('Address in local language')
    )
    address_en = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_('Address in English')
    )
    city_loc = models.CharField(max_length=255, verbose_name=_('City in local language'))
    city_en = models.CharField(max_length=255, verbose_name=_('City in English'))
    focal_person_loc = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Focal person for local language')
    )
    focal_person_en = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Focal person for English')
    )
    postcode = models.CharField(max_length=10, null=True, verbose_name=_('Postal code'))
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Telephone')
    )
    email = models.EmailField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Email')
    )
    link = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Social link')
    )
    location = models.PointField()

    def __str__(self):
        branch_name = self.local_branch_name or self.english_branch_name
        return f'{branch_name} ({self.country.name})'
    