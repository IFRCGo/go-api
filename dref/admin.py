from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin

from lang.admin import TranslationAdmin
from .models import (
    Dref,
    DrefFile,
    DrefOperationalUpdate,
    DrefFinalReport,
    NationalSocietyAction,
    IdentifiedNeed,
    PlannedIntervention,
)


class ReadOnlyMixin():
    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


@admin.register(NationalSocietyAction)
class NationalSocietyActionAdmin(
    ReadOnlyMixin,
    admin.ModelAdmin
):
    search_fields = ['title']


@admin.register(IdentifiedNeed)
class IdentifiedNeedAdmin(
    ReadOnlyMixin,
    admin.ModelAdmin
):
    search_fields = ['title']


@admin.register(PlannedIntervention)
class PlannedInterventionAdmin(
    ReadOnlyMixin,
    admin.ModelAdmin
):
    search_fields = ['title']


@admin.register(DrefFile)
class DrefFileAdmin(admin.ModelAdmin):
    search_fields = ("file",)


@admin.register(Dref)
class DrefAdmin(
    CompareVersionAdmin,
    TranslationAdmin,
    admin.ModelAdmin
):
    search_fields = ("title",)
    list_display = (
        "title",
        "national_society",
        "disaster_type",
        "ns_request_date",
        "submission_to_geneva",
        "status",
    )
    autocomplete_fields = (
        "national_society",
        "disaster_type",
        "created_by",
        "modified_by",
        "event_map",
        "assessment_report",
        "country",
        "district",
        "images",
        "cover_image",
        "users",
        "field_report",
        "supporting_document",
        "national_society_actions",
        "needs_identified",
        "planned_interventions",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "created_by",
                "modified_by",
                "national_society",
                "disaster_type",
                "event_map",
                "cover_image",
                "country",
                "field_report",
                "supporting_document"
            )
            .prefetch_related(
                "planned_interventions",
                "needs_identified",
                "national_society_actions",
                "users",
                "risk_security"
            )
        )


@admin.register(DrefOperationalUpdate)
class DrefOperationalUpdateAdmin(CompareVersionAdmin, TranslationAdmin, admin.ModelAdmin):
    list_display = ("title", "national_society", "disaster_type")
    autocomplete_fields = (
        "national_society",
        "disaster_type",
        "images",
        "users",
        "event_map",
        "images",
        "budget_file",
        "cover_image",
    )
    list_filter = ["dref"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "created_by",
                "modified_by",
                "national_society",
                "disaster_type",
                "event_map",
                "cover_image",
                "country",
                "budget_file",
            )
            .prefetch_related(
                "planned_interventions",
                "needs_identified",
                "national_society_actions",
                "users"
            )
        )


@admin.register(DrefFinalReport)
class DrefFinalReportAdmin(
    CompareVersionAdmin,
    TranslationAdmin,
    admin.ModelAdmin
):
    list_display = ("title", "national_society", "disaster_type")
    autocomplete_fields = (
        "national_society",
        "disaster_type",
        "photos",
        "dref",
        "created_by",
        "modified_by",
        "event_map",
        "photos",
        "assessment_report",
        "country",
        "district",
        "images",
        "cover_image",
        "financial_report",
    )
    list_filter = ["dref"]
    search_fields = ["title", "national_society__name"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "created_by",
                "modified_by",
                "national_society",
                "disaster_type",
                "event_map",
                "cover_image",
                "country",
                "assessment_report",
                "dref"
            )
            .prefetch_related(
                "planned_interventions",
                "needs_identified",
                "national_society_actions",
                "users",
                "dref__planned_interventions",
                "dref__national_society_actions",
                "dref__needs_identified",
            )
        )
