from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from api.models import Country, DisasterType, District


class EarlyActionIndicator(models.Model):
    class IndicatorChoices(models.TextChoices):  # TODO these indicator are yet to be provided by client.
        INDICATOR_1 = "indicator_1", _("Indicator 1")
        INDICATOR_2 = "indicator_2", _("Indicator 2")

    indicator = models.CharField(
        IndicatorChoices.choices, max_length=255, default=IndicatorChoices.INDICATOR_1, null=True, blank=True
    )
    indicator_value = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = _("Early Action Indicator")
        verbose_name_plural = _("Early Actions Indicators")

    def __str__(self):
        return f"{self.indicator}"


class EarlyAction(models.Model):
    class Sector(models.IntegerChoices):
        SHELTER_HOUSING_AND_SETTLEMENTS = 0, _("Shelter, Housing And Settlements")
        LIVELIHOODS = 1, _("Livelihoods")
        MULTI_PURPOSE_CASH = 2, _("Multi-purpose Cash")
        HEALTH_AND_CARE = 3, _("Health And Care")
        WATER_SANITATION_AND_HYGIENE = 4, _("Water, Sanitation And Hygiene")
        PROTECTION_GENDER_AND_INCLUSION = 5, _("Protection, Gender And Inclusion")
        EDUCATION = 6, _("Education")
        MIGRATION = 7, _("Migration")
        RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY = 8, _("Risk Reduction, Climate Adaptation And Recovery")
        COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY = 9, _("Community Engagement And Accountability")
        ENVIRONMENT_SUSTAINABILITY = 10, _("Environment Sustainability")
        SHELTER_CLUSTER_COORDINATION = 11, _("Shelter Cluster Coordination")

    sector = models.IntegerField(choices=Sector.choices, verbose_name=_("sector"))
    budget_per_sector = models.IntegerField(verbose_name=_("Budget per sector (CHF)"), null=True, blank=True)
    indicators = models.ManyToManyField(EarlyActionIndicator, verbose_name=_("Indicators"), blank=True)

    prioritized_risk = models.TextField(verbose_name=_("Prioritized risk"), null=True, blank=True)
    targeted_people = models.IntegerField(
        verbose_name=_("Targeted people"),
        null=True,
        blank=True,
    )

    readiness_activities = models.TextField(verbose_name=_("Readiness Activities"), null=True, blank=True)
    prepositioning_activities = models.TextField(verbose_name=_("Pre-positioning Activities"), null=True, blank=True)

    class Meta:
        verbose_name = _("Early Action")
        verbose_name_plural = _("Early Actions")

    def __str__(self):
        return f"{self.sector}"


