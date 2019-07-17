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

class OverviewAdmin(RegionRestrictedAdmin):
    search_fields = ('country',)

class NiceDocumentAdmin(RegionRestrictedAdmin):
    country_in = 'country__in'
#   Duplicated from situation reports
    def save_model(self, request, obj, form, change):
       if change:
           obj.save()
       else:
           for i,one_document in enumerate(request.FILES.getlist('documents_multiple')):
               if i<30: # not letting tons of documents to be attached
                   models.NiceDocument.objects.create(
                       name        =obj.name if i == 0 else obj.name + '-' + str(i),
                       document    =one_document,
                       document_url=obj.document_url,
                       country     =obj.country,
                       visibility  =obj.visibility,
                       )

admin.site.register(models.Form, FormAdmin)
#admin.site.register(models.FormData, FormDataAdmin) - if we want to edit form data in Django
admin.site.register(models.NSPhase, NSPhaseAdmin)
admin.site.register(models.WorkPlan, WorkPlanAdmin)
admin.site.register(models.Overview, OverviewAdmin)
admin.site.register(models.NiceDocument, NiceDocumentAdmin)
