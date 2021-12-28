import os

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.templatetags.static import static
from django.http import request

from enumfields import IntEnum, EnumIntegerField

from api.models import (
    Country,
    DisasterType,
    District,
    FieldReport
)
from api.storage import get_storage
from .enums import TextChoices


def dref_document_path(instance, filename):
    return f'dref/event/{filename}'


def image_path(instance, filename):
    return f'dref-images/{filename}'


class NationalSocietyAction(models.Model):
    # NOTE: Replace `TextChoices` to `models.TextChoices` after upgrade to Django version 3
    class Title(TextChoices):
        NATIONAL_SOCIETY_READINESS = 'national_society_readiness', _('National Society Readiness')
        ASSESSMENT = 'assessment', _('Assessment')
        COORDINATION = 'coordination', _('Coordination')
        RESOURCE_MOBILIZATION = 'resource_mobilization', _('Resource Mobilization')
        ACTIVATION_OF_CONTINGENCY_PLANS = 'activation_of_contingency_plans', _('Activation Of Contingency Plans')
        NATIONAL_SOCIETY_EOC = 'national_society_eoc', _('National Society EOC')
        SHELTER_AND_BASIC_HOUSEHOLD_ITEMS = 'shelter_and_basic_household_items', _('Shelter And Basic Household Items')
        LIVELIHOODS_AND_BASIC_NEEDS = 'livelihoods_and_basic_needs', _('Livelihoods And Basic Needs')
        HEALTH = 'health', _('Health')
        WATER_SANITATION_AND_HYGIENE = 'water_sanitation_and_hygiene', _('Water, Sanitation And Hygiene')
        PROTECTION_GENDER_AND_INCULSION = 'protection_gender_and_inculsion', _('Protection, Gender And Inculsion')
        EDUCATION = 'education', _('Education')
        MIGRATION = 'migration', _('Migration')
        RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY = \
            'risk_reduction_climate_adaptation_and_recovery', _('Risk Reduction, Climate Adaptation And Recovery')
        COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY = \
            'community_engagement_and _accountability', _('Community Engagement And Accountability')
        ENVIRONMENT_SUSTAINABILITY = 'environment_sustainability ', _('Environment Sustainability')
        OTHER = 'other', _('Other')

    title = models.CharField(max_length=255, verbose_name=_('title'), choices=Title.choices)
    image_url = models.CharField(max_length=255, verbose_name=_('image_url'), null=True, blank=True)
    description = models.TextField(verbose_name=_('description'), blank=True, null=True)

    class Meta:
        verbose_name = _('national society action')
        verbose_name_plural = _('national society actions')

    @staticmethod
    def get_image_map(title, request):
        title_static_map = {
            NationalSocietyAction.Title.SHELTER_AND_BASIC_HOUSEHOLD_ITEMS: 'shelter.png',
            NationalSocietyAction.Title.LIVELIHOODS_AND_BASIC_NEEDS: 'livelihood.png',
            NationalSocietyAction.Title.HEALTH: 'health.png',
            NationalSocietyAction.Title.WATER_SANITATION_AND_HYGIENE: 'water.png',
            NationalSocietyAction.Title.PROTECTION_GENDER_AND_INCULSION: 'protection.png',
            NationalSocietyAction.Title.EDUCATION: 'education.png',
            NationalSocietyAction.Title.MIGRATION: 'migration.png',
            NationalSocietyAction.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY: 'risk.png',
            NationalSocietyAction.Title.ENVIRONMENT_SUSTAINABILITY: 'environment.png',
            NationalSocietyAction.Title.NATIONAL_SOCIETY_READINESS: 'favicon.png',
            NationalSocietyAction.Title.ASSESSMENT: 'favicon.png',
            NationalSocietyAction.Title.COORDINATION: 'favicon.png',
            NationalSocietyAction.Title.RESOURCE_MOBILIZATION: 'favicon.png',
            NationalSocietyAction.Title.ACTIVATION_OF_CONTINGENCY_PLANS: 'favicon.png',
            NationalSocietyAction.Title.NATIONAL_SOCIETY_EOC: 'favicon.png',
            NationalSocietyAction.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY: 'favicon.png',
            NationalSocietyAction.Title.OTHER: 'favicon.png',
        }
        return request.build_absolute_uri(static(os.path.join('images/dref', title_static_map[title])))


