from django.contrib import admin
import per.models as models
from per.admin_classes import RegionRestrictedAdmin

class FormDataInline(admin.TabularInline):
    model = models.FormData
    readonly_fields = ('question_id', 'selected_option', 'notes',)
    can_delete = False

class FormAdmin(RegionRestrictedAdmin):
    country_in = 'country__pk__in'
    region_in = 'country__region_id__in'
    inlines = [FormDataInline]
    exclude = ("ip_address", )
    search_fields = ('code', 'name', 'country', )

class FormDataAdmin(RegionRestrictedAdmin):
    country_in = 'form__country__pk__in'
    region_in = 'form__country__region_id__in'
    search_fields = ('question_id', 'form__name', 'form__code', )

class NSPhaseAdmin(RegionRestrictedAdmin):
    search_fields = ('phase',)

class WorkPlanAdmin(RegionRestrictedAdmin):
    search_fields = ('prioritization',)

admin.site.register(models.Form, FormAdmin)
admin.site.register(models.NSPhase, NSPhaseAdmin)
admin.site.register(models.WorkPlan, WorkPlanAdmin)
#admin.site.register(models.FormData, FormDataAdmin) - if we want to edit form data in Django
