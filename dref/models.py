import reversion
import os
import copy

from pdf2image import convert_from_bytes

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.templatetags.static import static
from django.core.exceptions import ValidationError
from django.contrib.postgres.aggregates import ArrayAgg
from django.utils import timezone

from api.models import Country, DisasterType, District, FieldReport


@reversion.register()
class NationalSocietyAction(models.Model):
    class Title(models.TextChoices):
        NATIONAL_SOCIETY_READINESS = "national_society_readiness", _("National Society Readiness")
        ASSESSMENT = "assessment", _("Assessment")
        COORDINATION = "coordination", _("Coordination")
        RESOURCE_MOBILIZATION = "resource_mobilization", _("Resource Mobilization")
        ACTIVATION_OF_CONTINGENCY_PLANS = "activation_of_contingency_plans", _("Activation Of Contingency Plans")
        NATIONAL_SOCIETY_EOC = "national_society_eoc", _("National Society EOC")
        SHELTER_HOUSING_AND_SETTLEMENTS = "shelter_housing_and_settlements", _("Shelter, Housing And Settlements")
        LIVELIHOODS_AND_BASIC_NEEDS = "livelihoods_and_basic_needs", _("Livelihoods And Basic Needs")
        HEALTH = "health", _("Health")
        WATER_SANITATION_AND_HYGIENE = "water_sanitation_and_hygiene", _("Water, Sanitation And Hygiene")
        PROTECTION_GENDER_AND_INCLUSION = "protection_gender_and_inclusion", _("Protection, Gender And Inclusion")
        EDUCATION = "education", _("Education")
        MIGRATION = "migration", _("Migration")
        RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY = "risk_reduction_climate_adaptation_and_recovery", _(
            "Risk Reduction, Climate Adaptation And Recovery"
        )
        COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY = "community_engagement_and _accountability", _(
            "Community Engagement And Accountability"
        )
        ENVIRONMENT_SUSTAINABILITY = "environment_sustainability ", _("Environment Sustainability")
        MULTI_PURPOSE_CASH = "multi-purpose_cash", _("Multi-purpose Cash")
        OTHER = "other", _("Other")

    title = models.CharField(max_length=255, verbose_name=_("title"), choices=Title.choices)
    description = models.TextField(verbose_name=_("description"), blank=True, null=True)

    class Meta:
        verbose_name = _("national society action")
        verbose_name_plural = _("national society actions")

    @staticmethod
    def get_image_map(title, request):
        title_static_map = {
            NationalSocietyAction.Title.SHELTER_HOUSING_AND_SETTLEMENTS: "shelter.png",
            NationalSocietyAction.Title.LIVELIHOODS_AND_BASIC_NEEDS: "livelihood.png",
            NationalSocietyAction.Title.HEALTH: "health.png",
            NationalSocietyAction.Title.WATER_SANITATION_AND_HYGIENE: "water.png",
            NationalSocietyAction.Title.PROTECTION_GENDER_AND_INCLUSION: "protection.png",
            NationalSocietyAction.Title.EDUCATION: "education.png",
            NationalSocietyAction.Title.MIGRATION: "migration.png",
            NationalSocietyAction.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY: "risk.png",
            NationalSocietyAction.Title.ENVIRONMENT_SUSTAINABILITY: "environment.png",
            NationalSocietyAction.Title.NATIONAL_SOCIETY_READINESS: "favicon.png",
            NationalSocietyAction.Title.ASSESSMENT: "favicon.png",
            NationalSocietyAction.Title.COORDINATION: "favicon.png",
            NationalSocietyAction.Title.RESOURCE_MOBILIZATION: "favicon.png",
            NationalSocietyAction.Title.ACTIVATION_OF_CONTINGENCY_PLANS: "favicon.png",
            NationalSocietyAction.Title.NATIONAL_SOCIETY_EOC: "favicon.png",
            NationalSocietyAction.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY: "favicon.png",
            NationalSocietyAction.Title.MULTI_PURPOSE_CASH: "cash.png",
            NationalSocietyAction.Title.OTHER: "favicon.png",
        }
        return request.build_absolute_uri(static(os.path.join("images/dref", title_static_map[title])))


@reversion.register()
class IdentifiedNeed(models.Model):
    class Title(models.TextChoices):
        SHELTER_HOUSING_AND_SETTLEMENTS = "shelter_housing_and_settlements", _("Shelter Housing And Settlements")
        LIVELIHOODS_AND_BASIC_NEEDS = "livelihoods_and_basic_needs", _("Livelihoods And Basic Needs")
        HEALTH = "health", _("Health")
        WATER_SANITATION_AND_HYGIENE = "water_sanitation_and_hygiene", _("Water, Sanitation And Hygiene")
        PROTECTION_GENDER_AND_INCLUSION = "protection_gender_and_inclusion", _("Protection, Gender And Inclusion")
        EDUCATION = "education", _("Education")
        MIGRATION = "migration", _("Migration")
        MULTI_PURPOSE_CASH_GRANTS = "multi_purpose_cash_grants", _("Multi purpose cash grants")
        RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY = "risk_reduction_climate_adaptation_and_recovery", _(
            "Risk Reduction, Climate Adaptation And Recovery"
        )
        COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY = "community_engagement_and _accountability", _(
            "Community Engagement And Accountability"
        )
        ENVIRONMENT_SUSTAINABILITY = "environment_sustainability ", _("Environment Sustainability")
        SHELTER_CLUSTER_COORDINATION = "shelter_cluster_coordination", _("Shelter Cluster Coordination")

    title = models.CharField(max_length=255, verbose_name=_("title"), choices=Title.choices)
    description = models.TextField(verbose_name=_("description"), blank=True, null=True)

    class Meta:
        verbose_name = _("identified need")
        verbose_name_plural = _("identified needs")

    @staticmethod
    def get_image_map(title, request):
        title_static_map = {
            IdentifiedNeed.Title.SHELTER_HOUSING_AND_SETTLEMENTS: "shelter.png",
            IdentifiedNeed.Title.LIVELIHOODS_AND_BASIC_NEEDS: "livelihood.png",
            IdentifiedNeed.Title.HEALTH: "health.png",
            IdentifiedNeed.Title.WATER_SANITATION_AND_HYGIENE: "water.png",
            IdentifiedNeed.Title.PROTECTION_GENDER_AND_INCLUSION: "protection.png",
            IdentifiedNeed.Title.MULTI_PURPOSE_CASH_GRANTS: "cash.png",
            IdentifiedNeed.Title.EDUCATION: "education.png",
            IdentifiedNeed.Title.MIGRATION: "migration.png",
            IdentifiedNeed.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY: "risk.png",
            IdentifiedNeed.Title.ENVIRONMENT_SUSTAINABILITY: "environment.png",
            IdentifiedNeed.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY: "participation_team.png",
            IdentifiedNeed.Title.SHELTER_CLUSTER_COORDINATION: "migration.png",
        }
        return request.build_absolute_uri(static(os.path.join("images/dref", title_static_map[title])))


@reversion.register()
class PlannedInterventionIndicators(models.Model):
    title = models.CharField(max_length=255, verbose_name="Title")
    target = models.IntegerField(verbose_name=_("Target"), null=True, blank=True)
    actual = models.IntegerField(verbose_name=_("Actual"), null=True, blank=True)

    class Meta:
        verbose_name = _("planned intervention indicator")
        verbose_name_plural = _("planned intervention indicators")

    def __str__(self):
        return self.title


