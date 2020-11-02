from django.contrib import admin
from lang.admin import TranslationAdmin, TranslationInlineModelAdmin
import per.models as models
from per.admin_classes import RegionRestrictedAdmin
from reversion_compare.admin import CompareVersionAdmin


class FormDataInline(admin.TabularInline, TranslationInlineModelAdmin):
    model = models.FormData
    readonly_fields = ('question', 'selected_answer', 'notes')
    can_delete = False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'selected_answer',
            'question',
            'question__component',
            'question__component__area'
        ).prefetch_related('question__answers')


class FormAdmin(CompareVersionAdmin, RegionRestrictedAdmin):
    country_in = 'country__pk__in'
    region_in = 'country__region_id__in'
    inlines = [FormDataInline]
    exclude = ("ip_address", )
    search_fields = ('code', 'name', 'country__name', )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('area', 'country', 'user')


class FormAreaAdmin(CompareVersionAdmin, TranslationAdmin):
    search_fields = ('title',)


class FormComponentAdmin(CompareVersionAdmin, TranslationAdmin):
    search_fields = ('title',)
    list_display = ('title', 'area_number', 'component_number')

    def component_number(self, obj):
        return f'{obj.component_num or ""}{obj.component_letter or ""}'

    def area_number(self, obj):
        return obj.area.area_num

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
                   .order_by('area__area_num', 'component_num', 'component_letter')
                   .select_related('area')
        )


class FormQuestionAdmin(CompareVersionAdmin, TranslationAdmin):
    search_fields = ('question',)
    list_display = ('question', 'component_number', 'question_num')

    def component_number(self, obj):
        return f'{obj.component.component_num or ""}{obj.component.component_letter or ""}'

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
                   .order_by('component__component_num', 'question_num')
                   .select_related('component')
        )


class FormAnswerAdmin(CompareVersionAdmin, TranslationAdmin):
    search_fields = ('text',)


class FormDataAdmin(CompareVersionAdmin, RegionRestrictedAdmin, TranslationAdmin):
    country_in = 'form__country__pk__in'
    region_in = 'form__country__region_id__in'
    search_fields = ('question_id', 'form__name', 'form__code', )


class NSPhaseAdmin(CompareVersionAdmin, RegionRestrictedAdmin):
    search_fields = ('phase',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('country')


class WorkPlanAdmin(CompareVersionAdmin, RegionRestrictedAdmin):
    search_fields = ('prioritization',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('country')


class OverviewAdmin(CompareVersionAdmin, RegionRestrictedAdmin):
    search_fields = ('country',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('country')


class NiceDocumentAdmin(CompareVersionAdmin, RegionRestrictedAdmin):
    country_in = 'country__in'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('country')


class AssessmentTypeAdmin(CompareVersionAdmin, TranslationAdmin):
    search_fields = ('name',)


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
