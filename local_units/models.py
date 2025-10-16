import os

import reversion
from django.conf import settings
from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import UniqueConstraint
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from api.models import Country, VisibilityChoices
from main.fields import SecureFileField


class Affiliation(models.Model):
    code = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)])
    name = models.CharField(max_length=100, verbose_name=_("Name"))

    def __str__(self):
        return f"{self.name} ({self.code})"


class Functionality(models.Model):
    code = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)])
    name = models.CharField(max_length=100, verbose_name=_("Name"))

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name = "Functionality"
        verbose_name_plural = "Functionalities"


class FacilityType(models.Model):
    code = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)])
    name = models.CharField(max_length=100, verbose_name=_("Name"))

    def __str__(self):
        return f"{self.name} ({self.code})"

    @staticmethod
    def get_image_map(code, request):
        code_static_map = {
            1: "ambulance.png",
            2: "blood-center.png",
            3: "hospital.png",
            4: "pharmacy.png",
            5: "primary-health-care.png",
            6: "residential-facility.png",
            7: "training-facility.png",
            8: "specialized-services.png",
            9: "other.png",
        }
        return request.build_absolute_uri(
            static(os.path.join("images/local_units/health_facility_type", code_static_map.get(code, "favicon.png")))
        )


class PrimaryHCC(models.Model):
    code = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)])
    name = models.CharField(max_length=100, verbose_name=_("Name"))

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name = "Primary Health Care Center"
        verbose_name_plural = "Primary Health Care Centers"


class HospitalType(models.Model):
    code = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)])
    name = models.CharField(max_length=100, verbose_name=_("Name"))

    def __str__(self):
        return f"{self.name} ({self.code})"


class GeneralMedicalService(models.Model):
    code = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)])
    name = models.CharField(max_length=100, verbose_name=_("Name"))

    def __str__(self):
        return f"{self.name} ({self.code})"


class SpecializedMedicalService(models.Model):
    code = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)])
    name = models.CharField(max_length=100, verbose_name=_("Name"))

    def __str__(self):
        return f"{self.name} ({self.code})"


class BloodService(models.Model):
    code = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)])
    name = models.CharField(max_length=100, verbose_name=_("Name"))

    def __str__(self):
        return f"{self.name} ({self.code})"


class ProfessionalTrainingFacility(models.Model):
    code = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)])
    name = models.CharField(max_length=100, verbose_name=_("Name"))

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name = "Professional Training Facility"
        verbose_name_plural = "Professional Training Facilities"


class OtherProfile(models.Model):
    position = models.CharField(verbose_name=_("Position"))
    number = models.PositiveIntegerField(verbose_name=_("Number"))

    def __str__(self):
        return f"{self.position}"

    class Meta:
        verbose_name = "Other Profile"
        verbose_name_plural = "Other Profiles"


