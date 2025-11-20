from django.contrib import admin

from eap.models import EAPRegistration, FullEAP, KeyActor, SimplifiedEAP


@admin.register(EAPRegistration)
class DevelopmentRegistrationEAPAdmin(admin.ModelAdmin):
    list_select_related = True
    search_fields = (
        "national_society__name",
        "country__name",
        "disaster_type__name",
    )
    list_filter = ("eap_type",)
    list_display = (
        "national_society_name",
        "country",
        "eap_type",
        "disaster_type",
    )
    autocomplete_fields = (
        "national_society",
        "disaster_type",
        "partners",
        "created_by",
        "modified_by",
    )

    def national_society_name(self, obj):
        return obj.national_society.society_name

    national_society_name.short_description = "National Society (NS)"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "national_society",
                "country",
                "disaster_type",
                "created_by",
                "modified_by",
            )
            .prefetch_related(
                "partners",
            )
        )


@admin.register(SimplifiedEAP)
class SimplifiedEAPAdmin(admin.ModelAdmin):
    list_select_related = True
    search_fields = (
        "eap_registration__country__name",
        "eap_registration__disaster_type__name",
    )
    list_display = ("simplifed_eap_application", "version", "is_locked")
    autocomplete_fields = (
        "eap_registration",
        "created_by",
        "modified_by",
        "admin2",
    )
    readonly_fields = (
        "cover_image",
        "hazard_impact_images",
        "risk_selected_protocols_images",
        "selected_early_actions_images",
        "planned_operations",
        "enable_approaches",
        "parent",
        "is_locked",
        "version",
    )

    def simplifed_eap_application(self, obj):
        return f"{obj.eap_registration.national_society.society_name} - {obj.eap_registration.disaster_type.name}"

    simplifed_eap_application.short_description = "Simplified EAP Application"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "created_by",
                "modified_by",
                "eap_registration__country",
                "eap_registration__national_society",
                "eap_registration__disaster_type",
            )
            .prefetch_related(
                "admin2",
            )
        )


@admin.register(KeyActor)
class KeyActorAdmin(admin.ModelAdmin):
    list_display = ("national_society",)


@admin.register(FullEAP)
class FullEAPAdmin(admin.ModelAdmin):
    list_select_related = True
    search_fields = (
        "eap_registration__country__name",
        "eap_registration__disaster_type__name",
    )
    list_display = ("eap_registration",)
    autocomplete_fields = (
        "eap_registration",
        "created_by",
        "modified_by",
        "admin2",
    )
    readonly_fields = (
        "cover_image",
        "planned_operations",
        "enable_approaches",
        "planned_operations",
        "hazard_files",
        "exposed_element_and_vulnerability_factor_files",
        "prioritized_impact_file",
        "risk_analysis_relevant_file",
        "forecast_selection_files",
        "definition_and_justification_impact_level_files",
        "identification_of_the_intervention_area_files",
        "trigger_model_relevant_file",
        "early_action_selection_process_file",
        "evidence_base_file",
        "early_action_implementation_files",
        "trigger_activation_system_files",
        "activation_process_relevant_files",
        "meal_files",
        "capacity_relevant_files",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "created_by",
                "modified_by",
                "cover_image",
                "eap_registration__country",
                "eap_registration__national_society",
                "eap_registration__disaster_type",
            )
            .prefetch_related(
                "admin2",
                "key_actors",
                "risk_analysis_source_of_information",
                "trigger_statement_source_of_information",
                "trigger_model_source_of_information",
                "evidence_base_source_of_information",
                "activation_process_source_of_information",
            )
        )
