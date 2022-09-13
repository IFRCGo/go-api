from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from main.enums import TextChoices, IntegerChoices
from api.models import (
    Country,
    District,
    DisasterType,
    FieldReport,
)


class EarlyActionIndicator(models.Model):
    class IndicatorChoices(TextChoices):  # TODO these indicator are yet to be provided by client.
        INDICATOR_1 = 'indicator_1', _('Indicator 1')
        INDICATOR_2 = 'indicator_2', _('Indicator 2')

    indicator = models.CharField(
        max_length=255, choices=IndicatorChoices.choices,
        default=IndicatorChoices.INDICATOR_1, null=True, blank=True
    )
    indicator_value = models.IntegerField(null=True, blank=True)
    client_id = models.CharField(max_length=50, null=True, blank=True)

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
    targeted_people = models.IntegerField(verbose_name=_('Targeted people'), null=True, blank=True,)
    readiness_activities = models.TextField(verbose_name=_('Readiness Activities'), null=True, blank=True)
    prepositioning_activities = models.TextField(verbose_name=_('Pre-positioning Activities'), null=True, blank=True)
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _('Early Action')
        verbose_name_plural = _('Early Actions')

    def __str__(self):
        return f'{self.sector}'


class EAPDocument(models.Model):
    file = models.FileField(null=True, blank=True)
    caption = models.CharField(max_length=225, null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('Created by'), related_name='document_created_by',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')

    def __str__(self):
        return str(self.id)


class EAP(models.Model):
    class Status(TextChoices):
        APPROVED = 'approved', _('Approved')
        ACTIVATED = 'activated', _('Activated')

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
    districts = models.ManyToManyField(
        District, verbose_name=_('districts'),
        related_name='eap_district'
    )
    disaster_type = models.ForeignKey(
        DisasterType, on_delete=models.SET_NULL, verbose_name=_('Disaster Type'),
        related_name='eap_disaster_type', null=True
    )
    eap_number = models.CharField(max_length=50, verbose_name=_('EAP Number'))
    approval_date = models.DateField(verbose_name=_('Date of EAP Approval'))
    status = models.CharField(
        max_length=255, choices=Status.choices, default=Status.APPROVED,
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
    documents = models.ManyToManyField(
        EAPDocument,
        verbose_name=_('EAP Documents'),
        related_name='eap_document',
        blank=True
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
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _('EAP Partner')
        verbose_name_plural = _('EAP Partners')

    def __str__(self):
        return f'{self.name}'


class EAPReference(models.Model):
    eap = models.ForeignKey(EAP, on_delete=models.CASCADE, related_name='eap_reference', verbose_name=_('EAP'))
    source = models.CharField(max_length=255, verbose_name=_('Name'), null=True, blank=True)
    url = models.URLField(verbose_name=_('URL'), null=True, blank=True)
    client_id = models.CharField(max_length=50, null=True, blank=True)

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
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _('Action')
        verbose_name_plural = _('Actions')

    def __str__(self):
        return f'{self.id}'


class PrioritizedRisk(models.Model):
    early_action = models.ForeignKey(
        EarlyAction,
        on_delete=models.CASCADE,
        related_name='early_actions_prioritized_risk',
        verbose_name=_('early action')
    )
    risks = models.TextField(null=True, blank=True)
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _('Prioritized risk')
        verbose_name_plural = _('Prioritized risks')

    def __str__(self):
        return f'{self.id}'


class EAPActivation(models.Model):
    title = models.CharField(max_length=250, null=True, blank=True)
    field_report = models.ForeignKey(
        FieldReport,
        on_delete=models.SET_NULL,
        related_name='field_report_eap_activation',
        verbose_name=_('field report'),
        null=True, blank=True
    )
    eap = models.ForeignKey(
        EAP,
        on_delete=models.SET_NULL,
        related_name='eap_activation',
        verbose_name=_('eap'),
        null=True, blank=True
    )
    trigger_met_date = models.DateTimeField(verbose_name=_('Date the trigger was met'))
    description = models.TextField(verbose_name=_('Description of EAP Activation'))
    documents = models.ManyToManyField(
        EAPDocument,
        verbose_name=_('EAP Activation Documents'),
        related_name='eap_activation_document',
        blank=True
    )
    originator_name = models.CharField(max_length=250, verbose_name=_('Originator name'), null=True, blank=True)
    originator_title = models.CharField(max_length=250, verbose_name=_('Originator title'), null=True, blank=True)
    originator_email = models.CharField(max_length=250, verbose_name=_('Originator email'), null=True, blank=True)
    nsc_name_operational = models.CharField(max_length=250, verbose_name=_('National Society Contact (Operational)'), null=True, blank=True)
    nsc_title_operational = models.CharField(max_length=250, verbose_name=_('National Society Contact (Operational)'), null=True, blank=True)
    nsc_email_operational = models.CharField(max_length=250, verbose_name=_('National Society Contact (Operational)'), null=True, blank=True)
    nsc_name_secretary = models.CharField(max_length=250, verbose_name=_('National Society Contact (Secretary)'), null=True, blank=True)
    nsc_title_secretary = models.CharField(max_length=250, verbose_name=_('National Society Contact (Secretary)'), null=True, blank=True)
    nsc_email_secretary = models.CharField(max_length=250, verbose_name=_('National Society Contact (Secretary)'), null=True, blank=True)
    ifrc_focal_name = models.CharField(max_length=250, verbose_name=_('IFRC Focal Point Name'), null=True, blank=True)
    ifrc_focal_title = models.CharField(max_length=250, verbose_name=_('IFRC Focal Point Title'), null=True, blank=True)
    ifrc_focal_email = models.CharField(max_length=250, verbose_name=_('IFRC Focal Point Email'), null=True, blank=True)

    def __str__(self):
        return f'{self.eap.eap_number}'


class EAPOperationalPlan(models.Model):
    early_action = models.OneToOneField(
        EarlyAction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    budget = models.IntegerField(verbose_name=_('Budget per sector (CHF)'), null=True, blank=True)
    value = models.IntegerField(verbose_name=_('value'), null=True, blank=True)
    no_of_people_reached = models.IntegerField(verbose_name=_('People Reached'), null=True, blank=True)
    readiness_activities_achievements = models.TextField(verbose_name=_('Readiness Activities Achievements'), null=True, blank=True)
    prepo_activities_achievements = models.TextField(verbose_name=_('Pre-positioning Activities Achievements'), null=True, blank=True)
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _('EAP Operational Plan')
        verbose_name_plural = _('EAP Operational Plans')

    def __str__(self):
        return f'{self.id}'


class OperationalPlanIndicator(models.Model):
    operational_plan = models.ForeignKey(
        EAPOperationalPlan, on_delete=models.SET_NULL,
        related_name="operational_plan_indicator", verbose_name=_('Operational Plan'),
        null=True, blank=True
    )
    indicator = models.ForeignKey(
        EarlyActionIndicator,
        on_delete=models.SET_NULL,
        related_name='operational_plan_indicator',
        null=True,
        blank=True
    )
    indicator_value = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = _('Operational Indicator')
        verbose_name_plural = _('Operational Indicators')

    def __str__(self):
        return f'{self.indicator.id}'


class ActionAchievement(models.Model):
    operational_plan = models.ForeignKey(
        EAPOperationalPlan, on_delete=models.SET_NULL,
        related_name="action_achievement", verbose_name=_('Action Achievement'),
        null=True, blank=True
    )
    action = models.ForeignKey(
        Action,
        on_delete=models.SET_NULL,
        related_name='action_achievement',
        null=True, blank=True
    )
    early_act_achievement = models.TextField(verbose_name=_('Early Actions Achievements'), null=True, blank=True)
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _('Action Achievement')
        verbose_name_plural = _('Action Achievements')

    def __str__(self):
        return f'{self.id}'


class EAPActivationReport(models.Model):
    eap_activation = models.ForeignKey(
        EAPActivation,
        on_delete=models.SET_NULL,
        verbose_name=_('EAP Activation Report'),
        related_name='eap_activation_report',
        null=True, blank=True
    )
    number_of_people_reached = models.IntegerField(verbose_name=_('Number Of People Reached'))
    description = models.TextField(verbose_name=_('Description of Event & Overview of Implementation'))
    overall_objectives = models.TextField(verbose_name=_('Overall Objective of the Intervention'))
    documents = models.ManyToManyField(
        EAPDocument,
        verbose_name=_('EAP Activation Report Document'),
        related_name='eap_act_reports',
        blank=True
    )
    challenges_and_lesson = models.TextField(verbose_name=_('Challenges & Lesson Learned per Sector'))
    general_lesson_and_recomendations = models.TextField(verbose_name=_('General Lessons Learned and Recomendations'))
    ifrc_financial_report = models.ForeignKey(
        EAPDocument,
        on_delete=models.SET_NULL,
        verbose_name=_('IFRC Financial Report'),
        related_name='eap_activation_ifrc_report',
        null=True, blank=True
    )
    operational_plans = models.ManyToManyField(
        EAPOperationalPlan,
        verbose_name=_('Operational Plans'),
        blank=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('Created by'), related_name='eap_act_report_created_by',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('Modified by'), related_name='eap_act_modified_by',
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(verbose_name=_('Created at'), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=_('Updated at'), auto_now=True)

    def __str__(self):
        return f'{self.eap_activation.title}'
