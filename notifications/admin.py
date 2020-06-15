from django.contrib import admin
import notifications.models as models
from api.admin_classes import RegionRestrictedAdmin
from django_admin_listfilter_dropdown.filters import ChoiceDropdownFilter
from reversion.admin import VersionAdmin
from reversion.models import Revision
from reversion_compare.admin import CompareVersionAdmin


class SurgeAlertAdmin(CompareVersionAdmin, RegionRestrictedAdmin):
    country_in = 'event__countries__in'
    region_in = 'event__regions__in'
    autocomplete_fields = ('event',)
    search_fields = ('operation', 'message', 'event__name',)


class SubscriptionAdmin(CompareVersionAdmin):
    search_fields = ('user__username', 'rtype')
    list_filter   = (('rtype', ChoiceDropdownFilter),)


class NotificationGUIDAdmin(admin.ModelAdmin):
    list_display = ('api_guid', 'email_type', 'created_at',)
    list_filter = ('email_type',)
    search_fields = ('email_type',)
    readonly_fields = ('api_guid', 'email_type', 'to_list',)

    def has_add_permission(self, request, obj=None):
        return False


admin.site.register(models.NotificationGUID, NotificationGUIDAdmin)
admin.site.register(models.Subscription, SubscriptionAdmin)
admin.site.register(models.SurgeAlert, SurgeAlertAdmin)
