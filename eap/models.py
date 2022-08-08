from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from main.enums import TextChoices
from deployments.models import Sectors
from main.enums import IntegerChoices
from api.models import (
    Country,
    District,
    DisasterType,
)


class EarlyActionIndicator(models.Model):
    class IndicatorChoices(TextChoices):  # TODO these indicator are yet to be provided by client.
        INDICATOR_1 = 'indicator_1', _('Indicator 1')
        INDICATOR_2 = 'indicator_2', _('Indicator 2')

    indicator = models.CharField(
        IndicatorChoices.choices, max_length=255,
        default=IndicatorChoices.INDICATOR_1, null=True, blank=True
    )
    indicator_value = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = _('Early Action Indicator')
        verbose_name_plural = _('Early Actions Indicators')

    def __str__(self):
        return f'{self.indicator}'


class EarlyAction(models.Model):
    class Sector(IntegerChoices):
        SHELTER_HOUSING_AND_SETTLEMENTS = 0, _('Shelter, Housing And Settlements')
        LIVELIHOODS = 1, _('Livelihoods')
        MULTI_PURPOSE_CASH = 2, _('Multi-purpose Cash')
        HEALTH_AND_CARE = 3, _('Health And Care')
        WATER_SANITATION_AND_HYGIENE = 4, _('Water, Sanitation And Hygiene')
        PROTECTION_GENDER_AND_INCLUSION = 5, _('Protection, Gender And Inclusion')
        EDUCATION = 6, _('Education')
        MIGRATION = 7, _('Migration')
        RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY = \
            8, _('Risk Reduction, Climate Adaptation And Recovery')
        COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY = \
            9, _('Community Engagement And Accountability')
        ENVIRONMENT_SUSTAINABILITY = 10, _('Environment Sustainability')
        SHELTER_CLUSTER_COORDINATION = 11, _('Shelter Cluster Coordination')

    sector = models.IntegerField(choices=Sector.choices, verbose_name=_('sector'))
    budget_per_sector = models.IntegerField(verbose_name=_('Budget per sector (CHF)'), null=True, blank=True)
    indicators = models.ManyToManyField(EarlyActionIndicator, verbose_name=_('Indicators'), blank=True)

    prioritized_risk = models.TextField(verbose_name=_('Prioritized risk'), null=True, blank=True)
    targeted_people = models.IntegerField(verbose_name=_('Targeted people'), null=True, blank=True,)

    readiness_activities = models.TextField(verbose_name=_('Readiness Activities'), null=True, blank=True)
    prepositioning_activities = models.TextField(verbose_name=_('Pre-positioning Activities'), null=True, blank=True)

    class Meta:
        verbose_name = _('Early Action')
        verbose_name_plural = _('Early Actions')

    def __str__(self):
        return f'{self.sector}'


