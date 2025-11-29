from django.contrib import admin
from django_admin_listfilter_dropdown.filters import ChoiceDropdownFilter
from reversion_compare.admin import CompareVersionAdmin

import notifications.models as models
from api.admin_classes import RegionRestrictedAdmin
from lang.admin import TranslationAdmin


class SurgeAlertAdmin(CompareVersionAdmin, RegionRestrictedAdmin, TranslationAdmin):

    @admin.display(description="std")
    def std(self, obj):
        return obj.molnix_status == models.SurgeAlertStatus.STOOD_DOWN

    std.boolean = True
    country_in = "event__countries__in"
    region_in = "event__regions__in"
    autocomplete_fields = ("event",)
    search_fields = (
        "operation",
        "message",
        "event__name",
    )
    readonly_fields = ("molnix_id",)
    list_display = ("__str__", "message", "start", "molnix_id", "molnix_status", "std")
    list_filter = ("molnix_status",)


class SubscriptionAdmin(CompareVersionAdmin):
    search_fields = ("user__username", "rtype")
    list_filter = (("rtype", ChoiceDropdownFilter),)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


class NotificationGUIDAdmin(admin.ModelAdmin):
    list_display = (
        "api_guid",
        "email_type",
        "created_at",
    )
    list_filter = ("email_type",)
    search_fields = ("email_type",)
    readonly_fields = (
        "api_guid",
        "email_type",
        "to_list",
        "created_at",
    )

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(models.NotificationGUID, NotificationGUIDAdmin)
admin.site.register(models.Subscription, SubscriptionAdmin)
admin.site.register(models.SurgeAlert, SurgeAlertAdmin)


@admin.register(models.HazardType)
class AlertTypeAdmin(admin.ModelAdmin):
    list_display = ("type",)


@admin.register(models.AlertSubscription)
class AlertSubscriptionAdmin(admin.ModelAdmin):
    list_select_related = True
    list_display = ("user", "created_at")
    autocomplete_fields = ("user",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "user",
            )
            .prefetch_related(
                "countries",
                "regions",
                "hazard_types",
            )
        )
