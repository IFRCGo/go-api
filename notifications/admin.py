from django.contrib import admin
import notifications.models as models

class SurgeAlertAdmin(admin.ModelAdmin):
    autocomplete_fields = ('event',)
    search_fields = ('operation', 'message', 'event__name',)


class SubscriptionAdmin(admin.ModelAdmin):
    search_fields = ('user__username',)


admin.site.register(models.SurgeAlert, SurgeAlertAdmin)
admin.site.register(models.Subscription, SubscriptionAdmin)
