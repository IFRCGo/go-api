import csv
import time
from functools import lru_cache

from django.contrib import admin
from django.http import HttpResponse
from django.utils.translation import get_language as django_get_language
from reversion_compare.admin import CompareVersionAdmin

import per.models as models
from api.models import Appeal
from lang.admin import TranslationAdmin, TranslationInlineModelAdmin
from per.admin_classes import GotoNextModelAdmin, RegionRestrictedAdmin
from per.task import generate_summary


class FormDataInline(admin.TabularInline, TranslationInlineModelAdmin):
    model = models.FormData
    readonly_fields = ("question", "selected_answer", "notes")
    can_delete = False

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("selected_answer", "question", "question__component", "question__component__area")
            .prefetch_related("question__answers")
            .order_by("question__component__area__area_num", "question__component__component_num", "question__question_num")
        )


class FormAdmin(CompareVersionAdmin, RegionRestrictedAdmin):
    country_in = "overview__country_id__in"
    region_in = "overview__country__region_id__in"
    inlines = [FormDataInline]
    exclude = ("ip_address",)
    list_display = ("area", "overview", "overview__date_of_assessment")
    search_fields = ("area__title",)
    readonly_fields = ("overview", "area")
    ordering = ("-created_at",)

    def overview__date_of_assessment(self, obj):
        return f'{obj.overview.date_of_assessment or ""}'

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("area", "user", "overview", "overview__country")
            .prefetch_related("form_data")
        )


class FormAreaAdmin(CompareVersionAdmin, TranslationAdmin):
    search_fields = ("title",)


class FormComponentAdmin(CompareVersionAdmin, TranslationAdmin):
    search_fields = ("title",)
    list_display = ("title", "area_number", "component_number")
    autocomplete_fields = ["question_responses"]

    def component_number(self, obj):
        return f'{obj.component_num or ""}{obj.component_letter or ""}'

    def area_number(self, obj):
        return obj.area.area_num

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.exclude(component_num=14, component_letter__isnull=False)
        return queryset.order_by("area__area_num", "component_num", "component_letter").select_related("area")


class FormQuestionAdmin(CompareVersionAdmin, TranslationAdmin):
    search_fields = ("question",)
    list_display = ("question", "component_number", "question_num")

    def component_number(self, obj):
        return f'{obj.component.component_num or ""}{obj.component.component_letter or ""}'

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("component__component_num", "question_num").select_related("component")


class FormAnswerAdmin(CompareVersionAdmin, TranslationAdmin):
    search_fields = ("text",)


class FormDataAdmin(CompareVersionAdmin, RegionRestrictedAdmin, TranslationAdmin):
    country_in = "form__overview__country_id__in"
    region_in = "form__overview__country__region_id__in"
    search_fields = ("question_id", "form__area__title")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("form", "form__overview", "form__overview__country")