class IdentifiedNeed(models.Model):
    class Title(TextChoices):
        SHELTER_AND_BASIC_HOUSEHOLD_ITEMS = 'shelter_and_basic_household_items', _('Shelter And Basic Household Items')
        LIVELIHOODS_AND_BASIC_NEEDS = 'livelihoods_and_basic_needs', _('Livelihoods And Basic Needs')
        HEALTH = 'health', _('Health')
        WATER_SANITATION_AND_HYGIENE = 'water_sanitation_and_hygiene', _('Water, Sanitation And Hygiene')
        PROTECTION_GENDER_AND_INCULSION = 'protection_gender_and_inculsion', _('Protection, Gender And Inculsion')
        EDUCATION = 'education', _('Education')
        MIGRATION = 'migration', _('Migration')
        RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY = \
            'risk_reduction_climate_adaptation_and_recovery', _('Risk Reduction, Climate Adaptation And Recovery')
        COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY = \
            'community_engagement_and _accountability', _('Community Engagement And Accountability')
        ENVIRONMENT_SUSTAINABILITY = 'environment_sustainability ', _('Environment Sustainability')
        SHELTER_CLUSTER_COORDINATION = ('shelter_cluster_coordination'), _('Shelter Cluster Coordination')

    title = models.CharField(max_length=255, verbose_name=_('title'), choices=Title.choices)
    image_url = models.CharField(max_length=255, verbose_name=_('image_url'), null=True, blank=True)
    description = models.TextField(verbose_name=_('description'), blank=True, null=True)

    class Meta:
        verbose_name = _('identified need')
        verbose_name_plural = _('identified needs')

    @staticmethod
    def get_image_map(title, request):
        title_static_map = {
            IdentifiedNeed.Title.SHELTER_AND_BASIC_HOUSEHOLD_ITEMS: 'shelter.png',
            IdentifiedNeed.Title.LIVELIHOODS_AND_BASIC_NEEDS: 'livelihood.png',
            IdentifiedNeed.Title.HEALTH: 'health.png',
            IdentifiedNeed.Title.WATER_SANITATION_AND_HYGIENE: 'water.png',
            IdentifiedNeed.Title.PROTECTION_GENDER_AND_INCULSION: 'protection.png',
            IdentifiedNeed.Title.EDUCATION: 'education.png',
            IdentifiedNeed.Title.MIGRATION: 'migration.png',
            IdentifiedNeed.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY: 'risk.png',
            IdentifiedNeed.Title.ENVIRONMENT_SUSTAINABILITY: 'environment.png',
            IdentifiedNeed.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY: 'favicon.png',
            IdentifiedNeed.Title.SHELTER_CLUSTER_COORDINATION: 'favicon.png'
        }
        return request.build_absolute_uri(static(os.path.join('images/dref', title_static_map[title])))