class PlannedIntervention(models.Model):
    class Title(models.TextChoices):
        SHELTER_HOUSING_AND_SETTLEMENTS = "shelter_housing_and_settlements", _("Shelter Housing And Settlements")
        LIVELIHOODS_AND_BASIC_NEEDS = "livelihoods_and_basic_needs", _("Livelihoods And Basic Needs")
        HEALTH = "health", _("Health")
        WATER_SANITATION_AND_HYGIENE = "water_sanitation_and_hygiene", _("Water, Sanitation And Hygiene")
        PROTECTION_GENDER_AND_INCLUSION = "protection_gender_and_inclusion", _("Protection, Gender And Inclusion")
        EDUCATION = "education", _("Education")
        MIGRATION = "migration", _("Migration")
        RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY = "risk_reduction_climate_adaptation_and_recovery_", _(
            "Risk Reduction, Climate Adaptation And Recovery"
        )
        SECRETARIAT_SERVICES = "secretariat_services", _("Secretariat Services")
        NATIONAL_SOCIETY_STRENGTHENING = "national_society_strengthening", _("National Society Strengthening")
        MULTI_PURPOSE_CASH = "multi-purpose_cash", _("Multi-purpose Cash")
        ENVIRONMENTAL_SUSTAINABILITY = "environmental_sustainability", _("Environmental Sustainability")
        COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY = "community_engagement_and_accountability", _(
            "Community Engagement And Accountability"
        )

    title = models.CharField(max_length=255, verbose_name=_("title"), choices=Title.choices)
    description = models.TextField(verbose_name=_("description"), blank=True, null=True)
    person_targeted = models.IntegerField(verbose_name=_("person targeted"), null=True, blank=True)
    person_assisted = models.IntegerField(verbose_name=_("person assisted"), null=True, blank=True)
    budget = models.IntegerField(verbose_name=_("budget"), blank=True, null=True)
    male = models.IntegerField(verbose_name=_("male"), blank=True, null=True)
    female = models.IntegerField(verbose_name=_("female"), blank=True, null=True)
    indicators = models.ManyToManyField(
        PlannedInterventionIndicators,
        verbose_name=_("Indicators"),
        blank=True,
    )
    progress_towards_outcome = models.TextField(verbose_name=_("Progress Towards Outcome"), blank=True, null=True)
    narrative_description_of_achievements = models.TextField(
        verbose_name=_("Narrative description of achievements"), blank=True, null=True
    )
    challenges = models.TextField(verbose_name=_("Challenges"), null=True, blank=True)
    lessons_learnt = models.TextField(verbose_name=_("Lessons learnt"), null=True, blank=True)

    class Meta:
        verbose_name = _("planned intervention")
        verbose_name_plural = _("planned interventions")

    @staticmethod
    def get_image_map(title, request):
        title_static_map = {
            PlannedIntervention.Title.SHELTER_HOUSING_AND_SETTLEMENTS: "shelter.png",
            PlannedIntervention.Title.LIVELIHOODS_AND_BASIC_NEEDS: "livelihood.png",
            PlannedIntervention.Title.HEALTH: "health.png",
            PlannedIntervention.Title.WATER_SANITATION_AND_HYGIENE: "water.png",
            PlannedIntervention.Title.PROTECTION_GENDER_AND_INCLUSION: "protection.png",
            PlannedIntervention.Title.EDUCATION: "education.png",
            PlannedIntervention.Title.MIGRATION: "migration.png",
            PlannedIntervention.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY: "risk.png",
            PlannedIntervention.Title.SECRETARIAT_SERVICES: "work.png",
            PlannedIntervention.Title.NATIONAL_SOCIETY_STRENGTHENING: "independence.png",
            PlannedIntervention.Title.MULTI_PURPOSE_CASH: "cash.png",
            PlannedIntervention.Title.ENVIRONMENTAL_SUSTAINABILITY: "environment.png",
            PlannedIntervention.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY: "participation_team.png",
        }
        return request.build_absolute_uri(static(os.path.join("images/dref", title_static_map[title])))


@reversion.register()
class RiskSecurity(models.Model):
    client_id = models.CharField(max_length=50, null=True, blank=True, verbose_name=_("client_id"))
    risk = models.TextField(verbose_name=_("Risk"), null=True, blank=True)
    mitigation = models.TextField(verbose_name=_("Mitigation"), null=True, blank=True)


