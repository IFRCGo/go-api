from django.contrib import admin
import notifications.models as models
from api.admin_classes import RegionRestrictedAdmin

class SurgeAlertAdmin(RegionRestrictedAdmin):
    country_in = 'event__countries__in'
    region_in = 'event__regions__in'
    autocomplete_fields = ('event',)
    search_fields = ('operation', 'message', 'event__name',)


class SubscriptionAdmin(admin.ModelAdmin):
    search_fields = ('user__username',)


admin.site.register(models.SurgeAlert, SurgeAlertAdmin)
admin.site.register(models.Subscription, SubscriptionAdmin)
