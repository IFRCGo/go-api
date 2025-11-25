from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from api.models import Admin2, Country, DisasterType, District
from main.fields import SecureFileField


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

    # TYPING
    id: int
    created_by_id: int
    modified_by_id: int

    class Meta:
        abstract = True
        ordering = ["-id"]


class EAPFile(EAPBaseModel):
    file = SecureFileField(
        verbose_name=_("file"),
        upload_to="eap/files/",
        null=False,
        blank=False,
        help_text=_("Upload EAP related file."),
    )
    caption = models.CharField(max_length=225, blank=True, null=True)

    class Meta:
        verbose_name = _("eap file")
        verbose_name_plural = _("eap files")
        ordering = ["-id"]


class OperationActivity(models.Model):
    # NOTE: `timeframe` and `time_value` together represent the time span for an activity.
    # Make sure to keep them in sync.
    class TimeFrame(models.IntegerChoices):
        YEARS = 10, _("Years")
        MONTHS = 20, _("Months")
        DAYS = 30, _("Days")
        HOURS = 40, _("Hours")

    class YearsTimeFrameChoices(models.IntegerChoices):
        ONE_YEAR = 1, _("1")
        TWO_YEARS = 2, _("2")
        THREE_YEARS = 3, _("3")
        FOUR_YEARS = 4, _("4")
        FIVE_YEARS = 5, _("5")

    class MonthsTimeFrameChoices(models.IntegerChoices):
        ONE_MONTH = 1, _("1")
        TWO_MONTHS = 2, _("2")
        THREE_MONTHS = 3, _("3")
        FOUR_MONTHS = 4, _("4")
        FIVE_MONTHS = 5, _("5")
        SIX_MONTHS = 6, _("6")
        SEVEN_MONTHS = 7, _("7")
        EIGHT_MONTHS = 8, _("8")
        NINE_MONTHS = 9, _("9")
        TEN_MONTHS = 10, _("10")
        ELEVEN_MONTHS = 11, _("11")
        TWELVE_MONTHS = 12, _("12")

    class DaysTimeFrameChoices(models.IntegerChoices):
        ONE_DAY = 1, _("1")
        TWO_DAYS = 2, _("2")
        THREE_DAYS = 3, _("3")
        FOUR_DAYS = 4, _("4")
        FIVE_DAYS = 5, _("5")
        SIX_DAYS = 6, _("6")
        SEVEN_DAYS = 7, _("7")
        EIGHT_DAYS = 8, _("8")
        NINE_DAYS = 9, _("9")
        TEN_DAYS = 10, _("10")
        ELEVEN_DAYS = 11, _("11")
        TWELVE_DAYS = 12, _("12")
        THIRTEEN_DAYS = 13, _("13")
        FOURTEEN_DAYS = 14, _("14")
        FIFTEEN_DAYS = 15, _("15")
        SIXTEEN_DAYS = 16, _("16")
        SEVENTEEN_DAYS = 17, _("17")
        EIGHTEEN_DAYS = 18, _("18")
        NINETEEN_DAYS = 19, _("19")
        TWENTY_DAYS = 20, _("20")
        TWENTY_ONE_DAYS = 21, _("21")
        TWENTY_TWO_DAYS = 22, _("22")
        TWENTY_THREE_DAYS = 23, _("23")
        TWENTY_FOUR_DAYS = 24, _("24")
        TWENTY_FIVE_DAYS = 25, _("25")
        TWENTY_SIX_DAYS = 26, _("26")
        TWENTY_SEVEN_DAYS = 27, _("27")
        TWENTY_EIGHT_DAYS = 28, _("28")
        TWENTY_NINE_DAYS = 29, _("29")
        THIRTY_DAYS = 30, _("30")
        THIRTY_ONE_DAYS = 31, _("31")

    class HoursTimeFrameChoices(models.IntegerChoices):
        ZERO_TO_FIVE_HOURS = 5, _("0-5")
        FIVE_TO_TEN_HOURS = 10, _("5-10")
        TEN_TO_FIFTEEN_HOURS = 15, _("10-15")
        FIFTEEN_TO_TWENTY_HOURS = 20, _("15-20")
        TWENTY_TO_TWENTY_FIVE_HOURS = 25, _("20-25")
        TWENTY_FIVE_TO_THIRTY_HOURS = 30, _("25-30")

    activity = models.CharField(max_length=255, verbose_name=_("Activity"))
    timeframe = models.IntegerField(choices=TimeFrame.choices, verbose_name=_("Timeframe"))
    time_value = ArrayField(
        base_field=models.IntegerField(),
        verbose_name=_("Activity time span"),
    )

    class Meta:
        verbose_name = _("Operation Activity")
        verbose_name_plural = _("Operation Activities")

    def __str__(self):
        return f"{self.activity}"