class EAP(models.Model):
    class Status(models.TextChoices):  # TODO some more status choices are to be expected by client.
        APPROVED = "approved", _("Approved")
        IN_PROCESS = "in_process", _("In Process")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Created by"),
        related_name="eap_created_by",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Modified by"),
        related_name="eap_modified_by",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(verbose_name=_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=_("updated at"), auto_now=True)

    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, verbose_name=_("Country"), related_name="eap_country", null=True
    )
    district = models.ForeignKey(
        District,
        on_delete=models.SET_NULL,
        verbose_name=_("Provience/Region"),
        related_name="eap_district",
        null=True,
        blank=True,
    )
    disaster_type = models.ForeignKey(
        DisasterType, on_delete=models.SET_NULL, verbose_name=_("Disaster Type"), related_name="eap_disaster_type", null=True
    )
    eap_number = models.CharField(max_length=50, verbose_name=_("EAP Number"))
    approval_date = models.DateField(verbose_name=_("Date of EAP Approval"))
    status = models.CharField(max_length=255, choices=Status.choices, default=Status.IN_PROCESS, verbose_name=_("EAP Status"))
    operational_timeframe = models.IntegerField(verbose_name=_("Operational Timeframe (Months)"))
    lead_time = models.IntegerField(verbose_name=_("Lead Time"))
    eap_timeframe = models.IntegerField(verbose_name=_("EAP Timeframe (Years)"))
    num_of_people = models.IntegerField(verbose_name=_("Number of People Targeted"))
    total_budget = models.IntegerField(verbose_name=_("Total Budget (CHF)"))
    readiness_budget = models.IntegerField(verbose_name=_("Readiness Budget (CHF)"), null=True, blank=True)
    pre_positioning_budget = models.IntegerField(verbose_name=_("Pre-positioning Budget (CHF)"), null=True, blank=True)
    early_action_budget = models.IntegerField(verbose_name=_("Early Actions Budget (CHF)"), null=True, blank=True)
    trigger_statement = models.TextField(verbose_name=_("Trigger Statement (Threshold for Activation)"))
    overview = models.TextField(verbose_name=_("EAP Overview"))
    document = models.FileField(verbose_name=_("EAP Documents"), upload_to="eap/documents/", null=True, blank=True)
    early_actions = models.ManyToManyField(EarlyAction, verbose_name=_("Early actions"), blank=True)
    originator_name = models.CharField(verbose_name=_("Originator Name"), max_length=255, null=True, blank=True)
    originator_title = models.CharField(verbose_name=_("Originator Title"), max_length=255, null=True, blank=True)
    originator_email = models.CharField(verbose_name=_("Originator Email"), max_length=255, null=True, blank=True)
    originator_phone = models.CharField(verbose_name=_("Origingator Phone"), max_length=255, null=True, blank=True)

    nsc_name = models.CharField(verbose_name=_("National Society Contact Name"), max_length=255, null=True, blank=True)
    nsc_title = models.CharField(verbose_name=_("National Society Contact Title"), max_length=255, null=True, blank=True)
    nsc_email = models.CharField(verbose_name=_("National Society Contact Email"), max_length=255, null=True, blank=True)
    nsc_phone = models.CharField(verbose_name=_("National Society Contact Phone"), max_length=255, null=True, blank=True)

    ifrc_focal_name = models.CharField(verbose_name=_("Ifrc Focal Point Name"), max_length=255, null=True, blank=True)
    ifrc_focal_title = models.CharField(verbose_name=_("Ifrc Focal Point Title"), max_length=255, null=True, blank=True)
    ifrc_focal_email = models.CharField(verbose_name=_("Ifrc Focal Point Email"), max_length=255, null=True, blank=True)
    ifrc_focal_phone = models.CharField(verbose_name=_("Ifrc Focal Point Phone"), max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = _("Early Action Protocol")
        verbose_name_plural = _("Early Actions Protocols")

    def __str__(self):
        return f"{self.eap_number}"


class EAPPartner(models.Model):
    eap = models.ForeignKey(EAP, on_delete=models.CASCADE, related_name="eap_partner", verbose_name=_("EAP"))
    name = models.CharField(max_length=255, verbose_name=_("Name"), null=True, blank=True)
    url = models.URLField(verbose_name=_("URL"), null=True, blank=True)

    class Meta:
        verbose_name = _("EAP Partner")
        verbose_name_plural = _("EAP Partners")

    def __str__(self):
        return f"{self.name}"


class EAPReference(models.Model):
    eap = models.ForeignKey(EAP, on_delete=models.CASCADE, related_name="eap_reference", verbose_name=_("EAP"))
    source = models.CharField(max_length=255, verbose_name=_("Name"), null=True, blank=True)
    url = models.URLField(verbose_name=_("URL"), null=True, blank=True)

    class Meta:
        verbose_name = _("EAP Reference")
        verbose_name_plural = _("EAP References")

    def __str__(self):
        return f"{self.source}"


class Action(models.Model):
    early_action = models.ForeignKey(
        EarlyAction, on_delete=models.CASCADE, related_name="action", verbose_name=_("Early Actions")
    )
    early_act = models.TextField(verbose_name=_("Early Actions"), null=True, blank=True)

    class Meta:
        verbose_name = _("Action")
        verbose_name_plural = _("Actions")

    def __str__(self):
        return f"{self.id}"


# --- Early Action Protocol --- ##


class EAPType(models.IntegerChoices):
    FULL_EAP = 10, _("Full EAP")
    SIMPLIFIED_EAP = 20, _("Simplified EAP")


class EAPStatus(models.IntegerChoices):
    """Enum representing the status of a EAP."""

    UNDER_DEVELOPMENT = 10, _("Under Development")
    """Initial status when an EAP is being created."""

    UNDER_REVIEW = 20, _("Under Review")
    """ EAP has been submitted by NS. It is under review by IFRC and/or technical partners."""

    NS_ADDRESSING_COMMENTS = 30, _("NS Addressing Comments")
    """NS is addressing comments provided during the review process.
    IFRC has to upload review checklist.
    EAP can be changed to UNDER_REVIEW once comments have been addressed.
    """

    TECHNICALLY_VALIDATED = 40, _("Technically Validated")
    """EAP has been technically validated by IFRC and/or technical partners.
    """

    APPROVED = 50, _("Approved")
    """IFRC has to upload validated budget file.
    Cannot be changed back to previous statuses.
    """

    PFA_SIGNED = 60, _("PFA Signed")
    """EAP should be APPROVED before changing to this status."""


class EAPBaseModel(models.Model):
    """Base model for EAP models to include common fields."""

    created_at = models.DateTimeField(
        verbose_name=_("created at"),
        auto_now_add=True,
    )
    modified_at = models.DateTimeField(
        verbose_name=_("modified at"),
        auto_now=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        on_delete=models.PROTECT,
        related_name="%(class)s_created_by",
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("modified by"),
        on_delete=models.PROTECT,
        related_name="%(class)s_modified_by",
    )

    class Meta:
        abstract = True


# BASE MODEL FOR EAP
class EAPRegistration(EAPBaseModel):
    """Model representing the EAP Development Registration."""

    # National Society
    national_society = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        verbose_name=_("National Society (NS)"),
        help_text=_("Select National Society that is planning to apply for the EAP"),
        related_name="development_registration_eap_national_society",
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        verbose_name=_("Country"),
        help_text=_("The country will be pre-populated based on the NS selection, but can be adapted as needed."),
        related_name="development_registration_eap_country",
    )

    # Disaster
    disaster_type = models.ForeignKey(
        DisasterType,
        verbose_name=("Disaster Type"),
        on_delete=models.PROTECT,
        help_text=_("Select the disaster type for which the EAP is needed"),
    )
    eap_type = models.IntegerField(
        choices=EAPType.choices,
        verbose_name=_("EAP Type"),
        help_text=_("Select the type of EAP."),
        null=True,
        blank=True,
    )
    status = models.IntegerField(
        choices=EAPStatus.choices,
        verbose_name=_("EAP Status"),
        default=EAPStatus.UNDER_DEVELOPMENT,
        help_text=_("Select the current status of the EAP development process."),
    )
    # TODO(susilnem): Verify this field?
    is_active = models.BooleanField(
        verbose_name=_("Is Active"),
        help_text=_("Indicates whether this EAP development registration is active."),
        default=False,
    )

    expected_submission_time = models.DateField(
        verbose_name=_("Expected submission time"),
        help_text=_(
            "Include the propose time of submission, accounting for the time it will take to deliver the application."
            "Leave blank if not sure."
        ),
        blank=True,
        null=True,
    )

    partners = models.ManyToManyField(
        Country,
        verbose_name=_("Partners"),
        help_text=_("Select any partner NS involved in the EAP development."),
        related_name="development_registration_eap_partners",
        blank=True,
    )

    # Contacts
    # National Society
    national_society_contact_name = models.CharField(
        verbose_name=_("national society contact name"), max_length=255, null=True, blank=True
    )
    national_society_contact_title = models.CharField(
        verbose_name=_("national society contact title"), max_length=255, null=True, blank=True
    )
    national_society_contact_email = models.CharField(
        verbose_name=_("national society contact email"), max_length=255, null=True, blank=True
    )
    national_society_contact_phone_number = models.CharField(
        verbose_name=_("national society contact phone number"), max_length=100, null=True, blank=True
    )

    # IFRC Contact
    ifrc_contact_name = models.CharField(verbose_name=_("IFRC contact name "), max_length=255, null=True, blank=True)
    ifrc_contact_email = models.CharField(verbose_name=_("IFRC contact email"), max_length=255, null=True, blank=True)
    ifrc_contact_title = models.CharField(verbose_name=_("IFRC contact title"), max_length=255, null=True, blank=True)
    ifrc_contact_phone_number = models.CharField(
        verbose_name=_("IFRC contact phone number"), max_length=100, null=True, blank=True
    )

    # DREF Focal Point
    dref_focal_point_name = models.CharField(verbose_name=_("dref focal point name"), max_length=255, null=True, blank=True)
    dref_focal_point_email = models.CharField(verbose_name=_("Dref focal point email"), max_length=255, null=True, blank=True)
    dref_focal_point_title = models.CharField(verbose_name=_("Dref focal point title"), max_length=255, null=True, blank=True)
    dref_focal_point_phone_number = models.CharField(
        verbose_name=_("Dref focal point phone number"), max_length=100, null=True, blank=True
    )

    class Meta:
        verbose_name = _("Development Registration EAP")
        verbose_name_plural = _("Development Registration EAPs")

    def __str__(self):
        # NOTE: Use select_related in admin get_queryset for national_society field to avoid extra queries
        return f"EAP Development Registration - {self.national_society} - {self.disaster_type} - {self.get_eap_type_display()}"


