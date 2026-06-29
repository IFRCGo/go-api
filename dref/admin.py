from django.contrib import admin, messages
from reversion_compare.admin import CompareVersionAdmin

from api.utils import get_model_name
from lang.admin import TranslationAdmin, TranslationInlineModelAdmin

from .models import (
    Dref,
    DrefFile,
    DrefFinalReport,
    DrefOperationalUpdate,
    DrefSummary,
    IdentifiedNeed,
    NationalSocietyAction,
    PlannedIntervention,
    ProposedAction,
    RiskSecurity,
    SourceInformation,
)
from .tasks import generate_dref_summary


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
    list_display = ("id", "file", "appeal_code")
    search_fields = ("file",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                "event_map_dref",
                "image_dref",
                "budget_file_dref",
                "dref_assessment_report",
                "dref_supporting_document",
                "cover_image_dref",
                "dref_scenario_supporting_document",
                "dref_contingency_plans_supporting_document",
                "event_map_dref_operational_update",
                "image_dref_operational_update",
                "cover_image_dref_operational_update",
                "budget_file_dref_operational_update",
                "dref_operational_update_assessment_report",
                "photos_dref_operational_update",
                "event_map_dref_final_report",
                "photos_dref_final_report",
                "dref_final_report_assessment_report",
                "image_dref_final_report",
                "cover_image_dref_final_report",
            )
        )

    @admin.display(description="Appeal Code")
    def appeal_code(self, obj):
        related_codes = set()
        related_objects = (
            obj.event_map_dref.all(),
            obj.image_dref.all(),
            obj.budget_file_dref.all(),
            obj.dref_assessment_report.all(),
            obj.dref_supporting_document.all(),
            obj.cover_image_dref.all(),
            obj.dref_scenario_supporting_document.all(),
            obj.dref_contingency_plans_supporting_document.all(),
            obj.event_map_dref_operational_update.all(),
            obj.image_dref_operational_update.all(),
            obj.cover_image_dref_operational_update.all(),
            obj.budget_file_dref_operational_update.all(),
            obj.dref_operational_update_assessment_report.all(),
            obj.photos_dref_operational_update.all(),
            obj.event_map_dref_final_report.all(),
            obj.photos_dref_final_report.all(),
            obj.dref_final_report_assessment_report.all(),
            obj.image_dref_final_report.all(),
            obj.cover_image_dref_final_report.all(),
        )

        for related_set in related_objects:
            related_codes.update(code for code in (related_obj.appeal_code for related_obj in related_set) if code)

        return ", ".join(sorted(related_codes))


@admin.register(SourceInformation)
class SourceInformationAdmin(admin.ModelAdmin):
    search_fields = ("source_name",)


class DrefSummaryInline(admin.StackedInline, TranslationInlineModelAdmin):
    model = DrefSummary
    extra = 0
    readonly_fields = (
        "status",
        "prompt_hash",
        "created_at",
        "updated_at",
    )
    fields = (
        "status",
        "prompt_hash",
        "situational_overview",
        "operational_strategy",
        "people_centered_approach",
        "challenges_identified",
        "lessons_learned",
        "created_at",
        "updated_at",
    )


@admin.register(Dref)
class DrefAdmin(CompareVersionAdmin, TranslationAdmin, admin.ModelAdmin):
    inlines = [DrefSummaryInline]
    search_fields = ("title", "appeal_code")
    list_display = (
        "title",
        "national_society",
        "disaster_type",
        "ns_request_date",
        "submission_to_geneva",
        "appeal_code",
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
        "event",
        "supporting_document",
        "national_society_actions",
        "needs_identified",
        "planned_interventions",
        "risk_security",
        "proposed_action",
        "source_information",
        "disaster_category_analysis",
        "targeting_strategy_support_file",
        "budget_file",
        "scenario_analysis_supporting_document",
        "contingency_plans_supporting_document",
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
                "event",
                "supporting_document",
            )
            .prefetch_related("planned_interventions", "needs_identified", "national_society_actions", "users", "risk_security")
        )


@admin.register(DrefOperationalUpdate)
class DrefOperationalUpdateAdmin(CompareVersionAdmin, TranslationAdmin, admin.ModelAdmin):
    list_display = ("title", "national_society", "appeal_code", "disaster_type")
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
        "source_information",
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
    list_display = ("title", "national_society", "appeal_code", "disaster_type")
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
        "proposed_action",
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


@admin.register(DrefSummary)
class DrefSummaryAdmin(TranslationAdmin, admin.ModelAdmin):
    list_display = ("dref", "status", "source_model_name", "source_id", "created_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("dref__title", "dref__appeal_code")
    readonly_fields = ("prompt_hash", "created_at", "updated_at")
    autocomplete_fields = ("dref",)
    actions = ["regenerate_summary"]
    fields = (
        "dref",
        "status",
        "prompt_hash",
        "situational_overview",
        "operational_strategy",
        "people_centered_approach",
        "challenges_identified",
        "lessons_learned",
        "created_at",
        "updated_at",
    )

    @admin.action(description="Regenerate summary for selected DREFs")
    def regenerate_summary(self, request, queryset):
        """Re-trigger summary generation, replaying the source the summary was last built from."""
        for summary in queryset:
            generate_dref_summary.delay(
                summary.dref_id,
                # Fall back to the Dref itself for rows generated before the
                # source was tracked.
                source_model_name=summary.source_model_name or get_model_name(Dref),
                source_id=summary.source_id or summary.dref_id,
                overwrite=True,
            )
        self.message_user(
            request,
            f"Queued summary regeneration for {queryset.count()} DREF(s).",
            messages.SUCCESS,
        )
