import os

from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.templatetags.static import static


from api.models import Country, VisibilityChoices


class Affiliation(models.Model):
    code = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99)])
    name = models.CharField(
        max_length=100, verbose_name=_('Name'))

    def __str__(self):
        return f'{self.name} ({self.code})'


class Functionality(models.Model):
    code = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99)])
    name = models.CharField(
        max_length=100, verbose_name=_('Name'))

    def __str__(self):
        return f'{self.name} ({self.code})'

    class Meta:
        verbose_name = 'Functionality'
        verbose_name_plural = 'Functionalities'


class FacilityType(models.Model):
    code = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99)]
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name')
    )

    def __str__(self):
        return f'{self.name} ({self.code})'

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
        return request.build_absolute_uri(static(os.path.join("images/local_units/health_facility_type", code_static_map.get(code, "favicon.png"))))


class PrimaryHCC(models.Model):
    code = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99)])
    name = models.CharField(
        max_length=100, verbose_name=_('Name'))

    def __str__(self):
        return f'{self.name} ({self.code})'

    class Meta:
        verbose_name = 'Primary Health Care Center'
        verbose_name_plural = 'Primary Health Care Centers'


class HospitalType(models.Model):
    code = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99)])
    name = models.CharField(
        max_length=100, verbose_name=_('Name'))

    def __str__(self):
        return f'{self.name} ({self.code})'


class GeneralMedicalService(models.Model):
    code = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99)])
    name = models.CharField(
        max_length=100, verbose_name=_('Name'))

    def __str__(self):
        return f'{self.name} ({self.code})'


class SpecializedMedicalService(models.Model):
    code = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99)])
    name = models.CharField(
        max_length=100, verbose_name=_('Name'))

    def __str__(self):
        return f'{self.name} ({self.code})'


class BloodService(models.Model):
    code = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99)])
    name = models.CharField(
        max_length=100, verbose_name=_('Name'))

    def __str__(self):
        return f'{self.name} ({self.code})'


class ProfessionalTrainingFacility(models.Model):
    code = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(99)])
    name = models.CharField(
        max_length=100, verbose_name=_('Name'))

    def __str__(self):
        return f'{self.name} ({self.code})'

    class Meta:
        verbose_name = 'Professional Training Facility'
        verbose_name_plural = 'Professional Training Facilities'