@reversion.register()
class Dref(models.Model):
    class DrefType(models.IntegerChoices):
        IMMINENT = 0, _("Imminent")
        ASSESSMENT = 1, _("Assessment")
        RESPONSE = 2, _("Response")
        LOAN = 3, _("Loan")

    class OnsetType(models.IntegerChoices):
        SLOW = 1, _("Slow")
        SUDDEN = 2, _("Sudden")

    class DisasterCategory(models.IntegerChoices):
        YELLOW = 0, _("Yellow")
        ORANGE = 1, _("Orange")
        RED = 2, _("Red")

    class Status(models.IntegerChoices):
        IN_PROGRESS = 0, _("In Progress")
        COMPLETED = 1, _("Completed")

    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=_("modified at"), default=timezone.now, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_by_dref",
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("modified by"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="modified_by_dref",
    )
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name=_("users"), blank=True, related_name="user_dref")
    field_report = models.ForeignKey(
        FieldReport,
        verbose_name=_("field report"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="field_report_dref",
    )
    title = models.CharField(verbose_name=_("title"), max_length=255)
    title_prefix = models.CharField(verbose_name=_("title prefix"), max_length=255, null=True, blank=True)
    national_society = models.ForeignKey(
        Country,
        verbose_name=_("national_society"),
        on_delete=models.CASCADE,
    )
    disaster_type = models.ForeignKey(
        DisasterType, verbose_name=_("disaster type"), blank=True, null=True, on_delete=models.SET_NULL
    )
    type_of_dref = models.IntegerField(choices=DrefType.choices, verbose_name=_("dref type"), null=True, blank=True)
    type_of_onset = models.IntegerField(choices=OnsetType.choices, verbose_name=_("onset type"), null=True, blank=True)
    disaster_category = models.IntegerField(
        choices=DisasterCategory.choices, verbose_name=_("disaster category"), null=True, blank=True
    )
    status = models.IntegerField(choices=Status.choices, verbose_name=_("status"), null=True, blank=True)
    num_assisted = models.IntegerField(verbose_name=_("number of assisted"), blank=True, null=True)
    num_affected = models.IntegerField(verbose_name=_("number of affected"), blank=True, null=True)
    amount_requested = models.IntegerField(verbose_name=_("amount requested"), blank=True, null=True)
    people_in_need = models.IntegerField(verbose_name=_("people in need"), blank=True, null=True)
    emergency_appeal_planned = models.BooleanField(verbose_name=_("emergency appeal planned "), null=True, blank=True)
    event_date = models.DateField(
        verbose_name=_("event date"), null=True, blank=True, help_text=_("Date of event/Approximate date of impact")
    )
    event_text = models.TextField(verbose_name=_("event text"), blank=True, null=True)
    ns_respond_date = models.DateField(
        verbose_name=_("ns respond date"), null=True, blank=True, help_text=_("NS anticipatory actions started/NS response")
    )
    did_it_affect_same_area = models.BooleanField(
        null=True, blank=True, help_text=_("Has a similar event affected the same areas in the past?")
    )
    did_it_affect_same_population = models.BooleanField(null=True, blank=True, help_text=_("Did it affect the same population?"))
    affect_same_population_text = models.TextField(blank=True, null=True, verbose_name=_("affect same population text"))
    did_ns_respond = models.BooleanField(null=True, blank=True, default=False, help_text=_("Did NS respond"))
    did_ns_request_fund = models.BooleanField(
        null=True, blank=True, default=False, help_text=_("Did the NS request funding from DREF?")
    )
    ns_request_text = models.TextField(blank=True, null=True, verbose_name=_("ns request text"))
    dref_recurrent_text = models.TextField(verbose_name=_("dref recurrent text"), blank=True, null=True)
    lessons_learned = models.TextField(verbose_name=_("lessons learned"), blank=True, null=True)
    event_description = models.TextField(verbose_name=_("event description"), blank=True, null=True)
    anticipatory_actions = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("anticipatory actions"),
        help_text=_("Description of anticipatory actions or imminent disaster"),
    )
    event_scope = models.TextField(
        blank=True, null=True, verbose_name=_("event scope"), help_text=_("Scope and scale of event")
    )
    national_society_actions = models.ManyToManyField(
        NationalSocietyAction, verbose_name=_("national society actions"), blank=True
    )
    government_requested_assistance = models.BooleanField(
        null=True, blank=True, help_text=_("Has government requested assistance")
    )
    government_requested_assistance_date = models.DateField(
        verbose_name=_("government requested assistance date"), null=True, blank=True
    )
    national_authorities = models.TextField(verbose_name=_("national authorities"), blank=True, null=True)
    ifrc = models.TextField(verbose_name=_("ifrc"), blank=True, null=True)
    icrc = models.TextField(verbose_name=_("icrc"), blank=True, null=True)
    partner_national_society = models.TextField(verbose_name=_("partner national society"), blank=True, null=True)
    un_or_other_actor = models.TextField(verbose_name=_("un or other"), blank=True, null=True)
    is_there_major_coordination_mechanism = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_("Is major coordination mechanism"),
    )
    major_coordination_mechanism = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("major coordination mechanism"),
        help_text=_("List major coordination mechanisms in place"),
    )
    needs_identified = models.ManyToManyField(IdentifiedNeed, verbose_name=_("needs identified"), blank=True)
    identified_gaps = models.TextField(
        verbose_name=_("identified gaps"),
        blank=True,
        null=True,
        help_text=_("Any identified gaps/limitations in the assessment"),
    )
    people_assisted = models.TextField(verbose_name=_("people assisted"), blank=True, null=True)
    selection_criteria = models.TextField(
        verbose_name=_("selection criteria"), blank=True, null=True, help_text=_("Selection criteria for affected people")
    )
    entity_affected = models.TextField(
        verbose_name=_("entity affected"),
        blank=True,
        null=True,
        help_text=_("Protection, gender, Inclusion affected in this process"),
    )
    community_involved = models.TextField(
        verbose_name=_("community involved"),
        blank=True,
        null=True,
        help_text=_("Community been involved in the analysis of the process"),
    )
    women = models.IntegerField(verbose_name=_("women"), blank=True, null=True)
    men = models.IntegerField(verbose_name=_("men"), blank=True, null=True)
    girls = models.IntegerField(verbose_name=_("girls"), help_text=_("Girls under 18"), blank=True, null=True)
    boys = models.IntegerField(verbose_name=_("boys"), help_text=_("Boys under 18"), blank=True, null=True)
    total_targeted_population = models.IntegerField(
        verbose_name=_("total targeted population"),
        help_text=_("Estimated number of targeted people"),
        blank=True,
        null=True,
    )
    disability_people_per = models.FloatField(
        verbose_name=_("disability people per"),
        help_text=_("Estimated % people disability"),
        blank=True,
        null=True,
    )
    people_per_urban = models.FloatField(
        verbose_name=_("people per urban"),
        help_text=_("Estimated % people Urban"),
        blank=True,
        null=True,
    )
    people_per_local = models.FloatField(
        verbose_name=_("people per local"),
        help_text=_("Estimated % people Rural"),
        blank=True,
        null=True,
    )
    people_targeted_with_early_actions = models.IntegerField(
        verbose_name=_("people targeted with early actions"),
        help_text=_("Number of persons targeted with early actions"),
        blank=True,
        null=True,
    )
    displaced_people = models.IntegerField(
        verbose_name=_("displaced people"), help_text=_("Estimated number of displaced people"), blank=True, null=True
    )
    operation_objective = models.TextField(
        verbose_name=_("operation objective"),
        help_text=_("Overall objective of the operation"),
        blank=True,
        null=True,
    )
    response_strategy = models.TextField(
        verbose_name=_("response strategy"),
        blank=True,
        null=True,
    )
    planned_interventions = models.ManyToManyField(PlannedIntervention, verbose_name=_("planned intervention"), blank=True)
    did_national_society = models.BooleanField(verbose_name=_("Did National Society"), null=True, blank=True)
    ns_request_date = models.DateField(verbose_name=_("ns request date"), null=True, blank=True)
    submission_to_geneva = models.DateField(verbose_name=_("submission to geneva"), null=True, blank=True)
    date_of_approval = models.DateField(verbose_name=_("date of approval"), null=True, blank=True)
    end_date = models.DateField(verbose_name=_("end date"), null=True, blank=True)
    publishing_date = models.DateField(verbose_name=_("publishing date"), null=True, blank=True)
    operation_timeframe = models.IntegerField(verbose_name=_("operation timeframe"), null=True, blank=True)
    appeal_code = models.CharField(verbose_name=_("appeal code"), max_length=255, null=True, blank=True)
    glide_code = models.CharField(verbose_name=_("glide number"), max_length=255, null=True, blank=True)
    ifrc_appeal_manager_name = models.CharField(
        verbose_name=_("ifrc appeal manager name"), max_length=255, null=True, blank=True
    )
    ifrc_appeal_manager_email = models.CharField(
        verbose_name=_("ifrc appeal manager email"), max_length=255, null=True, blank=True
    )
    ifrc_appeal_manager_title = models.CharField(
        verbose_name=_("ifrc appeal manager title"), max_length=255, null=True, blank=True
    )
    ifrc_appeal_manager_phone_number = models.CharField(
        verbose_name=_("ifrc appeal manager phone number"), max_length=100, null=True, blank=True
    )
    ifrc_project_manager_name = models.CharField(
        verbose_name=_("ifrc project manager name"), max_length=255, null=True, blank=True
    )
    ifrc_project_manager_email = models.CharField(
        verbose_name=_("ifrc project manager email"), max_length=255, null=True, blank=True
    )
    ifrc_project_manager_title = models.CharField(
        verbose_name=_("ifrc project manager title"), max_length=255, null=True, blank=True
    )
    ifrc_project_manager_phone_number = models.CharField(
        verbose_name=_("ifrc project manager phone number"), max_length=100, null=True, blank=True
    )
    national_society_contact_name = models.CharField(
        verbose_name=_("national society contact name"), max_length=255, null=True, blank=True
    )
    national_society_contact_email = models.CharField(
        verbose_name=_("national society contact email"), max_length=255, null=True, blank=True
    )
    national_society_contact_title = models.CharField(
        verbose_name=_("national society contact title"), max_length=255, null=True, blank=True
    )
    national_society_contact_phone_number = models.CharField(
        verbose_name=_("national society contact phone number"), max_length=100, null=True, blank=True
    )
    media_contact_name = models.CharField(verbose_name=_("media contact name"), max_length=255, null=True, blank=True)
    media_contact_email = models.CharField(verbose_name=_("media contact email"), max_length=255, null=True, blank=True)
    media_contact_title = models.CharField(verbose_name=_("media contact title"), max_length=255, null=True, blank=True)
    media_contact_phone_number = models.CharField(
        verbose_name=_("media_contact phone number"), max_length=100, null=True, blank=True
    )
    ifrc_emergency_name = models.CharField(verbose_name=_("ifrc emergency name"), max_length=255, null=True, blank=True)
    ifrc_emergency_email = models.CharField(verbose_name=_("ifrc emergency email"), max_length=255, null=True, blank=True)
    ifrc_emergency_title = models.CharField(verbose_name=_("ifrc emergency title"), max_length=255, null=True, blank=True)
    ifrc_emergency_phone_number = models.CharField(
        verbose_name=_("ifrc emergency phone number"), max_length=100, null=True, blank=True
    )
    originator_name = models.CharField(verbose_name=_("originator name"), max_length=255, null=True, blank=True)
    originator_email = models.CharField(verbose_name=_("originator email"), max_length=255, null=True, blank=True)
    originator_title = models.CharField(verbose_name=_("originator title"), max_length=255, null=True, blank=True)
    originator_phone_number = models.CharField(
        verbose_name=_("originator phone number"), max_length=100, null=True, blank=True
    )
    regional_focal_point_name = models.CharField(
        verbose_name=_("regional focal point name"), max_length=255, null=True, blank=True
    )
    regional_focal_point_email = models.CharField(
        verbose_name=_("regional focal point email"), max_length=255, null=True, blank=True
    )
    regional_focal_point_title = models.CharField(
        verbose_name=_("regional focal point title"), max_length=255, null=True, blank=True
    )
    regional_focal_point_phone_number = models.CharField(
        verbose_name=_("regional focal point phone number"), max_length=100, null=True, blank=True
    )
    human_resource = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("human resource"),
        help_text=_("how many volunteers and staff involved in the response?"),
    )
    is_surge_personnel_deployed = models.BooleanField(blank=True, null=True, verbose_name=_("Is surge personnel deployed"))
    surge_personnel_deployed = models.TextField(
        blank=True, null=True, verbose_name=_("surge personnel deployed"), help_text=_("Will a Surge personnel be deployed?")
    )
    logistic_capacity_of_ns = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("logistic capacity of ns"),
        help_text=_("what is the logistics capacity of the National Society?"),
    )
    safety_concerns = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("safety concerns"),
        help_text=_("Are there any safety/security concerns which may impact the implementation of this operation?"),
    )
    pmer = models.TextField(blank=True, null=True, verbose_name=_("pmer"), help_text=_("Does the NS have PMER capacity?"))
    communication = models.TextField(
        blank=True, null=True, verbose_name=_("organization"), help_text=_("Does the NS have Communications capacity?")
    )
    event_map = models.ForeignKey(
        "DrefFile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("event map"),
        related_name="event_map_dref",
    )
    images = models.ManyToManyField(
        # null=True is not ok here: null has no effect on ManyToManyField.
        "DrefFile",
        blank=True,
        verbose_name=_("images"),
        related_name="image_dref",
    )
    budget_file = models.ForeignKey(
        "DrefFile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("budget file"),
        related_name="budget_file_dref",
    )
    budget_file_preview = models.FileField(
        verbose_name=_("budget file preview"), null=True, blank=True, upload_to="dref/images/"
    )
    assessment_report = models.ForeignKey(
        "DrefFile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Assessment Report"),
        related_name="dref_assessment_report",
    )
    supporting_document = models.ForeignKey(
        "DrefFile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Supporting Document"),
        related_name="dref_supporting_document",
    )
    cover_image = models.ForeignKey(
        "DrefFile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("cover image"),
        related_name="cover_image_dref",
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name=_("Is published"),
    )
    is_final_report_created = models.BooleanField(
        default=False,
        verbose_name=_("Is final report created"),
    )
    country = models.ForeignKey(
        Country,
        verbose_name=_("country"),
        on_delete=models.CASCADE,
        help_text=_("Affected County"),
        null=True,
        blank=True,
        related_name="dref_country",
    )
    district = models.ManyToManyField(District, blank=True, verbose_name=_("district"))
    risk_security = models.ManyToManyField(RiskSecurity, blank=True, verbose_name=_("Risk Security"))
    risk_security_concern = models.TextField(blank=True, null=True, verbose_name=_("Risk Security Concern"))
    is_man_made_event = models.BooleanField(verbose_name=_("Is Man-made Event"), null=True, blank=True)
    __budget_file_id = None
    is_active = models.BooleanField(verbose_name=_("Is Active"), null=True, blank=True)

    class Meta:
        verbose_name = _("dref")
        verbose_name_plural = _("drefs")

    def save(self, *args, **kwargs):
        if self.budget_file and self.budget_file_id != self.__budget_file_id:
            pages = convert_from_bytes(self.budget_file.file.read())
            if len(pages) > 0:
                budget_file_preview = pages[0]  # get first page
                filename = f'preview_{self.budget_file.file.name.split("/")[0]}.png'
                temp_image = open(os.path.join("/tmp", filename), "wb")
                budget_file_preview.save(temp_image, "PNG")
                thumb_data = open(os.path.join("/tmp", filename), "rb")
                self.budget_file_preview.save(filename, thumb_data, save=False)
            else:
                raise ValidationError({"budget_file": "Sorry cannot generate preview for empty pdf"})

        self.status = Dref.Status.COMPLETED if self.is_published else Dref.Status.IN_PROGRESS
        self.__budget_file_id = self.budget_file_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} – {self.created_at.date()}, {self.get_status_display()}"

    @staticmethod
    def get_for(user):
        user_id = user.id
        current_user_list = []
        current_user_list.append(user_id)
        return Dref.objects.annotate(
            created_user_list=models.F("created_by"),
            users_list=ArrayAgg("users", filter=models.Q(users__isnull=False)),
            op_users=models.Subquery(
                DrefOperationalUpdate.objects.filter(dref=models.OuterRef("id"))
                .order_by()
                .values("id")
                .annotate(c=ArrayAgg("users", filter=models.Q(users__isnull=False)))
                .values("c")[:1]
            ),
            fr_users=models.Subquery(
                DrefFinalReport.objects.filter(dref=models.OuterRef("id"))
                .order_by()
                .values("id")
                .annotate(c=ArrayAgg("users", filter=models.Q(users__isnull=False)))
                .values("c")[:1],
            ),
        ).filter(
            models.Q(created_user_list=user_id)
            | models.Q(users_list__contains=current_user_list)
            | models.Q(op_users__contains=current_user_list)
            | models.Q(fr_users__contains=current_user_list)
        ).distinct()