# TODO(susilnem): Verify indicarors?
# class OperationIndicator(models.Model):
#     class IndicatorChoices(models.IntegerChoices):
#         INDICATOR_1 = 10, _("Indicator 1")
#         INDICATOR_2 = 20, _("Indicator 2")
#     indicator = models.IntegerField(choices=IndicatorChoices.choices, verbose_name=_("Indicator"))


class PlannedOperation(models.Model):
    class Sector(models.IntegerChoices):
        SHELTER = 101, _("Shelter")
        SETTLEMENT_AND_HOUSING = 102, _("Settlement and Housing")
        LIVELIHOODS = 103, _("Livelihoods")
        PROTECTION_GENDER_AND_INCLUSION = 104, _("Protection, Gender and Inclusion")
        HEALTH_AND_CARE = 105, _("Health and Care")
        RISK_REDUCTION = 106, _("Risk Reduction")
        CLIMATE_ADAPTATION_AND_RECOVERY = 107, _("Climate Adaptation and Recovery")
        MULTIPURPOSE_CASH = 108, _("Multipurpose Cash")
        WATER_SANITATION_AND_HYGIENE = 109, _("Water, Sanitation And Hygiene")
        WASH = 110, _("WASH")
        EDUCATION = 111, _("Education")
        MIGRATION = 112, _("Migration")
        ENVIRONMENT_SUSTAINABILITY = 113, _("Environment Sustainability")
        COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY = 114, _("Community Engagement And Accountability")

    sector = models.IntegerField(choices=Sector.choices, verbose_name=_("sector"))
    people_targeted = models.IntegerField(verbose_name=_("People Targeted"))
    budget_per_sector = models.IntegerField(verbose_name=_("Budget per sector (CHF)"))
    ap_code = models.IntegerField(verbose_name=_("AP Code"), null=True, blank=True)

    # TODO(susilnem): verify indicators?

    # indicators = models.ManyToManyField(
    #     OperationIndicator,
    #     verbose_name=_("Operation Indicators"),
    #     blank=True,
    # )

    # Activities
    readiness_activities = models.ManyToManyField(
        OperationActivity,
        verbose_name=_("Readiness Activities"),
        related_name="planned_operations_readiness_activities",
        blank=True,
    )
    prepositioning_activities = models.ManyToManyField(
        OperationActivity,
        verbose_name=_("Pre-positioning Activities"),
        related_name="planned_operations_prepositioning_activities",
        blank=True,
    )
    early_action_activities = models.ManyToManyField(
        OperationActivity,
        verbose_name=_("Early Action Activities"),
        related_name="planned_operations_early_action_activities",
        blank=True,
    )

    class Meta:
        verbose_name = _("Planned Operation")
        verbose_name_plural = _("Planned Operations")

    def __str__(self):
        return f"Planned Operation - {self.get_sector_display()}"


class EnableApproach(models.Model):
    class Approach(models.IntegerChoices):
        SECRETARIAT_SERVICES = 10, _("Secretariat Services")
        NATIONAL_SOCIETY_STRENGTHENING = 20, _("National Society Strengthening")
        PARTNERSHIP_AND_COORDINATION = 30, _("Partnership And Coordination")

    approach = models.IntegerField(choices=Approach.choices, verbose_name=_("Approach"))
    budget_per_approach = models.IntegerField(verbose_name=_("Budget per approach (CHF)"))
    ap_code = models.IntegerField(verbose_name=_("AP Code"), null=True, blank=True)
    indicator_target = models.IntegerField(verbose_name=_("Indicator Target"), null=True, blank=True)

    # TODO(susilnem): verify indicators?
    # indicators = models.ManyToManyField(
    #     OperationIndicator,
    #     verbose_name=_("Operation Indicators"),
    #     blank=True,
    # )

    # Activities
    readiness_activities = models.ManyToManyField(
        OperationActivity,
        verbose_name=_("Readiness Activities"),
        related_name="enable_approach_readiness_activities",
        blank=True,
    )
    prepositioning_activities = models.ManyToManyField(
        OperationActivity,
        verbose_name=_("Pre-positioning Activities"),
        related_name="enable_approach_prepositioning_activities",
        blank=True,
    )
    early_action_activities = models.ManyToManyField(
        OperationActivity,
        verbose_name=_("Early Action Activities"),
        related_name="enable_approach_early_action_activities",
        blank=True,
    )

    class Meta:
        verbose_name = _("Enable Approach")
        verbose_name_plural = _("Enable Approaches")

    def __str__(self):
        return f"Enable Approach - {self.get_approach_display()}"