class EAP(models.Model):
    class Status(TextChoices):  # TODO some more status choices are to be expected by client.
        APPROVED = 'approved', _('Approved')
        IN_PROCESS = 'in_process', _('In Process')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('Created by'), related_name='eap_created_by',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('Modified by'), related_name='eap_modified_by',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=_('updated at'), auto_now=True)

    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, verbose_name=_('Country'),
        related_name='eap_country', null=True
    )
    district = models.ForeignKey(
        District, on_delete=models.SET_NULL, verbose_name=_('Provience/Region'),
        related_name='eap_district', null=True, blank=True
    )
    disaster_type = models.ForeignKey(
        DisasterType, on_delete=models.SET_NULL, verbose_name=_('Disaster Type'),
        related_name='eap_disaster_type', null=True
    )
    eap_number = models.CharField(max_length=50, verbose_name=_('EAP Number'))
    approval_date = models.DateField(verbose_name=_('Date of EAP Approval'))
    status = models.CharField(
        max_length=255, choices=Status.choices, default=Status.IN_PROCESS,
        verbose_name=_('EAP Status')
    )
    operational_timeframe = models.IntegerField(verbose_name=_('Operational Timeframe (Months)'))
    lead_time = models.IntegerField(verbose_name=_('Lead Time'))
    eap_timeframe = models.IntegerField(verbose_name=_('EAP Timeframe (Years)'))
    num_of_people = models.IntegerField(verbose_name=_('Number of People Targeted'))
    total_budget = models.IntegerField(verbose_name=_('Total Budget (CHF)'))
    readiness_budget = models.IntegerField(verbose_name=_('Readiness Budget (CHF)'), null=True, blank=True)
    pre_positioning_budget = models.IntegerField(verbose_name=_('Pre-positioning Budget (CHF)'), null=True, blank=True)
    early_action_budget = models.IntegerField(verbose_name=_('Early Actions Budget (CHF)'), null=True, blank=True)
    trigger_statement = models.TextField(verbose_name=_('Trigger Statement (Threshold for Activation)'))
    overview = models.TextField(verbose_name=_('EAP Overview'))
    document = models.FileField(
        verbose_name=_('EAP Documents'), upload_to='eap/documents/',
        null=True, blank=True
    )
    early_actions = models.ManyToManyField(
        EarlyAction,
        verbose_name=_('Early actions'),
        blank=True
    )
    originator_name = models.CharField(verbose_name=_('Originator Name'), max_length=255, null=True, blank=True)
    originator_title = models.CharField(verbose_name=_('Originator Title'), max_length=255, null=True, blank=True)
    originator_email = models.CharField(verbose_name=_('Originator Email'), max_length=255, null=True, blank=True)
    originator_phone = models.CharField(verbose_name=_('Origingator Phone'), max_length=255, null=True, blank=True)

    nsc_name = models.CharField(verbose_name=_('National Society Contact Name'), max_length=255, null=True, blank=True)
    nsc_title = models.CharField(verbose_name=_('National Society Contact Title'), max_length=255, null=True, blank=True)
    nsc_email = models.CharField(verbose_name=_('National Society Contact Email'), max_length=255, null=True, blank=True)
    nsc_phone = models.CharField(verbose_name=_('National Society Contact Phone'), max_length=255, null=True, blank=True)

    ifrc_focal_name = models.CharField(verbose_name=_('Ifrc Focal Point Name'), max_length=255, null=True, blank=True)
    ifrc_focal_title = models.CharField(verbose_name=_('Ifrc Focal Point Title'), max_length=255, null=True, blank=True)
    ifrc_focal_email = models.CharField(verbose_name=_('Ifrc Focal Point Email'), max_length=255, null=True, blank=True)
    ifrc_focal_phone = models.CharField(verbose_name=_('Ifrc Focal Point Phone'), max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = _('Early Action Protocol')
        verbose_name_plural = _('Early Actions Protocols')

    def __str__(self):
        return f'{self.eap_number}'


class EAPPartner(models.Model):
    eap = models.ForeignKey(EAP, on_delete=models.CASCADE, related_name='eap_partner', verbose_name=_('EAP'))
    name = models.CharField(max_length=255, verbose_name=_('Name'), null=True, blank=True)
    url = models.URLField(verbose_name=_('URL'), null=True, blank=True)

    class Meta:
        verbose_name = _('EAP Partner')
        verbose_name_plural = _('EAP Partners')

    def __str__(self):
        return f'{self.name}'


class EAPReference(models.Model):
    eap = models.ForeignKey(EAP, on_delete=models.CASCADE, related_name='eap_reference', verbose_name=_('EAP'))
    source = models.CharField(max_length=255, verbose_name=_('Name'), null=True, blank=True)
    url = models.URLField(verbose_name=_('URL'), null=True, blank=True)

    class Meta:
        verbose_name = _('EAP Reference')
        verbose_name_plural = _('EAP References')

    def __str__(self):
        return f'{self.source}'


class Action(models.Model):
    early_action = models.ForeignKey(
        EarlyAction, on_delete=models.CASCADE,
        related_name="action", verbose_name=_('Early Actions')
    )
    early_act = models.TextField(verbose_name=_('Early Actions'), null=True, blank=True)

    class Meta:
        verbose_name = _('Action')
        verbose_name_plural = _('Actions')

    def __str__(self):
        return f'{self.id}'