class PlannedIntervention(models.Model):
    class Title(TextChoices):
        SHELTER_AND_BASIC_HOUSEHOLD_ITEMS = 'shelter_and_basic_household_items', _('Shelter And Basic Household Items')
        LIVELIHOODS_AND_BASIC_NEEDS = 'livelihoods_and_basic_needs', _('Livelihoods And Basic Needs')
        HEALTH = 'health', _('Health')
        WATER_SANITATION_AND_HYGIENE = 'water_sanitation_and_hygiene', _('Water, Sanitation And Hygiene')
        PROTECTION_GENDER_AND_INCULSION = 'protection_gender_and_inculsion', _('Protection, Gender And Inculsion')
        EDUCATION = 'education', _('Education')
        MIGRATION = 'migration', _('Migration')
        RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY = \
            'risk_reduction_climate_adaptation_and_recovery_', _('Risk Reduction, Climate Adaptation And Recovery')
        SECRETARIAT_SERVICES = 'secretariat_services', _('Secretariat Services')
        NATIONAL_SOCIETY_STRENGTHENING = 'national_society_strengthening', _('National Society Strengthening')

    title = models.CharField(max_length=255, verbose_name=_('title'), choices=Title.choices)
    description = models.TextField(verbose_name=_('description'), blank=True, null=True)
    budget = models.IntegerField(verbose_name=_('budget'), blank=True, null=True)
    person_targeted = models.IntegerField(verbose_name=_('person targeted'), blank=True, null=True)
    indicator = models.TextField(verbose_name=_('indicator'), blank=True, null=True)
    image_url = models.CharField(max_length=255, verbose_name=_('image_url'), null=True, blank=True)

    class Meta:
        verbose_name = _('planned intervention')
        verbose_name_plural = _('planned interventions')

    @staticmethod
    def get_image_map(title, request):
        title_static_map = {
            PlannedIntervention.Title.SHELTER_AND_BASIC_HOUSEHOLD_ITEMS: 'shelter.png',
            PlannedIntervention.Title.LIVELIHOODS_AND_BASIC_NEEDS: 'livelihood.png',
            PlannedIntervention.Title.HEALTH: 'health.png',
            PlannedIntervention.Title.WATER_SANITATION_AND_HYGIENE: 'water.png',
            PlannedIntervention.Title.PROTECTION_GENDER_AND_INCULSION: 'protection.png',
            PlannedIntervention.Title.EDUCATION: 'education.png',
            PlannedIntervention.Title.MIGRATION: 'migration.png',
            PlannedIntervention.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY: 'risk.png',
            PlannedIntervention.Title.SECRETARIAT_SERVICES: 'favicon.png',
            PlannedIntervention.Title.NATIONAL_SOCIETY_STRENGTHENING: 'favicon.png',
        }
        return request.build_absolute_uri(static(os.path.join('images/dref', title_static_map[title])))


