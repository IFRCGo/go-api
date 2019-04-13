from django.contrib import admin
import per.models as models

class FormAdmin(admin.ModelAdmin):
    search_fields = ('code', 'name',)

admin.site.register(models.Form, FormAdmin)