@reversion.register()
class HealthData(models.Model):
    created_at = models.DateTimeField(verbose_name=_("Created at"), auto_now=True)
    modified_at = models.DateTimeField(verbose_name=_("Modified at"), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_by_health_data",
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("modified by"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="modified_by_health_data",
    )
    affiliation = models.ForeignKey(
        Affiliation, on_delete=models.CASCADE, verbose_name=_("Affiliation"), related_name="health_affiliation"
    )
    other_affiliation = models.TextField(verbose_name=_("Other Affiliation"), null=True, blank=True)
    functionality = models.ForeignKey(
        Functionality,
        on_delete=models.CASCADE,
        verbose_name=_("Functionality"),
        related_name="health_functionality",
    )
    focal_point_email = models.EmailField(max_length=255, verbose_name=_("Focal point email"), blank=True, null=True)
    focal_point_phone_number = models.CharField(max_length=255, verbose_name=_("Focal point phone number"), blank=True, null=True)
    focal_point_position = models.CharField(max_length=255, verbose_name=_("Focal point position"), blank=True, null=True)
    health_facility_type = models.ForeignKey(
        FacilityType, on_delete=models.CASCADE, verbose_name=_("Health facility type"), related_name="health_facility_type"
    )
    other_facility_type = models.TextField(verbose_name=_("Other facility type"), blank=True, null=True)
    primary_health_care_center = models.ForeignKey(
        PrimaryHCC,
        on_delete=models.SET_NULL,
        verbose_name=_("Primary Health Care Center"),
        related_name="primary_health_care_center",
        null=True,
    )
    speciality = models.CharField(max_length=255, verbose_name=_("Speciality"), blank=True, null=True)
    hospital_type = models.ForeignKey(
        HospitalType,
        on_delete=models.SET_NULL,
        verbose_name=_("Hospital type"),
        related_name="hospital_type",
        null=True,
    )
    is_teaching_hospital = models.BooleanField(
        verbose_name=_("Is teaching hospital?"),
        null=True,
        blank=True,
    )
    is_in_patient_capacity = models.BooleanField(
        verbose_name=_("Has in-patient capacity?"),
        null=True,
        blank=True,
    )
    is_isolation_rooms_wards = models.BooleanField(
        verbose_name=_("Has isolation rooms wards?"),
        null=True,
        blank=True,
    )
    other_training_facilities = models.TextField(verbose_name="Other Training Facilities", blank=True, null=True)
    maximum_capacity = models.IntegerField(verbose_name=_("Maximum Capacity"), blank=True, null=True)
    number_of_isolation_rooms = models.IntegerField(verbose_name=_("Number of isolation rooms"), blank=True, null=True)
    is_warehousing = models.BooleanField(
        verbose_name=_("Has warehousing?"),
        null=True,
        blank=True,
    )
    is_cold_chain = models.BooleanField(
        verbose_name=_("Has cold chain?"),
        null=True,
        blank=True,
    )
    ambulance_type_a = models.IntegerField(verbose_name=_("Ambulance Type A"), blank=True, null=True)
    ambulance_type_b = models.IntegerField(verbose_name=_("Ambulance Type B"), blank=True, null=True)
    ambulance_type_c = models.IntegerField(verbose_name=_("Ambulance Type C"), blank=True, null=True)
    general_medical_services = models.ManyToManyField(
        GeneralMedicalService,
        related_name="general_medical_services",
        verbose_name=_("General medical services"),
        blank=True,
    )
    specialized_medical_beyond_primary_level = models.ManyToManyField(
        SpecializedMedicalService,
        related_name="specialized_medical_beyond_primary_level",
        verbose_name=_("Specialized medical beyond primary level"),
        blank=True,
    )
    other_services = models.TextField(verbose_name=_("Other Services"), blank=True, null=True)
    blood_services = models.ManyToManyField(
        BloodService,
        related_name="blood_services",
        verbose_name=_("Blood Services"),
        blank=True,
    )
    professional_training_facilities = models.ManyToManyField(
        ProfessionalTrainingFacility,
        related_name="professional_training_facilities",
        verbose_name=_("Professional Training Facilities"),
        blank=True,
    )
    total_number_of_human_resource = models.IntegerField(verbose_name=_("Total number of Human Resource"), blank=True, null=True)
    general_practitioner = models.IntegerField(verbose_name=_("General Practitioner"), blank=True, null=True)
    specialist = models.IntegerField(verbose_name=_("Specialist"), blank=True, null=True)
    residents_doctor = models.IntegerField(verbose_name=_("Residents Doctor"), blank=True, null=True)
    nurse = models.IntegerField(verbose_name=_("Nurse"), blank=True, null=True)
    dentist = models.IntegerField(verbose_name=_("Dentist"), blank=True, null=True)
    nursing_aid = models.IntegerField(verbose_name=_("Nursing Aid"), blank=True, null=True)
    midwife = models.IntegerField(verbose_name=_("Midwife"), blank=True, null=True)
    pharmacists = models.IntegerField(verbose_name=_("Pharmacists"), blank=True, null=True)
    other_medical_heal = models.BooleanField(
        verbose_name=_("Other medical heal"),
        null=True,
        blank=True,
    )
    other_profiles = models.ManyToManyField(
        OtherProfile,
        related_name="health_data_other_profile",
        verbose_name=_("Other Profiles"),
        blank=True,
    )
    feedback = models.TextField(verbose_name=_("Feedback"), blank=True, null=True)

    def __str__(self):
        return f"{self.affiliation} – {self.id}"

    class Meta:
        verbose_name = "Health Data"
        verbose_name_plural = "Health Data"


class LocalUnitType(models.Model):
    code = models.IntegerField(verbose_name=_("Type Code"), validators=[MaxValueValidator(10), MinValueValidator(0)])
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    colour = models.CharField(verbose_name=_("Local Unit Colour"), null=True, blank=True, max_length=50)

    def __str__(self):
        return f"{self.name} ({self.code})"

    @staticmethod
    def get_image_map(code, request):
        code_static_map = {
            1: "Admin.png",
            2: "Healthcare.png",
            3: "Emergency response.png",
            4: "Hum Assistance Centres.png",
            5: "Training & Education.png",
            6: "Other.png",
        }
        return request.build_absolute_uri(
            static(os.path.join("images/local_units/local_unit_type", code_static_map.get(code, "favicon.png")))
        )


class LocalUnitLevel(models.Model):
    level = models.IntegerField(verbose_name=_("Coverage"), validators=[MaxValueValidator(10), MinValueValidator(0)])
    name = models.CharField(max_length=100, verbose_name=_("Name"))

    class Meta:
        verbose_name = _("Local unit coverage")
        verbose_name_plural = _("Local unit coverages")

    def __str__(self):
        return f"{self.name} ({self.level})"


class LocalUnitBulkUpload(models.Model):
    class Status(models.IntegerChoices):
        SUCCESS = 1, _("Success")
        FAILED = 2, _("Failed")
        PENDING = 3, _("Pending")

    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        verbose_name=_("Country"),
        related_name="bulk_upload_local_unit_country",
    )
    local_unit_type = models.ForeignKey(
        LocalUnitType, on_delete=models.CASCADE, verbose_name=_("Local Unit Type"), related_name="bulk_upload_local_unit_type"
    )
    success_count = models.PositiveIntegerField(default=0, verbose_name=_("Success Count"))
    failed_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Failed Count"),
    )
    file_size = models.PositiveIntegerField(default=0, verbose_name=_("File Size"))
    status = models.IntegerField(
        choices=Status.choices,
        verbose_name=_("Status"),
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Triggered By"),
        related_name="triggered_by_bulk_upload",
    )
    triggered_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Triggered At"))
    file = SecureFileField(upload_to="local_unit/bulk_uploads/", verbose_name=_("Uploaded File"))
    error_file = SecureFileField(
        upload_to="local_unit/bulk_upload_errors/",
        null=True,
        blank=True,
        verbose_name=_("Error File"),
    )
    error_message = models.TextField(null=True, blank=True, verbose_name=_("Error Message"))
    # Type hints
    pk: int
    country_id: int
    local_unit_type_id: int
    triggered_by_id: int

    def __str__(self):
        return f"Bulk Upload - {self.country_id} - ({self.local_unit_type_id}) - {self.status}"

    def update_status(self, status: Status, commit: bool = True) -> None:
        """
        Update the status of the bulk upload.
        """
        self.status = status
        if commit:
            self.save(update_fields=["status"])


