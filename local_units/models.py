from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _

from api.models import Country


class LocalUnitType(models.Model):
    code = models.IntegerField(
        verbose_name=_('Type Code'),
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
        return f'{self.name} ({self.code})'


class LocalUnitLevel(models.Model):
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
    subtype = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Subtype')
    )
    level = models.ForeignKey(
        LocalUnitLevel, on_delete=models.SET_NULL, verbose_name=_('Level'),
        related_name='local_unit_level', null=True
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
        verbose_name=_('Modified at'),
        auto_now=True
    )
    date_of_data = models.DateField(
        verbose_name=_('Date of data collection'),
        auto_now=False,
        blank=True,
        null=True,
    )
    draft = models.BooleanField(default=False, verbose_name=_('Draft'))
    validated = models.BooleanField(default=False, verbose_name=_('Validated'))
    is_public = models.BooleanField(default=False, verbose_name=_('Is public?'))
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
    city_loc = models.CharField(
        max_length=255,
        verbose_name=_('City in local language'),
        null=True,
        blank=True,
    )
    city_en = models.CharField(
        max_length=255,
        verbose_name=_('City in English'),
        null=True,
        blank=True,
    )
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
        max_length=30,
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
    # added to track health local unit type
    data_source_id = models.IntegerField(
        verbose_name=_('Data Source Id'),
        null=True,
        blank=True
    )

    def __str__(self):
        branch_name = self.local_branch_name or self.english_branch_name
        return f'{branch_name} ({self.country.name})'


class DelegationOfficeType(models.Model):
    code = models.IntegerField(
        verbose_name=_('Type Code'),
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
        return f'{self.name} ({self.code})'


class DelegationOffice(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name=_('Name')
    )
    dotype = models.ForeignKey(
        DelegationOfficeType, on_delete=models.SET_NULL, verbose_name=_('Type'),
        related_name='delegation_office_type', null=True
    )
    city = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_('City')
    )
    address = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_('Address')
    )
    postcode = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Postal code')
    )
    location = models.PointField()
    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, verbose_name=_('Country'),
        related_name='delegation_office_country', null=True
    )
    society_url = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('URL of national society')
    )
    url_ifrc = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('URL on IFRC webpage')
    )
    hod_first_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('HOD first name')
    )
    hod_last_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('HOD last name')
    )
    hod_mobile_number = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('HOD mobile number')
    )
    hod_email = models.EmailField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('HOD Email')
    )
    assistant_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Assistant name')
    )
    assistant_email = models.EmailField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Assistant email')
    )
    is_ns_same_location = models.BooleanField(default=False, verbose_name=_('NS on same location?'))
    is_multiple_ifrc_offices = models.BooleanField(default=False, verbose_name=_('Multiple IFRC offices?'))
    is_public = models.BooleanField(default=False, verbose_name=_('Is public?'))
    created_at = models.DateTimeField(
        verbose_name=_('Created at'),
        auto_now=True
    )
    modified_at = models.DateTimeField(
        verbose_name=_('Modified at'),
        auto_now=True
    )
    date_of_data = models.DateField(
        verbose_name=_('Date of data collection'),
        auto_now=False,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f'{self.name} ({self.country.name})'
