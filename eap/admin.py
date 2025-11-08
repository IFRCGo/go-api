from django.contrib import admin

from eap.models import EAPRegistration, SimplifiedEAP


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
    list_display = ("eap_registration",)
    autocomplete_fields = (
        "eap_registration",
        "created_by",
        "modified_by",
        "admin2",
    )
    readonly_fields = (
        "cover_image",
        "hazard_impact_file",
        "risk_selected_protocols_file",
        "selected_early_actions_file",
        "planned_operations",
        "enable_approaches",
    )

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