class Validator(models.IntegerChoices):
    LOCAL = 1, _("Local")
    REGIONAL = 2, _("Regional")
    GLOBAL = 3, _("Global")


@reversion.register(follow=("health",))
class LocalUnit(models.Model):
    class DeprecateReason(models.IntegerChoices):
        NON_EXISTENT = 1, _("Non-existent local unit")
        INCORRECTLY_ADDED = 2, _("Incorrectly added local unit")
        SECURITY_CONCERNS = 3, _("Security concerns")
        OTHER = 4, _("Other")

    class Status(models.IntegerChoices):
        # NOTE: Tracks the status of LocalUnit entries to manage validation workflows.
        VALIDATED = 1, "Validated"
        UNVALIDATED = 2, "Unvalidated"
        PENDING_EDIT_VALIDATION = 3, "Pending Edit Validation"
        EXTERNALLY_MANAGED = 4, "Externally Managed"

    # added to track health local unit data (Table B)
    health = models.ForeignKey(
        HealthData, on_delete=models.SET_NULL, verbose_name=_("Health Data"), related_name="health_data", null=True, blank=True
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        verbose_name=_("Country"),
        related_name="local_unit_country",
    )
    type = models.ForeignKey(LocalUnitType, on_delete=models.CASCADE, verbose_name=_("Type"), related_name="local_unit_type")
    subtype = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("Subtype"))
    level = models.ForeignKey(
        LocalUnitLevel, on_delete=models.SET_NULL, verbose_name=_("Coverage"), related_name="local_unit_level", null=True
    )
    local_branch_name = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Branch name in local language"))
    english_branch_name = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Branch name in English"))
    created_at = models.DateTimeField(verbose_name=_("Created at"), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=_("Modified at"), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_by_local_unit",
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("modified by"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="modified_by_local_unit",
    )
    date_of_data = models.DateField(
        verbose_name=_("Date of data collection"),
        auto_now=False,
    )
    draft = models.BooleanField(default=False, verbose_name=_("Draft"))
    status = models.IntegerField(
        choices=Status.choices, default=Status.UNVALIDATED, verbose_name=_("Validation Status")
    )  # NOTE: Replacement of validated field for better status tracking
    visibility = models.IntegerField(choices=VisibilityChoices.choices, verbose_name=_("visibility"), default=2)  # 2:IFRC
    source_en = models.CharField(max_length=500, blank=True, null=True, verbose_name=_("Source in Local Language"))
    source_loc = models.CharField(max_length=500, blank=True, null=True, verbose_name=_("Source in English"))
    address_loc = models.CharField(max_length=500, blank=True, null=True, verbose_name=_("Address in local language"))
    address_en = models.CharField(max_length=500, blank=True, null=True, verbose_name=_("Address in English"))
    city_loc = models.CharField(
        max_length=255,
        verbose_name=_("City in local language"),
        null=True,
        blank=True,
    )
    city_en = models.CharField(
        max_length=255,
        verbose_name=_("City in English"),
        null=True,
        blank=True,
    )
    focal_person_loc = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Focal person for local language"))
    focal_person_en = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Focal person for English"))
    postcode = models.CharField(max_length=10, null=True, verbose_name=_("Postal code"), blank=True)
    phone = models.CharField(max_length=30, blank=True, null=True, verbose_name=_("Telephone"))
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name=_("Email"))
    link = models.URLField(max_length=255, blank=True, null=True, verbose_name=_("Social link"))
    location = models.PointField(srid=4326, help_text="Local Unit Location")
    is_deprecated = models.BooleanField(default=False, verbose_name=_("Is deprecated?"))
    deprecated_reason = models.IntegerField(
        choices=DeprecateReason.choices, verbose_name=_("deprecated reason"), blank=True, null=True
    )
    deprecated_reason_overview = models.TextField(
        verbose_name=_("Explain the reason why the local unit is being deleted"), blank=True, null=True
    )
    update_reason_overview = models.TextField(
        verbose_name=_("Explain the reason why the local unit is being updated"), blank=True, null=True
    )
    last_sent_validator_type = models.IntegerField(
        choices=Validator.choices,
        verbose_name=_("Last email sent validator type"),
        default=Validator.LOCAL,
    )
    bulk_upload = models.ForeignKey(
        LocalUnitBulkUpload,
        verbose_name=_("Bulk Upload Local Unit"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="bulk_upload_local_unit",
    )

    def __str__(self):
        branch_name = self.local_branch_name or self.english_branch_name
        return f"{branch_name} ({self.country.name})"

    def location_json(self):
        """
        Returns location in JSON format
        """
        return {
            "lat": self.location.y,
            "lng": self.location.x,
        }


class ExternallyManagedLocalUnit(models.Model):
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        verbose_name=_("Country"),
        related_name="externally_managed_local_unit_country",
    )
    local_unit_type = models.ForeignKey(
        LocalUnitType, on_delete=models.CASCADE, verbose_name=_("Type"), related_name="externally_managed_local_unit_type"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_external_local_units"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="updated_external_local_units"
    )
    updated_at = models.DateTimeField(auto_now=True)
    enabled = models.BooleanField(default=False)

    class Meta:
        constraints = [UniqueConstraint(fields=["country", "local_unit_type"], name="unique_country_local_unit_type")]