class EAPType(models.IntegerChoices):
    """Enum representing the type of EAP."""

    FULL_EAP = 10, _("Full EAP")
    """Full EAP Application """

    SIMPLIFIED_EAP = 20, _("Simplified EAP")
    """Simplified EAP Application """


class EAPStatus(models.IntegerChoices):
    """Enum representing the status of a EAP."""

    UNDER_DEVELOPMENT = 10, _("Under Development")
    """Initial status when an EAP is being created."""

    UNDER_REVIEW = 20, _("Under Review")
    """EAP has been submitted by NS. It is under review by IFRC and/or technical partners."""

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

    ACTIVATED = 70, _("Activated")
    """EAP has been activated"""


# BASE MODEL FOR EAP
class EAPRegistration(EAPBaseModel):
    """Model representing the EAP Development Registration."""

    Status = EAPStatus

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
    disaster_type = models.ForeignKey[DisasterType, DisasterType](
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

    # Validated Budget file
    validated_budget_file = SecureFileField(
        upload_to="eap/files/validated_budgets/",
        blank=True,
        null=True,
        verbose_name=_("Validated Budget File"),
        help_text=_("Upload the validated budget file once the EAP is technically validated."),
    )

    # Review checklist
    review_checklist_file = SecureFileField(
        verbose_name=_("Review Checklist File"),
        upload_to="eap/files/",
        null=True,
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

    # STATUS timestamps
    technically_validated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("technically validated at"),
        help_text=_("Timestamp when the EAP was technically validated."),
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("approved at"),
        help_text=_("Timestamp when the EAP was approved."),
    )
    pfa_signed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("PFA signed at"),
        help_text=_("Timestamp when the PFA was signed."),
    )
    activated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("activated at"),
        help_text=_("Timestamp when the EAP was activated."),
    )

    # TYPING
    national_society_id = int
    country_id = int
    disaster_type_id = int
    id = int

    class Meta:
        verbose_name = _("Development Registration EAP")
        verbose_name_plural = _("Development Registration EAPs")
        ordering = ["-id"]

    def __str__(self):
        # NOTE: Use select_related in admin get_queryset for national_society field to avoid extra queries
        return f"EAP Development Registration - {self.national_society} - {self.disaster_type} - {self.get_eap_type_display()}"

    @property
    def has_eap_application(self) -> bool:
        """Check if the EAP Registration has an associated EAP application."""
        # TODO(susilnem): Add FULL EAP check, when model is created.
        if hasattr(self, "simplified_eap") and self.simplified_eap.exists():
            return True
        return False

    @property
    def get_status_enum(self) -> EAPStatus:
        """Get the status as an EAPStatus enum."""
        return EAPStatus(self.status)

    @property
    def get_eap_type_enum(self) -> EAPType | None:
        """Get the EAP type as an EAPType enum."""
        if self.eap_type is not None:
            return EAPType(self.eap_type)
        return None

    def update_status(self, status: EAPStatus, commit: bool = True):
        self.status = status
        if commit:
            self.save(update_fields=("status",))

    def update_eap_type(self, eap_type: EAPType, commit: bool = True):
        self.eap_type = eap_type
        if commit:
            self.save(update_fields=("eap_type",))


