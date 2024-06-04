from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib.gis import admin
from django.core.exceptions import ValidationError
from reversion_compare.admin import CompareVersionAdmin

from .models import (
    Affiliation,
    BloodService,
    DelegationOffice,
    DelegationOfficeType,
    FacilityType,
    Functionality,
    GeneralMedicalService,
    HealthData,
    HospitalType,
    LocalUnit,
    LocalUnitLevel,
    LocalUnitType,
    PrimaryHCC,
    ProfessionalTrainingFacility,
    SpecializedMedicalService,
)


@admin.register(LocalUnitType)
class LocalUnitTypeAdmin(admin.ModelAdmin):
    ordering = ("code",)
    search_fields = ("name",)


@admin.register(LocalUnitLevel)
class LocalUnitLevelAdmin(admin.ModelAdmin):
    ordering = ("level",)
    search_fields = ("name",)


@admin.register(LocalUnit)
class LocalUnitAdmin(CompareVersionAdmin, admin.OSMGeoAdmin):
    search_fields = (
        "english_branch_name",
        "local_branch_name",
        "city_loc",
        "city_en",
        "country__name",
    )
    autocomplete_fields = (
        "country",
        "type",
        "level",
        "health",
    )
    list_filter = (
        AutocompleteFilterFactory("Country", "country"),
        AutocompleteFilterFactory("Type", "type"),
        AutocompleteFilterFactory("Level", "level"),
    )

    def save_model(self, request, obj, form, change):
        if obj.type.code == 1 and obj.health:
            raise ValidationError({"Can't have health data for type %s" % obj.type.code})
        super().save_model(request, obj, form, change)


@admin.register(DelegationOffice)
class DelegationOfficeAdmin(admin.OSMGeoAdmin):
    search_fields = ("name", "city", "country", "country__name")

    autocomplete_fields = ("country",)
    list_filter = (AutocompleteFilterFactory("Country", "country"),)


@admin.register(DelegationOfficeType)
class DelegationOfficeTypeAdmin(admin.ModelAdmin):
    ordering = ("code",)


@admin.register(Affiliation)
class AffiliationAdmin(admin.ModelAdmin):
    ordering = ("code",)
    search_fields = ("name",)


@admin.register(Functionality)
class FunctionalityAdmin(admin.ModelAdmin):
    ordering = ("code",)
    search_fields = ("name",)


@admin.register(FacilityType)
class FacilityTypeAdmin(admin.ModelAdmin):
    ordering = ("code",)
    search_fields = ("name",)


@admin.register(PrimaryHCC)
class PrimaryHCCAdmin(admin.ModelAdmin):
    ordering = ("code",)
    search_fields = ("name",)


@admin.register(HospitalType)
class HospitalTypeAdmin(admin.ModelAdmin):
    ordering = ("code",)
    search_fields = ("name",)


@admin.register(GeneralMedicalService)
class GeneralMedicalServiceAdmin(admin.ModelAdmin):
    ordering = ("code",)
    search_fields = ("name",)


@admin.register(SpecializedMedicalService)
class SpecializedMedicalServiceAdmin(admin.ModelAdmin):
    ordering = ("code",)
    search_fields = ("name",)


@admin.register(BloodService)
class BloodServiceAdmin(admin.ModelAdmin):
    ordering = ("code",)
    search_fields = ("name",)


@admin.register(ProfessionalTrainingFacility)
class ProfessionalTrainingFacilityAdmin(admin.ModelAdmin):
    ordering = ("code",)
    search_fields = ("name",)


@admin.register(HealthData)
class HealthDataAdmin(CompareVersionAdmin, admin.ModelAdmin):
    autocomplete_fields = [
        "affiliation",
        "functionality",
        "health_facility_type",
        "primary_health_care_center",
        "hospital_type",
        "general_medical_services",
        "specialized_medical_beyond_primary_level",
        "blood_services",
        "professional_training_facilities",
    ]

    search_fields = ("affiliation__name", "health_facility_type__name")
    list_filter = (
        AutocompleteFilterFactory("Country", "health_data__country"),
        AutocompleteFilterFactory("Affiliation", "affiliation"),
        AutocompleteFilterFactory("Functionality", "functionality"),
        AutocompleteFilterFactory("FacilityType", "health_facility_type"),
        AutocompleteFilterFactory("PrimaryHCC", "primary_health_care_center"),
        AutocompleteFilterFactory("GeneralMedicalService", "general_medical_services"),
        AutocompleteFilterFactory("SpecializedMedicalService", "specialized_medical_beyond_primary_level"),
        AutocompleteFilterFactory("BloodService", "blood_services"),
        AutocompleteFilterFactory("ProfessionalTrainingFacility", "professional_training_facilities"),
    )