class LocalUnitChangeRequest(models.Model):

    class Status(models.IntegerChoices):
        PENDING = 1, _("Pending")
        APPROVED = 2, _("Approved")
        REVERT = 3, _("Revert")

    local_unit = models.ForeignKey(
        LocalUnit, on_delete=models.CASCADE, verbose_name=_("Local Unit"), related_name="local_unit_change_request"
    )
    previous_data = models.JSONField(verbose_name=_("Previous data"), default=dict)
    status = models.IntegerField(choices=Status.choices, verbose_name=_("status"), default=Status.PENDING)
    current_validator = models.IntegerField(
        choices=Validator.choices, verbose_name=_("Current validator"), default=Validator.LOCAL
    )

    # NOTE: triggered_by is the user who created the request
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("triggered by"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="tiggered_by_local_unit",
    )
    triggered_at = models.DateTimeField(verbose_name=_("Triggered at"), auto_now_add=True)

    # NOTE: updated_by is the user who approved/revert the request
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("updated by"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="updated_by_local_unit",
    )
    updated_at = models.DateTimeField(verbose_name=_("Updated at"), auto_now=True)
    rejected_data = models.JSONField(verbose_name=_("Rejected data"), default=dict)
    rejected_reason = models.TextField(verbose_name=_("Rejected reason"), blank=True, null=True)

    class Meta:
        ordering = ("id",)

    def __str__(self):
        # NOTE: N+1, make sure to use select_related
        branch_name = self.local_unit.local_branch_name or self.local_unit.english_branch_name
        return f"{branch_name}-Change Request-{self.id}"


