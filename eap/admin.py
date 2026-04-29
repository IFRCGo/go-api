from django.contrib import admin
from django.db import transaction

from eap.models import (
    EAPFile,
    EAPRegistration,
    EAPType,
    EmailRecipient,
    FullEAP,
    KeyActor,
    SimplifiedEAP,
)


@admin.register(EAPFile)
class EAPFileAdmin(admin.ModelAdmin):
    search_fields = ("caption",)
    list_select_related = True
    autocomplete_fields = (
        "created_by",
        "modified_by",
    )


@admin.register(EmailRecipient)
class EmailRecipientAdmin(admin.ModelAdmin):
    list_select_related = True
    search_fields = ("email",)
    list_display = (
        "type",
        "title",
        "region",
        "email",
    )
    list_filter = (
        "type",
        "region",
    )
    autocomplete_fields = ("region",)

    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(EAPRegistration)
class DevelopmentRegistrationEAPAdmin(admin.ModelAdmin):
    list_select_related = True
    search_fields = (
        "national_society__name",
        "country__name",
        "disaster_type__name",
    )
    readonly_fields = ("summary_file",)
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
    actions = [
        "regenerate_full_eap_summary",
    ]

    def regenerate_full_eap_summary(self, request, queryset):
        """
        Admin action to regenerate EAP summary PDF files for selected EAP registrations.
        """
        from eap.tasks import generate_eap_summary_pdf

        for eap_registration in queryset:
            if eap_registration.get_eap_type_enum != EAPType.FULL_EAP:
                continue
            transaction.on_commit(lambda: generate_eap_summary_pdf.delay(eap_registration.id))

    regenerate_full_eap_summary.short_description = "Regenerate EAP summary PDF files for Full EAP"

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
    list_display = ("simplifed_eap_application", "eap_registration", "version", "is_locked")
    autocomplete_fields = (
        "eap_registration",
        "created_by",
        "modified_by",
        "admin2",
        "partners",
    )
    readonly_fields = (
        "cover_image",
        "partner_contacts",
        "hazard_impact_images",
        "risk_selected_protocols_images",
        "selected_early_actions_images",
        "planned_operations",
        "enabling_approaches",
        "parent",
        "is_locked",
        "version",
    )
    actions = [
        "regenerate_diff_pdf_file",
        "regenerate_export_eap_file",
    ]

    def regenerate_export_eap_file(self, request, queryset):
        """
        Admin action to regenerate EAP export files for selected Simplified EAP.
        """
        from eap.tasks import generate_export_eap_pdf

        for simplified_eap in queryset:
            transaction.on_commit(
                lambda: generate_export_eap_pdf.delay(
                    eap_registration_id=simplified_eap.eap_registration.id,
                    version=simplified_eap.version,
                )
            )

    regenerate_export_eap_file.short_description = "Regenerate EAP export PDF files for selected Simplified EAPs"

    def regenerate_diff_pdf_file(self, request, queryset):
        """
        Admin action to regenerate EAP diff PDF files for selected Simplified EAP.
        """
        from eap.tasks import generate_export_diff_pdf

        for simplified_eap in queryset:
            transaction.on_commit(
                lambda: generate_export_diff_pdf.delay(
                    eap_registration_id=simplified_eap.eap_registration.id,
                    version=simplified_eap.version,
                )
            )

    regenerate_diff_pdf_file.short_description = "Regenerate EAP diff PDF files for selected Simplified EAPs"

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
                "partners",
                "partner_contacts",
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
    list_display = ("full_eap_application", "eap_registration", "version", "is_locked")
    autocomplete_fields = (
        "eap_registration",
        "created_by",
        "modified_by",
        "admin2",
        "partners",
    )
    readonly_fields = (
        "partner_contacts",
        "cover_image",
        "planned_operations",
        "enabling_approaches",
        "planned_operations",
        "hazard_selection_images",
        "theory_of_change_table_file",
        "exposed_element_and_vulnerability_factor_images",
        "prioritized_impact_images",
        "risk_analysis_relevant_files",
        "forecast_selection_images",
        "definition_and_justification_impact_level_images",
        "identification_of_the_intervention_area_images",
        "trigger_model_relevant_files",
        "early_action_selection_process_images",
        "evidence_base_relevant_files",
        "early_action_implementation_images",
        "trigger_activation_system_images",
        "activation_process_relevant_files",
        "meal_relevant_files",
        "capacity_relevant_files",
        "forecast_table_file",
    )
    actions = [
        "regenerate_diff_pdf_file",
        "regenerate_export_eap_file",
    ]

    def regenerate_export_eap_file(self, request, queryset):
        """
        Admin action to regenerate EAP export PDF files for selected EAP registrations.
        """
        from eap.tasks import generate_export_eap_pdf

        for full_eap in queryset:
            transaction.on_commit(
                lambda: generate_export_eap_pdf.delay(
                    eap_registration_id=full_eap.eap_registration.id,
                    version=full_eap.version,
                )
            )

    regenerate_export_eap_file.short_description = "Regenerate EAP export PDF files for selected Full EAPs"

    def regenerate_diff_pdf_file(self, request, queryset):
        """
        Admin action to regenerate EAP diff PDF files for selected EAP registrations.
        """
        from eap.tasks import generate_export_diff_pdf

        for full_eap in queryset:
            transaction.on_commit(
                lambda: generate_export_diff_pdf.delay(
                    eap_registration_id=full_eap.eap_registration.id,
                    version=full_eap.version,
                )
            )

    regenerate_diff_pdf_file.short_description = "Regenerate EAP diff PDF files for selected Full EAPs"

    def full_eap_application(self, obj):
        return f"{obj.eap_registration.national_society.society_name} - {obj.eap_registration.disaster_type.name}"

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
                "partners",
                "partner_contacts",
                "key_actors",
                "risk_analysis_source_of_information",
                "trigger_statement_source_of_information",
                "trigger_model_source_of_information",
                "evidence_base_source_of_information",
                "activation_process_source_of_information",
            )
        )
