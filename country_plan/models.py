from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from api.models import Country


def file_upload_to(instance, filename):
    date_str = timezone.now().strftime('%Y-%m-%d-%H-%M-%S')
    return f'country-plan-exel-files/{date_str}/{filename}'


def pdf_upload_to(instance, filename):
    date_str = timezone.now().strftime('%Y-%m-%d-%H-%M-%S')
    return f'country-plan-pdf/{date_str}/{filename}'


class CountryPlanBase(models.Model):
    created_by = models.ForeignKey(
        User,
        verbose_name=_('Created By'),
        blank=True,
        null=True,
        related_name='data_import_created_by',
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(verbose_name=_('Created at'), auto_now_add=True)
    updated_by = models.ForeignKey(
        User,
        verbose_name=_('Updated by'),
        blank=True,
        null=True,
        related_name='data_import_updated_by',
        on_delete=models.SET_NULL
    )
    updated_at = models.DateTimeField(verbose_name=_('Updated at'), auto_now=True)


class DataImport(CountryPlanBase):
    file = models.FileField(verbose_name=_('EXEL file'), upload_to=file_upload_to)

    def __str__(self):
        return self.file.name


class CountryPlan(CountryPlanBase):
    internal_plan_file = models.FileField(verbose_name=_('Internal Plan'), upload_to=pdf_upload_to)
    public_plan_file = models.FileField(verbose_name=_('Country Plan'), upload_to=pdf_upload_to)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    requested_amount = models.IntegerField(verbose_name=_('Requested Amount'), blank=True, null=True)
    people_targeted = models.IntegerField(verbose_name=_('People Targeted'), blank=True, null=True)
    situation_analysis = models.TextField(blank=True, verbose_name=_('Situation Analysis'))
    role_of_national_society = models.TextField(blank=True, verbose_name=_('Role of National Society'))
    is_publish = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.country}'


class StrategicPriority(models.Model):
    class StrategicPriorityName(models.TextChoices):
        SP_1 = 'sp_1', _('Climate and environmental crisis')
        SP_2 = 'sp_2', _('Evolving crisis and disasters')
        SP_3 = 'sp_3', _('Growing gaps in health and wellbeing')
        SP_4 = 'sp_4', _('Migration and Identity')
        SP_5 = 'sp_5', _('Value power and inclusion')

    country_plan = models.ForeignKey(
        CountryPlan, on_delete=models.CASCADE,
        verbose_name=_('Country Plan'),
        related_name='country_plan_sp'
    )
    sp_name = models.CharField(
        max_length=100, choices=StrategicPriorityName.choices,
        null=True, blank=True, verbose_name=_('share with')
    )
    funding_requirement = models.IntegerField(verbose_name=_('Funding Requirement'), blank=True, null=True)
    people_targeted = models.IntegerField(verbose_name=_('People Targeted'), blank=True, null=True)

    def __str__(self):
        return f'{self.country_plan.iso3}'


class MembershipCoordination(models.Model):
    class MembershipCoordinationChoices(models.TextChoices):
        SP_1 = 'sp_1', _('SP1')
        SP_2 = 'sp_2', _('SP2')
        SP_3 = 'sp_3', _('SP3')
        SP_4 = 'sp_4', _('SP4')
        SP_5 = 'sp_5', _('SP5')
        EA_1 = 'ea_1', _('EA1')
        EA_2 = 'ea_2', _('EA2')
        EA_3 = 'ea_3', _('EA3')

    country_plan = models.ForeignKey(CountryPlan, on_delete=models.SET_NULL, null=True, blank=True)
    national_society = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    strategic_priority = models.CharField(
        max_length=100, choices=MembershipCoordinationChoices.choices,
        null=True, blank=True, verbose_name=_('share with')
    )
    has_coordination = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.national_society.iso3}-{self.strategic_priority}'