class DelegationOfficeType(models.Model):
    code = models.IntegerField(verbose_name=_("Type Code"), validators=[MaxValueValidator(10), MinValueValidator(0)])
    name = models.CharField(max_length=100, verbose_name=_("Name"))

    def __str__(self):
        return f"{self.name} ({self.code})"


class DelegationOffice(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    dotype = models.ForeignKey(
        DelegationOfficeType, on_delete=models.SET_NULL, verbose_name=_("Type"), related_name="delegation_office_type", null=True
    )
    city = models.CharField(max_length=500, blank=True, null=True, verbose_name=_("City"))
    address = models.CharField(max_length=500, blank=True, null=True, verbose_name=_("Address"))
    postcode = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Postal code"))
    location = models.PointField()
    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, verbose_name=_("Country"), related_name="delegation_office_country", null=True
    )
    society_url = models.URLField(max_length=255, blank=True, null=True, verbose_name=_("URL of national society"))
    url_ifrc = models.URLField(max_length=255, blank=True, null=True, verbose_name=_("URL on IFRC webpage"))
    hod_first_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("HOD first name"))
    hod_last_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("HOD last name"))
    hod_mobile_number = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("HOD mobile number"))
    hod_email = models.EmailField(max_length=255, blank=True, null=True, verbose_name=_("HOD Email"))
    assistant_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Assistant name"))
    assistant_email = models.EmailField(max_length=255, blank=True, null=True, verbose_name=_("Assistant email"))
    is_ns_same_location = models.BooleanField(default=False, verbose_name=_("NS on same location?"))
    is_multiple_ifrc_offices = models.BooleanField(default=False, verbose_name=_("Multiple IFRC offices?"))
    visibility = models.IntegerField(choices=VisibilityChoices.choices, verbose_name=_("visibility"), default=2)  # 2:IFRC
    created_at = models.DateTimeField(verbose_name=_("Created at"), auto_now=True)
    modified_at = models.DateTimeField(verbose_name=_("Modified at"), auto_now=True)
    date_of_data = models.DateField(
        verbose_name=_("Date of data collection"),
        auto_now=False,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.name} ({self.country.name})"
