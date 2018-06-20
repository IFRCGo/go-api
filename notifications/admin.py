from django.contrib import admin
import notifications.models as models

class SurgeAlertAdmin(admin.ModelAdmin):
    autocomplete_fields = ('event',)

admin.site.register(models.SurgeAlert, SurgeAlertAdmin)
admin.site.register(models.Subscription)