class SimplifiedEAP(EAPBaseModel):
    """Model representing a Simplified EAP."""

    eap_registration = models.OneToOneField(
        EAPRegistration,
        on_delete=models.CASCADE,
        verbose_name=_("EAP Development Registration"),
        related_name="simplified_eap",
    )

    # Contacts
    # National Society
    national_society_contact_name = models.CharField(
        verbose_name=_("national society contact name"), max_length=255, null=True, blank=True
    )
    national_society_contact_title = models.CharField(
        verbose_name=_("national society contact title"), max_length=255, null=True, blank=True
    )
    national_society_contact_email = models.CharField(
        verbose_name=_("national society contact email"), max_length=255, null=True, blank=True
    )
    national_society_contact_phone_number = models.CharField(
        verbose_name=_("national society contact phone number"), max_length=100, null=True, blank=True
    )

    # Partners NS
    partner_ns_name = models.CharField(verbose_name=_("Partner NS name"), max_length=255, null=True, blank=True)
    partner_ns_email = models.CharField(verbose_name=_("Partner NS email"), max_length=255, null=True, blank=True)
    partner_ns_title = models.CharField(verbose_name=_("Partner NS title"), max_length=255, null=True, blank=True)
    partner_ns_phone_number = models.CharField(verbose_name=_("Partner NS phone number"), max_length=100, null=True, blank=True)

    # Delegations
    ifrc_delegation_focal_point_name = models.CharField(
        verbose_name=_("IFRC delegation focal point name"), max_length=255, null=True, blank=True
    )
    ifrc_delegation_focal_point_email = models.CharField(
        verbose_name=_("IFRC delegation focal point email"), max_length=255, null=True, blank=True
    )
    ifrc_delegation_focal_point_title = models.CharField(
        verbose_name=_("IFRC delegation focal point title"), max_length=255, null=True, blank=True
    )
    ifrc_delegation_focal_point_phone_number = models.CharField(
        verbose_name=_("IFRC delegation focal point phone number"), max_length=100, null=True, blank=True
    )

    ifrc_head_of_delegation_name = models.CharField(
        verbose_name=_("IFRC head of delegation name"), max_length=255, null=True, blank=True
    )
    ifrc_head_of_delegation_email = models.CharField(
        verbose_name=_("IFRC head of delegation email"), max_length=255, null=True, blank=True
    )
    ifrc_head_of_delegation_title = models.CharField(
        verbose_name=_("IFRC head of delegation title"), max_length=255, null=True, blank=True
    )
    ifrc_head_of_delegation_phone_number = models.CharField(
        verbose_name=_("IFRC head of delegation phone number"), max_length=100, null=True, blank=True
    )

    # Regional and Global
    # DREF Focal Point
    dref_focal_point_name = models.CharField(verbose_name=_("dref focal point name"), max_length=255, null=True, blank=True)
    dref_focal_point_email = models.CharField(verbose_name=_("Dref focal point email"), max_length=255, null=True, blank=True)
    dref_focal_point_title = models.CharField(verbose_name=_("Dref focal point title"), max_length=255, null=True, blank=True)
    dref_focal_point_phone_number = models.CharField(
        verbose_name=_("Dref focal point phone number"), max_length=100, null=True, blank=True
    )

    # Regional
    ifrc_regional_focal_point_name = models.CharField(
        verbose_name=_("IFRC regional focal point name"), max_length=255, null=True, blank=True
    )
    ifrc_regional_focal_point_email = models.CharField(
        verbose_name=_("IFRC regional focal point email"), max_length=255, null=True, blank=True
    )
    ifrc_regional_focal_point_title = models.CharField(
        verbose_name=_("IFRC regional focal point title"), max_length=255, null=True, blank=True
    )
    ifrc_regional_focal_point_phone_number = models.CharField(
        verbose_name=_("IFRC regional focal point phone number"), max_length=100, null=True, blank=True
    )

    # Regional Ops Manager
    ifrc_regional_ops_manager_name = models.CharField(
        verbose_name=_("IFRC regional ops manager name"), max_length=255, null=True, blank=True
    )
    ifrc_regional_ops_manager_email = models.CharField(
        verbose_name=_("IFRC regional ops manager email"), max_length=255, null=True, blank=True
    )
    ifrc_regional_ops_manager_title = models.CharField(
        verbose_name=_("IFRC regional ops manager title"), max_length=255, null=True, blank=True
    )
    ifrc_regional_ops_manager_phone_number = models.CharField(
        verbose_name=_("IFRC regional ops manager phone number"), max_length=100, null=True, blank=True
    )

    # Regional Head DCC
    ifrc_regional_head_dcc_name = models.CharField(
        verbose_name=_("IFRC regional head of DCC name"), max_length=255, null=True, blank=True
    )
    ifrc_regional_head_dcc_email = models.CharField(
        verbose_name=_("IFRC regional head of DCC email"), max_length=255, null=True, blank=True
    )
    ifrc_regional_head_dcc_title = models.CharField(
        verbose_name=_("IFRC regional head of DCC title"), max_length=255, null=True, blank=True
    )
    ifrc_regional_head_dcc_phone_number = models.CharField(
        verbose_name=_("IFRC regional head of DCC phone number"), max_length=100, null=True, blank=True
    )

    # Global Ops Manager
    ifrc_global_ops_coordinator_name = models.CharField(
        verbose_name=_("IFRC global ops coordinator name"), max_length=255, null=True, blank=True
    )
    ifrc_global_ops_coordinator_email = models.CharField(
        verbose_name=_("IFRC global ops coordinator email"), max_length=255, null=True, blank=True
    )
    ifrc_global_ops_coordinator_title = models.CharField(
        verbose_name=_("IFRC global ops coordinator title"), max_length=255, null=True, blank=True
    )
    ifrc_global_ops_coordinator_phone_number = models.CharField(
        verbose_name=_("IFRC global ops coordinator phone number"), max_length=100, null=True, blank=True
    )

    # RISK ANALYSIS and EARLY ACTION SELECTION #

    # RISK ANALYSIS #
    prioritized_hazard_and_impact = models.TextField(
        verbose_name=_("Prioritized Hazard and its  historical impact."),
        null=True,
        blank=True,
    )
    # TODO(susilnem): Add image max 5

    risks_selected_protocols = models.TextField(
        verbose_name=_("Risk selected for the protocols."),
        null=True,
        blank=True,
    )
    # TODO(susilnem): Add image max 5

    # EARLY ACTION SELECTION #
    selected_early_actions = models.TextField(
        verbose_name=_("Selected Early Actions"),
        null=True,
        blank=True,
    )
    # TODO(susilnem): Add image max 5

    # EARLY ACTION INTERVENTION #
    overall_objective_intervention = models.TextField(
        verbose_name=_("Overall objective of the intervention"),
        help_text=_("Provide an objective statement that describe the main of the intervention."),
        null=True,
        blank=True,
    )

    # TODO(susilnem): Discuss and add selections regions
    potential_geographical_high_risk_areas = models.TextField(
        verbose_name=_("Potential geographical high-risk areas"),
        null=True,
        blank=True,
    )
    people_targeted = models.IntegerField(
        verbose_name=_("People Targeted."),
        null=True,
        blank=True,
    )
    assisted_through_operation = models.TextField(
        verbose_name=_("Assisted through the operation"),
        null=True,
        blank=True,
    )
    selection_criteria = models.TextField(
        verbose_name=_("Selection Criteria."),
        help_text=_("Explain the selection criteria for who will be targeted"),
        null=True,
        blank=True,
    )

    trigger_statement = models.TextField(
        verbose_name=_("Trigger Statement"),
        null=True,
        blank=True,
    )

    seap_lead_time = models.IntegerField(
        verbose_name=_("sEAP Lead Time (Hours)"),
        null=True,
        blank=True,
    )
    operational_timeframe = models.IntegerField(
        verbose_name=_("Operational Timeframe (Months)"),
        null=True,
        blank=True,
    )
    trigger_threshold_justification = models.TextField(
        verbose_name=_("Trigger Threshold Justification"),
        help_text=_("Explain how the trigger were set and provide information"),
        null=True,
        blank=True,
    )
    next_step_towards_full_eap = models.TextField(
        verbose_name=_("Next Steps towards Full EAP"),
    )

    # PLANNED OPEATIONS #
    # TODO(susilnem): continue

    class Meta:
        verbose_name = _("Simplified EAP")
        verbose_name_plural = _("Simplified EAPs")

    def __str__(self):
        return f"Simplified EAP for {self.eap_registration}"