class DrefFile(models.Model):
    file = models.FileField(
        verbose_name=_("file"),
        upload_to="dref/images/",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created_by"),
        on_delete=models.SET_NULL,
        null=True,
    )
    caption = models.CharField(max_length=225, blank=True, null=True)
    client_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = _("dref file")
        verbose_name_plural = _("dref files")

    def clone(self, user):
        clone = copy.deepcopy(self)
        clone.id = None
        clone.client_id = None
        clone.created_by = user
        clone.save()
        return clone


@reversion.register()
class DrefOperationalUpdate(models.Model):
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=_("modified at"), default=timezone.now, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_by_dref_operational_update",
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("modified by"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="modified_by_dref_operational_update",
    )
    dref = models.ForeignKey(Dref, verbose_name=_("Dref"), on_delete=models.CASCADE)
    title = models.CharField(
        verbose_name=_("title"),
        null=True,
        blank=True,
        max_length=255,
    )
    title_prefix = models.CharField(verbose_name=_("title prefix"), max_length=255, null=True, blank=True)
    national_society = models.ForeignKey(
        Country,
        verbose_name=_("national_society"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="national_society_operational_update",
    )
    disaster_type = models.ForeignKey(
        DisasterType, verbose_name=_("disaster type"), blank=True, null=True, on_delete=models.SET_NULL
    )
    type_of_dref = models.IntegerField(choices=Dref.DrefType.choices, verbose_name=_("dref type"), null=True, blank=True)
    type_of_onset = models.IntegerField(choices=Dref.OnsetType.choices, verbose_name=_("onset type"), null=True, blank=True)
    disaster_category = models.IntegerField(
        choices=Dref.DisasterCategory.choices, verbose_name=_("disaster category"), null=True, blank=True
    )
    status = models.IntegerField(choices=Dref.Status.choices, verbose_name=_("status"), null=True, blank=True)
    number_of_people_targeted = models.IntegerField(verbose_name=_("Number of people targeted"), blank=True, null=True)
    number_of_people_affected = models.IntegerField(verbose_name=_("number of people affected"), blank=True, null=True)
    dref_allocated_so_far = models.IntegerField(verbose_name=_("Dref allocated so far"), null=True, blank=True)
    additional_allocation = models.IntegerField(verbose_name=_("Additional allocation"), null=True, blank=True)
    total_dref_allocation = models.IntegerField(verbose_name=_("Total dref allocation"), null=True, blank=True)
    emergency_appeal_planned = models.BooleanField(verbose_name=_("emergency appeal planned "), null=True, blank=True)
    event_map = models.ForeignKey(
        "DrefFile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("event map"),
        related_name="event_map_dref_operational_update",
    )
    images = models.ManyToManyField(
        "DrefFile", blank=True, verbose_name=_("images"), related_name="image_dref_operational_update"
    )
    cover_image = models.ForeignKey(
        "DrefFile",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("cover image"),
        related_name="cover_image_dref_operational_update",
    )
    budget_file = models.ForeignKey(
        "DrefFile",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("budget file"),
        related_name="budget_file_dref_operational_update",
    )
    assessment_report = models.ForeignKey(
        "DrefFile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Assessment Report"),
        related_name="dref_operational_update_assessment_report",
    )
    photos = models.ManyToManyField(
        "DrefFile", blank=True, verbose_name=_("images"), related_name="photos_dref_operational_update"
    )
    operational_update_number = models.IntegerField(verbose_name=_("Operational Update Number"), null=True, blank=True)
    reporting_timeframe = models.DateField(verbose_name=_("Reporting Timeframe"), null=True, blank=True)
    update_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Update Date"),
    )
    is_timeframe_extension_required = models.BooleanField(
        null=True, blank=True, verbose_name=_("Is Timeframe Extension Required")
    )
    new_operational_start_date = models.DateField(verbose_name=_("New Operation Start Date"), null=True, blank=True)
    new_operational_end_date = models.DateField(verbose_name=_("New Operation End Date"), null=True, blank=True)
    total_operation_timeframe = models.IntegerField(verbose_name=_("Total Operation Timeframe"), null=True, blank=True)
    appeal_code = models.CharField(verbose_name=_("appeal code"), max_length=255, null=True, blank=True)
    glide_code = models.CharField(verbose_name=_("glide number"), max_length=255, null=True, blank=True)
    ifrc_appeal_manager_name = models.CharField(
        verbose_name=_("ifrc appeal manager name"), max_length=255, null=True, blank=True
    )
    ifrc_appeal_manager_email = models.CharField(
        verbose_name=_("ifrc appeal manager email"), max_length=255, null=True, blank=True
    )
    ifrc_appeal_manager_title = models.CharField(
        verbose_name=_("ifrc appeal manager title"), max_length=255, null=True, blank=True
    )
    ifrc_appeal_manager_phone_number = models.CharField(
        verbose_name=_("ifrc appeal manager phone number"), max_length=100, null=True, blank=True
    )
    ifrc_project_manager_name = models.CharField(
        verbose_name=_("ifrc project manager name"), max_length=255, null=True, blank=True
    )
    ifrc_project_manager_email = models.CharField(
        verbose_name=_("ifrc project manager email"), max_length=255, null=True, blank=True
    )
    ifrc_project_manager_title = models.CharField(
        verbose_name=_("ifrc project manager title"), max_length=255, null=True, blank=True
    )
    ifrc_project_manager_phone_number = models.CharField(
        verbose_name=_("ifrc project manager phone number"), max_length=100, null=True, blank=True
    )
    national_society_contact_name = models.CharField(
        verbose_name=_("national society contact name"), max_length=255, null=True, blank=True
    )
    national_society_contact_email = models.CharField(
        verbose_name=_("national society contact email"), max_length=255, null=True, blank=True
    )
    national_society_contact_title = models.CharField(
        verbose_name=_("national society contact title"), max_length=255, null=True, blank=True
    )
    national_society_contact_phone_number = models.CharField(
        verbose_name=_("national society contact phone number"), max_length=100, null=True, blank=True
    )
    media_contact_name = models.CharField(verbose_name=_("media contact name"), max_length=255, null=True, blank=True)
    media_contact_email = models.CharField(verbose_name=_("media contact email"), max_length=255, null=True, blank=True)
    media_contact_title = models.CharField(verbose_name=_("media contact title"), max_length=255, null=True, blank=True)
    media_contact_phone_number = models.CharField(
        verbose_name=_("media_contact phone number"), max_length=100, null=True, blank=True
    )
    ifrc_emergency_name = models.CharField(verbose_name=_("ifrc emergency name"), max_length=255, null=True, blank=True)
    ifrc_emergency_email = models.CharField(verbose_name=_("ifrc emergency email"), max_length=255, null=True, blank=True)
    ifrc_emergency_title = models.CharField(verbose_name=_("ifrc emergency title"), max_length=255, null=True, blank=True)
    ifrc_emergency_phone_number = models.CharField(
        verbose_name=_("ifrc emergency phone number"), max_length=100, null=True, blank=True
    )
    regional_focal_point_name = models.CharField(
        verbose_name=_("regional focal point name"), max_length=255, null=True, blank=True
    )
    regional_focal_point_email = models.CharField(
        verbose_name=_("regional focal point email"), max_length=255, null=True, blank=True
    )
    regional_focal_point_title = models.CharField(
        verbose_name=_("regional focal point title"), max_length=255, null=True, blank=True
    )
    regional_focal_point_phone_number = models.CharField(
        verbose_name=_("regional focal point phone number"), max_length=100, null=True, blank=True
    )
    changing_timeframe_operation = models.BooleanField(null=True, blank=True, verbose_name=_("Changing time operation"))
    changing_operation_strategy = models.BooleanField(null=True, blank=True, verbose_name=_("Changing operation strategy"))
    changing_target_population_of_operation = models.BooleanField(
        null=True, blank=True, verbose_name=_("Changing target population of operation")
    )
    changing_geographic_location = models.BooleanField(null=True, blank=True, verbose_name=_("Changing geographic location"))
    changing_budget = models.BooleanField(null=True, blank=True, verbose_name=_("Changing budget"))
    request_for_second_allocation = models.BooleanField(
        null=True, blank=True, verbose_name=_("Request for second allocation")
    )
    summary_of_change = models.TextField(verbose_name=_("Summary of change"), null=True, blank=True)
    has_change_since_request = models.BooleanField(verbose_name=_("Has change since request"), null=True, blank=True)
    event_description = models.TextField(verbose_name=_("Event description"), null=True, blank=True)
    anticipatory_actions = models.TextField(verbose_name=_("Anticipatory actions"), null=True, blank=True)
    event_scope = models.TextField(verbose_name=_("Event scope"), null=True, blank=True)
    national_society_actions = models.ManyToManyField(
        NationalSocietyAction, verbose_name=_("national society actions"), blank=True
    )
    ifrc = models.TextField(verbose_name=_("ifrc"), blank=True, null=True)
    icrc = models.TextField(verbose_name=_("icrc"), blank=True, null=True)
    partner_national_society = models.TextField(verbose_name=_("partner national society"), blank=True, null=True)
    government_requested_assistance = models.BooleanField(
        null=True, blank=True, help_text=_("Has government requested assistance")
    )
    national_authorities = models.TextField(verbose_name=_("national authorities"), blank=True, null=True)
    is_there_un_or_other_actor = models.BooleanField(null=True, blank=True, verbose_name=_("Is there un_or_other_actor"))
    un_or_other_actor = models.TextField(verbose_name=_("un or other"), blank=True, null=True)
    is_there_major_coordination_mechanism = models.BooleanField(
        null=True, blank=True, help_text=_("Is there major coordinate mechanism")
    )
    major_coordination_mechanism = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("major coordination mechanism"),
    )
    needs_identified = models.ManyToManyField(IdentifiedNeed, verbose_name=_("needs identified"), blank=True)
    people_assisted = models.TextField(verbose_name=_("people assisted"), blank=True, null=True)
    selection_criteria = models.TextField(
        verbose_name=_("selection criteria"), blank=True, null=True, help_text=_("Selection criteria for affected people")
    )
    community_involved = models.TextField(
        verbose_name=_("community involved"),
        blank=True,
        null=True,
        help_text=_("Community been involved in the analysis of the process"),
    )
    entity_affected = models.TextField(
        verbose_name=_("entity affected"),
        blank=True,
        null=True,
        help_text=_("Protection, gender, Inclusion affected in this process"),
    )
    women = models.IntegerField(verbose_name=_("women"), blank=True, null=True)
    men = models.IntegerField(verbose_name=_("men"), blank=True, null=True)
    girls = models.IntegerField(verbose_name=_("girls"), help_text=_("Girls under 18"), blank=True, null=True)
    boys = models.IntegerField(verbose_name=_("boys"), help_text=_("Boys under 18"), blank=True, null=True)
    disability_people_per = models.DecimalField(
        verbose_name=_("disability people per"), blank=True, null=True, max_digits=5, decimal_places=2
    )
    people_per_urban = models.DecimalField(
        verbose_name=_("people per urban"), blank=True, null=True, max_digits=5, decimal_places=2
    )
    people_per_local = models.DecimalField(
        verbose_name=_("people per local"), blank=True, null=True, max_digits=5, decimal_places=2
    )
    people_targeted_with_early_actions = models.IntegerField(
        verbose_name=_("people targeted with early actions"), blank=True, null=True
    )
    displaced_people = models.IntegerField(verbose_name=_("displaced people"), blank=True, null=True)
    operation_objective = models.TextField(
        verbose_name=_("operation objective"),
        blank=True,
        null=True,
    )
    response_strategy = models.TextField(
        verbose_name=_("response strategy"),
        blank=True,
        null=True,
    )
    planned_interventions = models.ManyToManyField(PlannedIntervention, verbose_name=_("planned intervention"), blank=True)
    is_published = models.BooleanField(
        default=False,
        verbose_name=_("Is published"),
    )
    country = models.ForeignKey(
        Country,
        verbose_name=_("country"),
        on_delete=models.CASCADE,
        help_text=_("Affected County"),
        null=True,
        blank=True,
        related_name="operational_update_country",
    )
    district = models.ManyToManyField(District, blank=True, verbose_name=_("district"))
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, verbose_name=_("users"), blank=True, related_name="user_dref_operational_update"
    )
    risk_security = models.ManyToManyField(RiskSecurity, blank=True, verbose_name=_("Risk Security"))
    risk_security_concern = models.TextField(blank=True, null=True, verbose_name=_("Risk Security Concern"))
    has_forecasted_event_materialize = models.BooleanField(
        verbose_name=_("Has Forecasted Event Materialize"), null=True, blank=True
    )
    anticipatory_to_response = models.TextField(
        verbose_name=_("Please explain how is the operation is transitioning from Anticipatory to Response"),
        null=True,
        blank=True,
    )
    specified_trigger_met = models.TextField(verbose_name=_("Specified Trigger Met"), null=True, blank=True)
    people_in_need = models.IntegerField(verbose_name=_("people in need"), blank=True, null=True)
    event_date = models.DateField(
        verbose_name=_("event date"),
        null=True,
        blank=True,
    )
    ns_respond_date = models.DateField(
        verbose_name=_("ns respond date"),
        null=True,
        blank=True,
    )
    did_ns_respond = models.BooleanField(null=True, blank=True, default=False, help_text=_("Did NS respond"))
    total_targeted_population = models.IntegerField(verbose_name=_("total targeted population"), blank=True, null=True)
    has_event_occurred = models.BooleanField(null=True, blank=True, help_text=_("Has Event occurred"))
    reporting_start_date = models.DateField(verbose_name=_("Reporting Time Start Date"), null=True, blank=True)
    reporting_end_date = models.DateField(verbose_name=_("Reporting Time End Date"), null=True, blank=True)
    human_resource = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("human resource"),
        help_text=_("how many volunteers and staff involved in the response?"),
    )
    is_surge_personnel_deployed = models.BooleanField(blank=True, null=True, verbose_name=_("Is surge personnel deployed"))
    surge_personnel_deployed = models.TextField(
        blank=True, null=True, verbose_name=_("surge personnel deployed"), help_text=_("Will a Surge personnel be deployed?")
    )
    logistic_capacity_of_ns = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("logistic capacity of ns"),
        help_text=_("what is the logistics capacity of the National Society?"),
    )
    safety_concerns = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("safety concerns"),
        help_text=_("Are there any safety/security concerns which may impact the implementation of this operation?"),
    )
    pmer = models.TextField(blank=True, null=True, verbose_name=_("pmer"), help_text=_("Does the NS have PMER capacity?"))
    communication = models.TextField(
        blank=True, null=True, verbose_name=_("organization"), help_text=_("Does the NS have Communications capacity?")
    )
    # Fields only for DrefType: LOAN
    ns_request_date = models.DateField(
        verbose_name=_("Ns request date"),
        null=True,
        blank=True,
    )
    date_of_approval = models.DateField(
        verbose_name=_("Date of Approval"),
        null=True,
        blank=True,
    )
    identified_gaps = models.TextField(
        verbose_name=_("identified gaps"),
        blank=True,
        null=True,
        help_text=_("Any identified gaps/limitations in the assessment"),
    )

    class Meta:
        verbose_name = _("Dref Operational Update")
        verbose_name_plural = _("Dref Operational Updates")

    def save(self, *args, **kwargs):
        # self.status = Dref.Status.COMPLETED if self.is_published else Dref.Status.IN_PROGRESS
        super().save(*args, **kwargs)

    @staticmethod
    def get_for(user):
        # get the user in dref
        from dref.utils import get_dref_users

        dref_users = get_dref_users()
        current_user_dref = []
        for dref in dref_users:
            for dref_user in dref["users"]:
                if user.id == dref_user:
                    current_user_dref.append(dref)
        current_user_dref_id = []
        for dref in current_user_dref:
            current_user_dref_id.append(dref["id"])
        op_update_users = DrefOperationalUpdate.objects.filter(dref__in=current_user_dref_id).distinct()
        op_update_created_by = DrefOperationalUpdate.objects.filter(created_by=user).distinct()
        union_query = op_update_users.union(op_update_created_by)
        return DrefOperationalUpdate.objects.filter(id__in=union_query.values("id")).distinct()