class NSPhaseAdmin(CompareVersionAdmin, RegionRestrictedAdmin):
    search_fields = ("phase",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("country")


class WorkPlanAdmin(CompareVersionAdmin, RegionRestrictedAdmin):
    search_fields = ("prioritization",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("country")


class OverviewAdmin(CompareVersionAdmin, RegionRestrictedAdmin):
    country_in = "country_id__in"
    region_in = "country__region_id__in"
    search_fields = ("country__name",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("country")


class NiceDocumentAdmin(CompareVersionAdmin, RegionRestrictedAdmin):
    country_in = "country__in"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("country")


class AssessmentTypeAdmin(CompareVersionAdmin, TranslationAdmin):
    search_fields = ("name",)


class PerComponentRatingAdmin(CompareVersionAdmin, TranslationAdmin):
    ordering = ("value",)
    search_fields = ("title",)


class PerWorkPlanComponentAdmin(TranslationAdmin):
    pass


class PerWorkPlanAdmin(admin.ModelAdmin):
    pass


class FormPrioritizationAdmin(admin.ModelAdmin):
    pass


class FormPrioritizationComponentAdmin(TranslationAdmin):
    pass


class FormAssessmentAdmin(TranslationAdmin):
    pass


class FormAreaResponseAdmin(TranslationAdmin):
    pass


class FormComponentResponseAdmin(TranslationAdmin):
    pass


class FormComponentQuestionAndAnswerAdmin(TranslationAdmin):
    search_fields = [
        "question",
    ]


class OrganizationTypesAdmin(admin.ModelAdmin):
    list_display = ("title", "order")
    search_fields = ("title",)
    ordering = ("order",)


class PerDocumentUploadAdmin(admin.ModelAdmin):
    pass


class FormQuestionGroupAdmin(TranslationAdmin):
    pass


class OpsLearningAdmin(GotoNextModelAdmin):
    ordering = ("-created_at",)
    ls = ("organization", "organization_validated", "sector", "sector_validated", "per_component", "per_component_validated")
    list_filter = ("is_validated", "appeal_code__atype") + ls
    autocomplete_fields = ("appeal_code",) + ls
    search_fields = ("learning", "learning_validated", "appeal_code__aid", "appeal_code__code")
    list_display = ("learning", "appeal_code", "is_validated", "modified_at")
    change_form_template = "admin/opslearning_change_form.html"
    actions = ["export_selected_records"]

    def get_fields(self, request, obj=None):
        if obj and obj.is_validated:
            return (
                "learning_validated",
                "appeal_code",
                "appeal_document_id",
                "type_validated",
                "organization_validated",
                "sector_validated",
                "per_component_validated",
            )
        elif obj:
            return (
                "learning",
                "appeal_code",
                "appeal_document_id",
                "type",
                "organization",
                "sector",
                "per_component",
                "is_validated",
            )
        return ("learning", "appeal_code", "appeal_document_id", "type", "organization", "sector", "per_component")

    def save_model(self, request, obj, form, change):
        if change:
            orig_obj = models.OpsLearning.objects.get(pk=obj.pk)
            if obj and obj.is_validated and obj.is_validated != orig_obj.is_validated:
                # Validation happened just now:
                print("Moving data to validated fields for OpsLearning id: %d" % obj.pk)
                obj.learning_validated = obj.learning
                obj.type_validated = obj.type
                obj.organization_validated.add(*[x[0] for x in obj.organization.values_list()])
                obj.sector_validated.add(*[x[0] for x in obj.sector.values_list()])
                obj.per_component_validated.add(*[x[0] for x in obj.per_component.values_list()])

        super().save_model(request, obj, form, change)

    def export_selected_records(self, request, queryset):
        """
        The aim of this algorythm: to avoid flattening of multiple values.
        (Flattening means: displaying lists as value.0, value.1, value.2)
        Instead of this we would like to show these in different rows.
        Maybe there is an easier way also to achieve this.
        See also: custom_renderers.py::NarrowCSVRenderer()
        """

        # We cache the used appeals to make export faster
        @lru_cache(maxsize=5000)
        def get_appeal_details(code):
            appl = Appeal.objects.filter(code=code)
            if appl:
                a = appl[0]
                ctry = a.country and a.country.name_en
                regn = a.region and a.region.label_en
                dtyp = a.dtype and a.dtype.name_en
                year = a.start_date and a.start_date.year
                benf = a.num_beneficiaries
            else:
                ctry = regn = dtyp = year = benf = None
            return (ctry, regn, dtyp, year, benf)

        def break_to_rows(many2many, many2many_validated, is_validated, idx):
            if is_validated and many2many_validated.values_list():
                return [str(x[idx]) for x in many2many_validated.values_list()]
            elif many2many.values_list():
                return [str(x[idx]) for x in many2many.values_list()]
            return [""]

        timestr = time.strftime("%Y%m%d-%H%M%S")
        finding = [""] + [t.label for t in models.LearningType]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=OpsLearning_export_{}.csv".format(timestr)
        writer = csv.writer(response, quoting=csv.QUOTE_NONNUMERIC)

        writer.writerow(
            [
                "id",
                "appeal_code",
                "learning",
                "finding",
                "sector",
                "component",
                "organization",
                "country_name",
                "region_name",
                "dtype_name",
                "appeal_year",
                "appeal_num_beneficiaries",
                "modified_at",
            ]
        )

        for opsl in queryset:
            v = opsl.is_validated
            lrng = opsl.learning_validated if opsl.is_validated else opsl.learning
            find = finding[opsl.type_validated] if opsl.is_validated else finding[opsl.type]
            modf = opsl.modified_at.date()
            code = opsl.appeal_code
            (ctry, regn, dtyp, year, benf) = get_appeal_details(code)

            for orgn in break_to_rows(opsl.organization, opsl.organization_validated, v, 1):
                for sect in break_to_rows(opsl.sector, opsl.sector_validated, v, 1):
                    for pcom in break_to_rows(opsl.per_component, opsl.per_component_validated, v, 2):

                        writer.writerow([opsl.id, code, lrng, find, sect, pcom, orgn, ctry, regn, dtyp, year, benf, modf])

        print("Cache information of Appeal queries:\n", get_appeal_details.cache_info())
        return response

    export_selected_records.short_description = "Export selected Ops Learning records to CSV"


class OpsLearningCacheResponseAdmin(TranslationAdmin):
    search_fields = (
        "id",
        "used_ops_learning__appeal_code__aid",
        "used_ops_learning__appeal_code__code",
    )
    list_display = (
        "__str__",
        "insights1_title",
        "insights2_title",
        "insights3_title",
        "status",
    )
    list_filter = ("status",)
    used_ops_learning_in = "used_ops_learning_in"
    autocomplete_fields = ("used_ops_learning",)
    exclude = (
        "export_status",
        "exported_file",
        "exported_at",
    )
    actions = ["regenerate_summary"]

    def regenerate_summary(self, request, queryset):
        """
        Regenerate the summary of the selected OpsLearningCacheResponse objects.
        """
        requested_lang = django_get_language()
        for obj in queryset:
            generate_summary.delay(
                ops_learning_summary_id=obj.id,
                filter_data=obj.used_filters,
                translation_lazy=requested_lang == "en",
                # NOTE: Regenerating the summary will overwrite the cache
                overwrite_prompt_cache=True,
            )

    regenerate_summary.short_description = "Regenerate Summary for selected Ops Learning Cache Response"


class OpsLearningPromptResponseCacheAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "type",
        "response",
    )
    list_filter = ("type",)


admin.site.register(models.Form, FormAdmin)
admin.site.register(models.FormArea, FormAreaAdmin)
admin.site.register(models.FormComponent, FormComponentAdmin)
admin.site.register(models.FormQuestion, FormQuestionAdmin)
admin.site.register(models.FormAnswer, FormAnswerAdmin)
# admin.site.register(models.FormData, FormDataAdmin) - if we want to edit form data in Django
admin.site.register(models.NSPhase, NSPhaseAdmin)
admin.site.register(models.WorkPlan, WorkPlanAdmin)
admin.site.register(models.Overview, OverviewAdmin)
admin.site.register(models.NiceDocument, NiceDocumentAdmin)
admin.site.register(models.AssessmentType, AssessmentTypeAdmin)
admin.site.register(models.PerComponentRating, PerComponentRatingAdmin)
admin.site.register(models.PerWorkPlan, PerWorkPlanAdmin)
admin.site.register(models.PerWorkPlanComponent, PerWorkPlanComponentAdmin)
admin.site.register(models.FormPrioritization, FormPrioritizationAdmin)
admin.site.register(models.FormPrioritizationComponent, FormPrioritizationComponentAdmin)
admin.site.register(models.PerAssessment, FormAssessmentAdmin)
admin.site.register(models.AreaResponse, FormAreaResponseAdmin)
admin.site.register(models.FormComponentResponse, FormComponentResponseAdmin)
admin.site.register(models.FormComponentQuestionAndAnswer, FormComponentQuestionAndAnswerAdmin)
admin.site.register(models.OrganizationTypes, OrganizationTypesAdmin)
admin.site.register(models.OpsLearning, OpsLearningAdmin)
admin.site.register(models.PerDocumentUpload, PerDocumentUploadAdmin)
admin.site.register(models.FormQuestionGroup, FormQuestionGroupAdmin)
admin.site.register(models.OpsLearningCacheResponse, OpsLearningCacheResponseAdmin)
admin.site.register(models.OpsLearningPromptResponseCache, OpsLearningPromptResponseCacheAdmin)