class HealthData(models.Model):
    affiliation = models.ForeignKey(
        Affiliation,
        on_delete=models.CASCADE,
        verbose_name=_('Affiliation'),
        related_name='health_affiliation'
    )
    other_affiliation = models.CharField(
        max_length=300, verbose_name=_('Other Affiliation'),
        null=True, blank=True
    )
    functionality = models.ForeignKey(
        Functionality,
        on_delete=models.CASCADE,
        verbose_name=_('Functionality'),
        related_name='health_functionality',
    )
    focal_point_email = models.EmailField(
        max_length=90, verbose_name=_('Focal point email'), blank=True, null=True
    )
    focal_point_phone_number = models.CharField(
        max_length=90, verbose_name=_('Focal point phone number'), blank=True, null=True
    )
    focal_point_position = models.CharField(
        max_length=90, verbose_name=_('Focal point position'), blank=True, null=True
    )
    health_facility_type = models.ForeignKey(
        FacilityType,
        on_delete=models.CASCADE,
        verbose_name=_('Health facility type'),
        related_name='health_facility_type'
    )
    other_facility_type = models.CharField(
        max_length=300, verbose_name=_('Other facility type'), blank=True, null=True
    )
    primary_health_care_center = models.ForeignKey(
        PrimaryHCC,
        on_delete=models.SET_NULL,
        verbose_name=_('Primary Health Care Center'),
        related_name='primary_health_care_center',
        null=True,
    )
    speciality = models.CharField(
        max_length=200, verbose_name=_('Speciality'), blank=True, null=True
    )
    hospital_type = models.ForeignKey(
        HospitalType,
        on_delete=models.SET_NULL,
        verbose_name=_('Hospital type'),
        related_name='hospital_type',
        null=True,
    )
    is_teaching_hospital = models.BooleanField(
        verbose_name=_('Is teaching hospital?'), default=False
    )
    is_in_patient_capacity = models.BooleanField(
        verbose_name=_('Has in-patient capacity?'), default=False
    )
    is_isolation_rooms_wards = models.BooleanField(
        verbose_name=_('Has isolation rooms wards?'), default=False
    )
    maximum_capacity = models.IntegerField(
        verbose_name=_('Maximum Capacity'), blank=True, null=True
    )
    number_of_isolation_rooms = models.IntegerField(
        verbose_name=_('Number of isolation rooms'), blank=True, null=True
    )
    is_warehousing = models.BooleanField(
        verbose_name=_('Has warehousing?'), default=False
    )
    is_cold_chain = models.BooleanField(
        verbose_name=_('Has cold chain?'), default=False
    )
    ambulance_type_a = models.IntegerField(
        verbose_name=_('Ambulance Type A'), blank=True, null=True
    )
    ambulance_type_b = models.IntegerField(
        verbose_name=_('Ambulance Type B'), blank=True, null=True
    )
    ambulance_type_c = models.IntegerField(
        verbose_name=_('Ambulance Type C'), blank=True, null=True
    )
    general_medical_services = models.ManyToManyField(
        GeneralMedicalService,
        related_name='general_medical_services',
        verbose_name=_('General medical services'),
        blank=True,
    )
    specialized_medical_beyond_primary_level = models.ManyToManyField(
        SpecializedMedicalService,
        related_name='specialized_medical_beyond_primary_level',
        verbose_name=_('Specialized medical beyond primary level'),
        blank=True,
    )
    other_services = models.CharField(
        max_length=300, verbose_name=_('Other Services'), blank=True, null=True
    )
    blood_services = models.ManyToManyField(
        BloodService,
        related_name='blood_services',
        verbose_name=_('Blood Services'),
        blank=True,
    )
    professional_training_facilities = models.ManyToManyField(
        ProfessionalTrainingFacility,
        related_name='professional_training_facilities',
        verbose_name=_('Professional Training Facilities'),
        blank=True,
    )
    total_number_of_human_resource = models.IntegerField(
        verbose_name=_('Total number of Human Resource'), blank=True, null=True
    )
    general_practitioner = models.IntegerField(
        verbose_name=_('General Practitioner'), blank=True, null=True
    )
    specialist = models.IntegerField(
        verbose_name=_('Specialist'), blank=True, null=True
    )
    residents_doctor = models.IntegerField(
        verbose_name=_('Residents Doctor'), blank=True, null=True
    )
    nurse = models.IntegerField(verbose_name=_('Nurse'), blank=True, null=True)
    dentist = models.IntegerField(verbose_name=_('Dentist'), blank=True, null=True)
    nursing_aid = models.IntegerField(
        verbose_name=_('Nursing Aid'), blank=True, null=True
    )
    midwife = models.IntegerField(verbose_name=_('Midwife'), blank=True, null=True)
    other_medical_heal = models.BooleanField(
        verbose_name=_('Other medical heal'), default=False
    )
    other_profiles = models.CharField(
        max_length=200, verbose_name=_('Other Profiles'), blank=True, null=True
    )
    feedback = models.CharField(
        max_length=500, verbose_name=_('Feedback'), blank=True, null=True
    )

    def __str__(self):
        return f'{self.affiliation} – {self.id}'

    class Meta:
        verbose_name = 'Health Data'
        verbose_name_plural = 'Health Data'


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
    colour = models.CharField(
        verbose_name=_('Local Unit Colour'),
        null=True, blank=True,
        max_length=50
    )

    def __str__(self):
        return f'{self.name} ({self.code})'

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
        return request.build_absolute_uri(static(os.path.join("images/local_units/local_unit_type", code_static_map.get(code, "favicon.png"))))


class LocalUnitLevel(models.Model):
    level = models.IntegerField(
        verbose_name=_('Coverage'),
        validators=[
            MaxValueValidator(10),
            MinValueValidator(0)
        ]
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name')
    )

    class Meta:
        verbose_name = _("Local unit coverage")
        verbose_name_plural = _("Local unit coverages")

    def __str__(self):
        return f'{self.name} ({self.level})'


class LocalUnit(models.Model):
    # added to track health local unit data (Table B)
    health = models.ForeignKey(
        HealthData, on_delete=models.SET_NULL, verbose_name=_('Health Data'),
        related_name='health_data', null=True, blank=True
    )
    country = models.ForeignKey(
        Country, on_delete=models.CASCADE, verbose_name=_('Country'),
        related_name='local_unit_country',
    )
    type = models.ForeignKey(
        LocalUnitType, on_delete=models.CASCADE, verbose_name=_('Type'),
        related_name='local_unit_type'
    )
    subtype = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Subtype')
    )
    level = models.ForeignKey(
        LocalUnitLevel, on_delete=models.SET_NULL, verbose_name=_('Coverage'),
        related_name='local_unit_level', null=True
    )
    local_branch_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Branch name in local language')
    )
    english_branch_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
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
    )
    draft = models.BooleanField(default=False, verbose_name=_('Draft'))
    validated = models.BooleanField(default=False, verbose_name=_('Validated'))
    visibility = models.IntegerField(
        choices=VisibilityChoices.choices, verbose_name=_('visibility'),
        default=2)  # 2:IFRC
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
    postcode = models.CharField(
        max_length=10,
        null=True,
        verbose_name=_('Postal code'),
        blank=True
    )
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
    location = models.PointField(srid=4326, help_text="Local Unit Location")

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
    visibility = models.IntegerField(
        choices=VisibilityChoices.choices, verbose_name=_('visibility'),
        default=2)  # 2:IFRC
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