@reversion.register()
class DrefFinalReport(models.Model):
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=_("modified at"), default=timezone.now, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_by_dref_final_report",
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("modified by"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="modified_by_dref_final_report",
    )
    dref = models.OneToOneField(Dref, verbose_name=_("Dref"), on_delete=models.CASCADE)
    title = models.CharField(
        verbose_name=_("title"),
        null=True,
        blank=True,
        max_length=255,
    )
    title_prefix = models.CharField(verbose_name=_("title prefix"), max_length=255, null=True, blank=True)
    national_society = models.ForeignKey(
        Country,
        verbose_name=_("national_society"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="national_society_final_report",
    )
    disaster_type = models.ForeignKey(
        DisasterType, verbose_name=_("disaster type"), blank=True, null=True, on_delete=models.SET_NULL
    )
    type_of_dref = models.IntegerField(choices=Dref.DrefType.choices, verbose_name=_("dref type"), null=True, blank=True)
    type_of_onset = models.IntegerField(choices=Dref.OnsetType.choices, verbose_name=_("onset type"), null=True, blank=True)
    disaster_category = models.IntegerField(
        choices=Dref.DisasterCategory.choices, verbose_name=_("disaster category"), null=True, blank=True
    )
    status = models.IntegerField(choices=Dref.Status.choices, verbose_name=_("status"), null=True, blank=True)
    number_of_people_targeted = models.IntegerField(verbose_name=_("Number of people targeted"), blank=True, null=True)
    number_of_people_affected = models.IntegerField(verbose_name=_("number of people affected"), blank=True, null=True)
    total_dref_allocation = models.IntegerField(verbose_name=_("Total dref allocation"), null=True, blank=True)
    date_of_publication = models.DateField(verbose_name=_("Date of publication"), blank=True, null=True)
    total_operation_timeframe = models.IntegerField(verbose_name=_("Total Operation Timeframe"), null=True, blank=True)
    operation_start_date = models.DateField(verbose_name=_("Operation Start Date"), null=True, blank=True)
    appeal_code = models.CharField(verbose_name=_("appeal code"), max_length=255, null=True, blank=True)
    glide_code = models.CharField(verbose_name=_("glide number"), max_length=255, null=True, blank=True)
    ifrc_appeal_manager_name = models.CharField(
        verbose_name=_("ifrc appeal manager name"), max_length=255, null=True, blank=True
    )
    ifrc_appeal_manager_email = models.CharField(
        verbose_name=_("ifrc appeal manager email"), max_length=255, null=True, blank=True
    )
    ifrc_appeal_manager_title = models.CharField(
        verbose_name=_("ifrc appeal manager title"), max_length=255, null=True, blank=True
    )
    ifrc_appeal_manager_phone_number = models.CharField(
        verbose_name=_("ifrc appeal manager phone number"), max_length=100, null=True, blank=True
    )
    ifrc_project_manager_name = models.CharField(
        verbose_name=_("ifrc project manager name"), max_length=255, null=True, blank=True
    )
    ifrc_project_manager_email = models.CharField(
        verbose_name=_("ifrc project manager email"), max_length=255, null=True, blank=True
    )
    ifrc_project_manager_title = models.CharField(
        verbose_name=_("ifrc project manager title"), max_length=255, null=True, blank=True
    )
    ifrc_project_manager_phone_number = models.CharField(
        verbose_name=_("ifrc project manager phone number"), max_length=100, null=True, blank=True
    )
    national_society_contact_name = models.CharField(
        verbose_name=_("national society contact name"), max_length=255, null=True, blank=True
    )
    national_society_contact_email = models.CharField(
        verbose_name=_("national society contact email"), max_length=255, null=True, blank=True
    )
    national_society_contact_title = models.CharField(
        verbose_name=_("national society contact title"), max_length=255, null=True, blank=True
    )
    national_society_contact_phone_number = models.CharField(
        verbose_name=_("national society contact phone number"), max_length=100, null=True, blank=True
    )
    ifrc_emergency_name = models.CharField(verbose_name=_("ifrc emergency name"), max_length=255, null=True, blank=True)
    ifrc_emergency_email = models.CharField(verbose_name=_("ifrc emergency email"), max_length=255, null=True, blank=True)
    ifrc_emergency_title = models.CharField(verbose_name=_("ifrc emergency title"), max_length=255, null=True, blank=True)
    ifrc_emergency_phone_number = models.CharField(
        verbose_name=_("ifrc emergency phone number"), max_length=100, null=True, blank=True
    )
    media_contact_name = models.CharField(verbose_name=_("media contact name"), max_length=255, null=True, blank=True)
    media_contact_email = models.CharField(verbose_name=_("media contact email"), max_length=255, null=True, blank=True)
    media_contact_title = models.CharField(verbose_name=_("media contact title"), max_length=255, null=True, blank=True)
    media_contact_phone_number = models.CharField(
        verbose_name=_("media_contact phone number"), max_length=100, null=True, blank=True
    )
    event_map = models.ForeignKey(
        "DrefFile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("event map"),
        related_name="event_map_dref_final_report",
    )
    photos = models.ManyToManyField(
        "DrefFile", blank=True, verbose_name=_("images"), related_name="photos_dref_final_report"
    )
    assessment_report = models.ForeignKey(
        "DrefFile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Assessment Report"),
        related_name="dref_final_report_assessment_report",
    )
    event_description = models.TextField(verbose_name=_("Event description"), null=True, blank=True)
    anticipatory_actions = models.TextField(verbose_name=_("Anticipatory actions"), null=True, blank=True)
    event_scope = models.TextField(verbose_name=_("Event scope"), null=True, blank=True)
    ifrc = models.TextField(verbose_name=_("ifrc"), blank=True, null=True)
    icrc = models.TextField(verbose_name=_("icrc"), blank=True, null=True)
    partner_national_society = models.TextField(verbose_name=_("partner national society"), blank=True, null=True)
    government_requested_assistance = models.BooleanField(
        null=True, blank=True, help_text=_("Has government requested assistance")
    )
    national_authorities = models.TextField(verbose_name=_("national authorities"), blank=True, null=True)
    un_or_other_actor = models.TextField(verbose_name=_("un or other"), blank=True, null=True)
    major_coordination_mechanism = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("major coordination mechanism"),
    )
    needs_identified = models.ManyToManyField(IdentifiedNeed, verbose_name=_("needs identified"), blank=True)
    people_assisted = models.TextField(verbose_name=_("people assisted"), blank=True, null=True)
    selection_criteria = models.TextField(
        verbose_name=_("selection criteria"), blank=True, null=True, help_text=_("Selection criteria for affected people")
    )
    community_involved = models.TextField(
        verbose_name=_("community involved"),
        blank=True,
        null=True,
        help_text=_("Community been involved in the analysis of the process"),
    )
    entity_affected = models.TextField(
        verbose_name=_("entity affected"),
        blank=True,
        null=True,
        help_text=_("Protection, gender, Inclusion affected in this process"),
    )
    change_in_operational_strategy = models.BooleanField(
        verbose_name=_("Change in operational strategy"),
        default=False,
    )
    change_in_operational_strategy_text = models.TextField(
        verbose_name=_("Change in operational strategy"), null=True, blank=True
    )
    women = models.IntegerField(verbose_name=_("women"), blank=True, null=True)
    men = models.IntegerField(verbose_name=_("men"), blank=True, null=True)
    girls = models.IntegerField(verbose_name=_("girls"), help_text=_("Girls under 18"), blank=True, null=True)
    boys = models.IntegerField(verbose_name=_("boys"), help_text=_("Boys under 18"), blank=True, null=True)
    disability_people_per = models.DecimalField(
        verbose_name=_("disability people per"), blank=True, null=True, max_digits=5, decimal_places=2
    )
    people_per_urban = models.DecimalField(
        verbose_name=_("people per urban"), blank=True, null=True, max_digits=5, decimal_places=2
    )
    people_per_local = models.DecimalField(
        verbose_name=_("people per local"), blank=True, null=True, max_digits=5, decimal_places=2
    )
    people_targeted_with_early_actions = models.IntegerField(
        verbose_name=_("people targeted with early actions"), blank=True, null=True
    )
    displaced_people = models.IntegerField(verbose_name=_("displaced people"), blank=True, null=True)
    operation_objective = models.TextField(
        verbose_name=_("operation objective"),
        blank=True,
        null=True,
    )
    response_strategy = models.TextField(
        verbose_name=_("response strategy"),
        blank=True,
        null=True,
    )
    want_to_report = models.BooleanField(
        verbose_name=_("Want to report"),
        default=False,
    )
    additional_national_society_actions = models.TextField(
        verbose_name=_("Additional National Societies Actions"), null=True, blank=True
    )
    planned_interventions = models.ManyToManyField(PlannedIntervention, verbose_name=_("planned intervention"), blank=True)
    is_published = models.BooleanField(verbose_name=_("Is Published"), default=False)
    country = models.ForeignKey(
        Country,
        verbose_name=_("country"),
        on_delete=models.CASCADE,
        help_text=_("Affected County"),
        null=True,
        blank=True,
        related_name="final_report_country",
    )
    district = models.ManyToManyField(District, blank=True, verbose_name=_("district"))
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, verbose_name=_("users"), blank=True, related_name="user_dref_final_report"
    )
    images = models.ManyToManyField("DrefFile", blank=True, verbose_name=_("images"), related_name="image_dref_final_report")
    cover_image = models.ForeignKey(
        "DrefFile",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("cover image"),
        related_name="cover_image_dref_final_report",
    )
    is_there_major_coordination_mechanism = models.BooleanField(
        null=True, blank=True, help_text=_("Is there major coordinate mechanism")
    )
    major_coordination_mechanism = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("major coordination mechanism"),
    )
    total_targeted_population = models.IntegerField(verbose_name=_("total targeted population"), blank=True, null=True)
    risk_security = models.ManyToManyField(RiskSecurity, blank=True, verbose_name=_("Risk Security"))
    risk_security_concern = models.TextField(blank=True, null=True, verbose_name=_("Risk Security Concern"))
    event_date = models.DateField(
        verbose_name=_("event date"), null=True, blank=True, help_text=_("Date of event/Approximate date of impact")
    )
    national_society_actions = models.ManyToManyField(
        NationalSocietyAction, verbose_name=_("national society actions"), blank=True
    )
    people_in_need = models.IntegerField(verbose_name=_("people in need"), blank=True, null=True)
    event_text = models.TextField(verbose_name=_("event text"), blank=True, null=True)
    ns_respond_date = models.DateField(
        verbose_name=_("ns respond date"), null=True, blank=True, help_text=_("NS anticipatory actions started/NS response")
    )
    did_national_society = models.BooleanField(verbose_name=_("Did National Society"), null=True, blank=True)
    financial_report = models.ForeignKey(
        "DrefFile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("financial report"),
        related_name="financial_report_dref_final_report",
    )
    financial_report_preview = models.FileField(
        verbose_name=_("financial preview"), null=True, blank=True, upload_to="dref/images/"
    )
    num_assisted = models.IntegerField(verbose_name=_("number of assisted"), blank=True, null=True)
    has_national_society_conducted = models.BooleanField(
        verbose_name=_("Has national society conducted any intervention"), null=True, blank=True
    )
    national_society_conducted_description = models.TextField(
        verbose_name=_("National Society conducted description"), null=True, blank=True
    )
    financial_report_description = models.TextField(verbose_name=_("Financial Report Description"), null=True, blank=True)
    date_of_approval = models.DateField(
        verbose_name=_("Date of Approval"),
        null=True,
        blank=True,
    )
    main_donors = models.TextField(
        verbose_name=_("Main Donors"),
        null=True,
        blank=True
    )
    __financial_report_id = None

    class Meta:
        verbose_name = _("Dref Final Report")
        verbose_name_plural = _("Dref Final Reports")

    def save(self, *args, **kwargs):
        if self.financial_report_id and self.financial_report_id != self.__financial_report_id:
            pages = convert_from_bytes(self.financial_report.file.read())
            if len(pages) > 0:
                financial_report_preview = pages[0]  # get first page
                filename = f'preview_{self.financial_report.file.name.split("/")[0]}.png'
                temp_image = open(os.path.join("/tmp", filename), "wb")
                financial_report_preview.save(temp_image, "PNG")
                thumb_data = open(os.path.join("/tmp", filename), "rb")
                self.financial_report_preview.save(filename, thumb_data, save=False)
            else:
                raise ValidationError({"financial_report": "Sorry cannot generate preview for empty pdf"})

        self.status = Dref.Status.COMPLETED if self.is_published else Dref.Status.IN_PROGRESS
        self.__financial_report_id = self.financial_report_id
        super().save(*args, **kwargs)

    @staticmethod
    def get_for(user, is_published=False):
        from dref.utils import get_dref_users

        # get the user in dref
        dref_users = get_dref_users()
        current_user_dref = []
        for dref in dref_users:
            for dref_user in dref["users"]:
                if user.id == dref_user:
                    current_user_dref.append(dref)
        current_user_dref_id = []
        for dref in current_user_dref:
            current_user_dref_id.append(dref["id"])
        final_report_users = DrefFinalReport.objects.filter(
            dref__in=current_user_dref_id,
        ).distinct()
        final_report_created_by = DrefFinalReport.objects.filter(created_by=user).distinct()
        union_query = final_report_users.union(final_report_created_by)
        queryset = DrefFinalReport.objects.filter(id__in=union_query.values("id")).distinct()
        if is_published:
            return queryset.filter(is_published=True)
        return queryset
