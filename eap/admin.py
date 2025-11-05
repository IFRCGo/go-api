from django.contrib import admin

from eap.models import EAPRegistration


@admin.register(EAPRegistration)
class DevelopmentRegistrationEAPAdmin(admin.ModelAdmin):
    list_select_related = True
    search_fields = (
        "national_society__name",
        "country__name",
        "disaster_type__name",
    )
    list_filter = ("eap_type", "disaster_type", "national_society")
    list_display = (
        "national_society",
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
