from django.contrib import admin
import per.models as models

class PERFormAdmin(admin.ModelAdmin):
    search_fields = ('code', 'name',)

admin.site.register(models.PERForm, PERFormAdmin)
