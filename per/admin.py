from django.contrib import admin
import per.models as models
from per.admin_classes import RegionRestrictedAdmin

class FormAdmin(RegionRestrictedAdmin):
    country_in = 'country__pk__in'
    region_in = 'country__region_id__in'
    search_fields = ('code', 'name', 'country', )

admin.site.register(models.Form, FormAdmin)
