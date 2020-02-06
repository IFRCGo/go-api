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


class SubscriptionAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'rtype')
    list_filter   = (('rtype', ChoiceDropdownFilter),)


admin.site.register(models.SurgeAlert, SurgeAlertAdmin)
admin.site.register(models.Subscription, SubscriptionAdmin)