class Dref(models.Model):

    class OnsetType(IntEnum):
        IMMINENT = 0
        SLOW = 1
        SUDDEN = 2

        class Labels:
            IMMINENT = _('Imminent')
            SLOW = _('Slow')
            SUDDEN = _('Sudden')

    class DisasterCategory(IntEnum):
        YELLOW = 0
        ORANGE = 1
        RED = 2

        class Labels:
            YELLOW = _('Yellow')
            ORANGE = _('Orange')
            RED = _('Red')

    class Status(IntEnum):
        IN_PROGESS = 0
        COMPLETED = 1

        class Labels:
            IN_PROGESS = _('In Progress')
            COMPLETED = _('Completed')

    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=_('modified at'), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('created by'), on_delete=models.SET_NULL,
        null=True, related_name='created_by_dref'
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('modified by'), on_delete=models.SET_NULL,
        null=True, related_name='modified_by_dref'
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, verbose_name=_('users'),
        blank=True, related_name='user_dref'
    )
    field_report = models.ForeignKey(
        FieldReport, verbose_name=_('field report'),
        on_delete=models.SET_NULL, null=True,
        related_name='field_report_dref'
    )
    title = models.CharField(verbose_name=_('title'), max_length=255)
    national_society = models.ForeignKey(
        Country, verbose_name=_('national_society'),
        on_delete=models.CASCADE,
    )
    disaster_type = models.ForeignKey(
        DisasterType, verbose_name=_('disaster type'),
        blank=True, null=True,
        on_delete=models.SET_NULL
    )
    type_of_onset = EnumIntegerField(OnsetType, verbose_name=_('onset type'), null=True, blank=True)
    disaster_category = EnumIntegerField(DisasterCategory, verbose_name=_('disaster category'), null=True, blank=True)
    status = EnumIntegerField(Status, verbose_name=_('status'), null=True, blank=True)
    num_assisted = models.IntegerField(verbose_name=_('number of assisted'), blank=True, null=True)
    num_affected = models.IntegerField(verbose_name=_('number of affected'), blank=True, null=True)
    amount_requested = models.IntegerField(verbose_name=_('amount requested'), blank=True, null=True)
    emergency_appeal_planned = models.BooleanField(
        verbose_name=_('emergency appeal planned '),
        null=True, blank=True
    )
    event_date = models.DateField(
        verbose_name=_('event date'),
        null=True, blank=True,
        help_text=_('Date of event/Approximate date of impact')
    )
    event_text = models.TextField(verbose_name=_('event text'), blank=True, null=True)
    ns_respond_date = models.DateField(
        verbose_name=_('ns respond date'),
        null=True, blank=True,
        help_text=_('NS anticipatory actions started/NS response')
    )
    affect_same_area = models.BooleanField(
        null=True, blank=True,
        help_text=_('Has a similar event affected the same areas in the past?')
    )
    affect_same_population = models.BooleanField(
        null=True, blank=True,
        help_text=_('Did it affect the same population?')
    )
    affect_same_population_text = models.TextField(
        blank=True, null=True,
        verbose_name=_('affect same population text')
    )
    ns_respond = models.BooleanField(
        null=True, blank=True,
        default=False, help_text=_('Did NS respond')
    )
    ns_request_fund = models.BooleanField(
        null=True, blank=True,
        default=False, help_text=_('Did the NS request funding from DREF?')
    )
    ns_request_text = models.TextField(
        blank=True, null=True,
        verbose_name=_('ns request text')
    )
    dref_recurrent_text = models.TextField(verbose_name=_('dref recurrent text'), blank=True, null=True)
    lessons_learned = models.TextField(verbose_name=_('lessons learned'), blank=True, null=True)
    event_description = models.TextField(verbose_name=_('event description'), blank=True, null=True)
    anticipatory_actions = models.TextField(
        blank=True, null=True,
        verbose_name=_('anaticipatory actions'),
        help_text=_('Description of anticipatory actions or imminent disaster')
    )
    event_scope = models.TextField(
        blank=True, null=True,
        verbose_name=_('event scope'),
        help_text=_('Scope and scale of event')
    )
    national_society_actions = models.ManyToManyField(
        NationalSocietyAction, verbose_name=_('national society actions'),
        blank=True
    )
    government_requested_assistance = models.BooleanField(
        null=True, blank=True,
        help_text=_('Has government requested assistance')
    )
    government_requested_assistance_date = models.DateField(
        verbose_name=_('government requested assistance date'),
        null=True, blank=True
    )
    national_authorities = models.TextField(verbose_name=_('national authorities'), blank=True, null=True)
    ifrc = models.TextField(verbose_name=_('ifrc'), blank=True, null=True)
    icrc = models.TextField(verbose_name=_('icrc'), blank=True, null=True)
    partner_national_society = models.TextField(verbose_name=_('partner national society'), blank=True, null=True)
    un_or_other_actor = models.TextField(verbose_name=_('un or other'), blank=True, null=True)
    major_coordination_mechanism = models.TextField(
        blank=True, null=True,
        verbose_name=_('major coordination mechanism'),
        help_text=_('List major coordination mechanisms in place')
    )
    needs_identified = models.ManyToManyField(
        IdentifiedNeed, verbose_name=_('needs identified'),
        blank=True
    )
    identified_gaps = models.TextField(
        verbose_name=_('identified gaps'), blank=True, null=True,
        help_text=_('Any identified gaps/limitations in the assessment')
    )
    people_assisted = models.TextField(verbose_name=_('people assisted'), blank=True, null=True)
    selection_criteria = models.TextField(
        verbose_name=_('selection criteria'), blank=True, null=True,
        help_text=_('Selection criteria for affected people')
    )
    entity_affected = models.TextField(
        verbose_name=_('entity affected'), blank=True, null=True,
        help_text=_('Protection, gender, Inclusion affected in this process')
    )
    community_involved = models.TextField(
        verbose_name=_('community involved'), blank=True, null=True,
        help_text=_('Community been involved in the analysis of the process')
    )
    women = models.IntegerField(verbose_name=_('women'), blank=True, null=True)
    men = models.IntegerField(verbose_name=_('men'), blank=True, null=True)
    girls = models.IntegerField(
        verbose_name=_('girls'), help_text=_('Girls under 18'),
        blank=True, null=True
    )
    boys = models.IntegerField(
        verbose_name=_('boys'), help_text=_('Boys under 18'),
        blank=True, null=True
    )
    total_targated_population = models.IntegerField(
        verbose_name=_('total targated population'), help_text=_('Estimated number of targated people'),
        blank=True, null=True
    )
    disability_people_per = models.DecimalField(
        verbose_name=_('disability people per'), help_text=_('Estimated % people disability'),
        blank=True, null=True,
        max_digits=5, decimal_places=2
    )
    people_per_urban = models.DecimalField(
        verbose_name=_('people per urban'), help_text=_('Estimated % people Urban'),
        blank=True, null=True,
        max_digits=5, decimal_places=2
    )
    people_per_local = models.DecimalField(
        verbose_name=_('people per local'), help_text=_('Estimated % people Rural'),
        blank=True, null=True,
        max_digits=5, decimal_places=2
    )
    people_targeted_with_early_actions = models.IntegerField(
        verbose_name=_('people targeted with early actions'),
        help_text=_('Number of persons targeted with early actions'),
        blank=True, null=True
    )
    displaced_people = models.IntegerField(
        verbose_name=_('displaced people'), help_text=_('Estimated number of displaced people'),
        blank=True, null=True
    )
    operation_objective = models.TextField(
        verbose_name=_('operation objective'), help_text=_('Overall objective of the operation'),
        blank=True, null=True,
    )
    response_strategy = models.TextField(
        verbose_name=_('response strategy'),
        blank=True, null=True,
    )
    planned_interventions = models.ManyToManyField(
        PlannedIntervention,
        verbose_name=_('planned intervention'), blank=True
    )
    go_field_report_date = models.DateField(verbose_name=_('go field report date'), null=True, blank=True)
    ns_request_date = models.DateField(verbose_name=_('ns request date'), null=True, blank=True)
    submission_to_geneva = models.DateField(verbose_name=_('submission to geneva'), null=True, blank=True)
    date_of_approval = models.DateField(verbose_name=_('date of approval'), null=True, blank=True)
    end_date = models.DateField(verbose_name=_('end date'), null=True, blank=True)
    publishing_date = models.DateField(verbose_name=_('publishing date'), null=True, blank=True)
    operation_timeframe = models.IntegerField(verbose_name=_('operation timeframe'), null=True, blank=True)
    appeal_code = models.CharField(verbose_name=_('appeal code'), max_length=255, null=True, blank=True)
    glide_code = models.CharField(verbose_name=_('glide number'), max_length=255, null=True, blank=True)
    ifrc_appeal_manager_name = models.CharField(
        verbose_name=_('ifrc appeal manager name'), max_length=255,
        null=True, blank=True
    )
    ifrc_appeal_manager_email = models.CharField(
        verbose_name=_('ifrc appeal manager email'), max_length=255,
        null=True, blank=True
    )
    ifrc_appeal_manager_title = models.CharField(
        verbose_name=_('ifrc appeal manager title'), max_length=255,
        null=True, blank=True
    )
    ifrc_appeal_manager_phone_number = models.CharField(
        verbose_name=_('ifrc appeal manager phone number'), max_length=100,
        null=True, blank=True
    )
    ifrc_project_manager_name = models.CharField(
        verbose_name=_('ifrc project manager name'), max_length=255,
        null=True, blank=True
    )
    ifrc_project_manager_email = models.CharField(
        verbose_name=_('ifrc project manager email'), max_length=255,
        null=True, blank=True
    )
    ifrc_project_manager_title = models.CharField(
        verbose_name=_('ifrc project manager title'), max_length=255,
        null=True, blank=True
    )
    ifrc_project_manager_phone_number = models.CharField(
        verbose_name=_('ifrc project manager phone number'), max_length=100,
        null=True, blank=True
    )
    national_society_contact_name = models.CharField(
        verbose_name=_('national society contact name'), max_length=255,
        null=True, blank=True
    )
    national_society_contact_email = models.CharField(
        verbose_name=_('national society contact email'), max_length=255,
        null=True, blank=True
    )
    national_society_contact_title = models.CharField(
        verbose_name=_('national society contact title'), max_length=255,
        null=True, blank=True
    )
    national_society_contact_phone_number = models.CharField(
        verbose_name=_('national society contact phone number'), max_length=100,
        null=True, blank=True
    )
    media_contact_name = models.CharField(
        verbose_name=_('media contact name'), max_length=255,
        null=True, blank=True
    )
    media_contact_email = models.CharField(
        verbose_name=_('media contact email'), max_length=255,
        null=True, blank=True
    )
    media_contact_title = models.CharField(
        verbose_name=_('media contact title'), max_length=255,
        null=True, blank=True
    )
    media_contact_phone_number = models.CharField(
        verbose_name=_('media_contact phone number'), max_length=100,
        null=True, blank=True
    )
    ifrc_emergency_name = models.CharField(
        verbose_name=_('ifrc emergency name'), max_length=255,
        null=True, blank=True
    )
    ifrc_emergency_email = models.CharField(
        verbose_name=_('ifrc emergency email'), max_length=255,
        null=True, blank=True
    )
    ifrc_emergency_title = models.CharField(
        verbose_name=_('ifrc emergency title'), max_length=255,
        null=True, blank=True
    )
    ifrc_emergency_phone_number = models.CharField(
        verbose_name=_('ifrc emergency phone number'), max_length=100,
        null=True, blank=True
    )
    originator_name = models.CharField(
        verbose_name=_('originator name'), max_length=255,
        null=True, blank=True
    )
    originator_email = models.CharField(
        verbose_name=_('originator email'), max_length=255,
        null=True, blank=True
    )
    originator_title = models.CharField(
        verbose_name=_('originator title'), max_length=255,
        null=True, blank=True
    )
    originator_phone_number = models.CharField(
        verbose_name=_('originator phone number'), max_length=100,
        null=True, blank=True
    )
    human_resource = models.TextField(
        blank=True, null=True,
        verbose_name=_('human resource'),
        help_text=_('how many volunteers and staff involved in the response?')
    )
    surge_personnel_deployed = models.TextField(
        blank=True, null=True,
        verbose_name=_('surge personnel deployed'),
        help_text=_('Will a Surge personnel be deployed?')
    )
    logistic_capacity_of_ns = models.TextField(
        blank=True, null=True,
        verbose_name=_('logistic capacity of ns'),
        help_text=_('what is the logistics capacity of the National Society?')
    )
    safety_concerns = models.TextField(
        blank=True, null=True,
        verbose_name=_('safety concerns'),
        help_text=_('Are there any safety/security concerns which may impact the implementation of this operation?')
    )
    pmer = models.TextField(
        blank=True, null=True,
        verbose_name=_('pmer'),
        help_text=_('Does the NS have PMER capacity?')
    )
    communication = models.TextField(
        blank=True, null=True,
        verbose_name=_('organization'),
        help_text=_('Does the NS have Communications capacity?')
    )
    event_map = models.ForeignKey(
        'DrefFile', on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('event map'),
        related_name='event_map_dref'
    )
    images = models.ManyToManyField(
        'DrefFile', blank=True, null=True,
        verbose_name=_('images'),
        related_name='image_dref'
    )
    budget_file = models.ForeignKey(
        'DrefFile', on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('budget file'),
        related_name='budget_file_dref'
    )
    budget_file_preview = models.FileField(
        verbose_name=_('budget file preview'),
        null=True, blank=True,
        upload_to='dref/images/'
    )
    cover_image = models.ForeignKey(
        'DrefFile', on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_('cover image'),
        related_name='cover_image_dref'
    )

    class Meta:
        verbose_name = _('dref')
        verbose_name_plural = _('drefs')

    def save(self, *args, **kwargs):
        # TODO: Need to remove this if not required later
        if self.date_of_approval:
            self.status = Dref.Status.COMPLETED
        elif not self.date_of_approval:
            self.status = Dref.Status.IN_PROGESS
        return super().save(*args, **kwargs)


class DrefCountryDistrict(models.Model):
    dref = models.ForeignKey(Dref, verbose_name=_('dref'),
                             on_delete=models.CASCADE)
    country = models.ForeignKey(Country, verbose_name=_('country'),
                                on_delete=models.CASCADE,
                                help_text=_('Affected County'))
    district = models.ManyToManyField(District, blank=True,
                                      verbose_name=_('district'))

    class Meta:
        unique_together = ('dref', 'country')


class DrefFile(models.Model):
    file = models.FileField(
        blank=True, null=True, verbose_name=_('file'),
        upload_to='dref/images/',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('created_by'),
        on_delete=models.SET_NULL, null=True,
    )

    class Meta:
        verbose_name = _('dref file')
        verbose_name_plural = _('dref files')