class SimplifiedEAP(EAPBaseModel):
    """Model representing a Simplified EAP."""

    eap_registration = models.ForeignKey[EAPRegistration, EAPRegistration](
        EAPRegistration,
        on_delete=models.CASCADE,
        verbose_name=_("EAP Development Registration"),
        related_name="simplified_eap",
    )

    cover_image = models.ForeignKey[EAPFile | None, EAPFile | None](
        EAPFile,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("cover image"),
        related_name="cover_image_simplified_eap",
    )
    seap_timeframe = models.IntegerField(
        verbose_name=_("sEAP Timeframe (Years)"),
        help_text=_("A simplified EAP has a timeframe of 2 years unless early action are activated."),
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
    hazard_impact_file = models.ManyToManyField(
        EAPFile,
        verbose_name=_("Hazard Impact Files"),
        related_name="simplified_eap_hazard_impact_files",
        blank=True,
    )

    risks_selected_protocols = models.TextField(
        verbose_name=_("Risk selected for the protocols."),
        null=True,
        blank=True,
    )

    risk_selected_protocols_file = models.ManyToManyField(
        EAPFile,
        verbose_name=_("Risk Selected Protocols Files"),
        related_name="simplified_eap_risk_selected_protocols_files",
        blank=True,
    )

    # EARLY ACTION SELECTION #
    selected_early_actions = models.TextField(
        verbose_name=_("Selected Early Actions"),
        null=True,
        blank=True,
    )
    selected_early_actions_file = models.ManyToManyField(
        EAPFile,
        verbose_name=_("Selected Early Actions Files"),
        related_name="simplified_eap_selected_early_actions_files",
        blank=True,
    )

    # EARLY ACTION INTERVENTION #
    overall_objective_intervention = models.TextField(
        verbose_name=_("Overall objective of the intervention"),
        help_text=_("Provide an objective statement that describe the main of the intervention."),
        null=True,
        blank=True,
    )

    potential_geographical_high_risk_areas = models.TextField(
        verbose_name=_("Potential geographical high-risk areas"),
        null=True,
        blank=True,
    )

    admin2 = models.ManyToManyField(
        Admin2,
        verbose_name=_("admin2"),
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
    planned_operations = models.ManyToManyField(
        PlannedOperation,
        verbose_name=_("Planned Operations"),
        blank=True,
    )

    # ENABLE APPROACHES #
    enable_approaches = models.ManyToManyField(
        EnableApproach,
        verbose_name=_("Enabling Approaches"),
        related_name="simplified_eap_enable_approaches",
        blank=True,
    )

    # CONDITION TO DELIVER AND BUDGET #

    # RISK ANALYSIS #

    early_action_capability = models.TextField(
        verbose_name=_("Experience or Capacity to implement Early Action."),
        help_text=_("Assumptions or minimum conditions needed to deliver the early actions."),
        null=True,
        blank=True,
    )
    rcrc_movement_involvement = models.TextField(
        verbose_name=_("RCRC Movement Involvement."),
        help_text=_("RCRC Movement partners, Governmental/other agencies consulted/involved."),
        null=True,
        blank=True,
    )

    # BUDGET #
    total_budget = models.IntegerField(
        verbose_name=_("Total Budget (CHF)"),
    )
    readiness_budget = models.IntegerField(
        verbose_name=_("Readiness Budget (CHF)"),
    )
    pre_positioning_budget = models.IntegerField(
        verbose_name=_("Pre-positioning Budget (CHF)"),
    )
    early_action_budget = models.IntegerField(
        verbose_name=_("Early Actions Budget (CHF)"),
    )

    # BUDGET DETAILS #
    budget_file = SecureFileField(
        verbose_name=_("Budget File"),
        upload_to="eap/simplified_eap/budget_files/",
        null=True,
        blank=True,
    )

    # Review Checklist
    updated_checklist_file = SecureFileField(
        verbose_name=_("Updated Checklist File"),
        upload_to="eap/files/",
        null=True,
        blank=True,
    )

    # NOTE: Snapshot fields
    version = models.IntegerField(
        verbose_name=_("Version"),
        help_text=_("Version identifier for the Simplified EAP."),
        default=1,
    )
    is_locked = models.BooleanField(
        verbose_name=_("Is Locked?"),
        help_text=_("Indicates whether the Simplified EAP is locked for editing."),
        default=False,
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        verbose_name=_("Parent Simplified EAP"),
        help_text=_("Reference to the parent Simplified EAP if this is a snapshot."),
        null=True,
        blank=True,
        related_name="snapshots",
    )

    # TYPING
    eap_registration_id: int
    parent_id: int
    id = int

    class Meta:
        verbose_name = _("Simplified EAP")
        verbose_name_plural = _("Simplified EAPs")
        ordering = ["-id"]

    def __str__(self):
        return f"Simplified EAP for {self.eap_registration}- version:{self.version}"

    def generate_snapshot(self):
        """
        Generate a snapshot of the given Simplified EAP.
        """

        from eap.utils import copy_model_instance

        with transaction.atomic():
            copy_model_instance(
                self,
                overrides={
                    "parent_id": self.id,
                    "version": self.version + 1,
                    "created_by_id": self.created_by_id,
                    "modified_by_id": self.modified_by_id,
                    "updated_checklist_file": None,
                },
                exclude_clone_m2m_fields=[
                    "admin2",
                ],
            )

            # Setting Parent as locked
            self.is_locked = True
            self.save(update_fields=["is_locked"])
