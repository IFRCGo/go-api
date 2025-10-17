from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin

from lang.admin import TranslationAdmin

from .models import (
    Dref,
    DrefFile,
    DrefFinalReport,
    DrefOperationalUpdate,
    IdentifiedNeed,
    NationalSocietyAction,
    PlannedIntervention,
    ProposedAction,
    RiskSecurity,
    SourceInformation,
)


class ReadOnlyMixin:
    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


@admin.register(NationalSocietyAction)
class NationalSocietyActionAdmin(ReadOnlyMixin, admin.ModelAdmin):

    def descr(self, obj):
        return obj.description.replace("-", "")[:190]

    def related_dref(self, obj):
        return "/".join([dref.title for dref in obj.dref_set.all()])

    search_fields = ["title", "description"]
    list_display = ["id", "title", "descr", "related_dref"]
    list_filter = ["title"]


@admin.register(RiskSecurity)
class RiskSecurityAdmin(ReadOnlyMixin, admin.ModelAdmin):
    search_fields = ["risk", "mitigation"]


@admin.register(IdentifiedNeed)
class IdentifiedNeedAdmin(ReadOnlyMixin, admin.ModelAdmin):
    search_fields = ["title"]


@admin.register(PlannedIntervention)
class PlannedInterventionAdmin(ReadOnlyMixin, admin.ModelAdmin):
    search_fields = ["title"]


@admin.register(DrefFile)
class DrefFileAdmin(admin.ModelAdmin):
    search_fields = ("file",)


@admin.register(SourceInformation)
class SourceInformationAdmin(admin.ModelAdmin):
    search_fields = ("source_name",)


@admin.register(Dref)
class DrefAdmin(CompareVersionAdmin, TranslationAdmin, admin.ModelAdmin):
    search_fields = ("title", "appeal_code")
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
        "risk_security",
        "proposed_action",
    )
    readonly_fields = ("starting_language",)

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
                "supporting_document",
            )
            .prefetch_related("planned_interventions", "needs_identified", "national_society_actions", "users", "risk_security")
        )


@admin.register(DrefOperationalUpdate)
class DrefOperationalUpdateAdmin(CompareVersionAdmin, TranslationAdmin, admin.ModelAdmin):
    list_display = ("title", "national_society", "disaster_type")
    search_fields = ("title", "national_society__name", "appeal_code")
    autocomplete_fields = (
        "national_society",
        "disaster_type",
        "images",
        "users",
        "event_map",
        "images",
        "budget_file",
        "cover_image",
        "created_by",
        "modified_by",
        "dref",
        "assessment_report",
        "photos",
        "national_society_actions",
        "needs_identified",
        "planned_interventions",
        "country",
        "district",
        "risk_security",
    )
    readonly_fields = ("starting_language",)
    list_filter = ["dref"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "national_society",
                "disaster_type",
                "event_map",
                "budget_file",
                "cover_image",
                "created_by",
                "modified_by",
                "dref",
                "assessment_report",
                "country",
            )
            .prefetch_related(
                "planned_interventions",
                "needs_identified",
                "national_society_actions",
                "users",
                "district",
                "photos",
                "images",
                "district",
            )
        )


@admin.register(DrefFinalReport)
class DrefFinalReportAdmin(CompareVersionAdmin, TranslationAdmin, admin.ModelAdmin):
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
        "risk_security",
        "needs_identified",
        "planned_interventions",
        "users",
        "national_society_actions",
        "source_information",
    )
    readonly_fields = ("starting_language",)
    list_filter = ["dref"]
    search_fields = ["title", "national_society__name", "appeal_code"]

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
                "dref",
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

    # NOTE: If the Dref Final report is unpublished, set Dref related to it as active
    def save_model(self, request, obj, form, change):
        if obj.status != Dref.Status.APPROVED and obj.dref:
            obj.dref.is_active = True
            obj.dref.save(update_fields=["is_active"])
        super().save_model(request, obj, form, change)


@admin.register(ProposedAction)
class ProposedActionAdmin(ReadOnlyMixin, admin.ModelAdmin):
    search_fields = ["action"]
