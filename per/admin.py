from django.contrib import admin
import per.models as models
from per.admin_classes import RegionRestrictedAdmin

class FormAdmin(RegionRestrictedAdmin):
    country_in = 'country__pk__in'
    region_in = 'country__region_id__in'
    search_fields = ('code', 'name', 'country', )

class FormDataAdmin(RegionRestrictedAdmin):
    country_in = 'form__country__pk__in'
    region_in = 'form__country__region_id__in'
    search_fields = ('question_id', 'form__name', 'form__code', )

admin.site.register(models.Form, FormAdmin)
admin.site.register(models.FormData, FormDataAdmin)
