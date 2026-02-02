from django.contrib import admin

from .models import AlertEmailLog, AlertEmailThread, Connector, ExtractionItem, LoadItem


@admin.register(Connector)
class ConnectorAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "last_success_run", "status")
    readonly_fields = ("last_success_run",)


@admin.register(ExtractionItem)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "stac_id",
        "created_at",
        "collection",
        "guid",
    )
    list_filter = ("connector", "collection")
    readonly_fields = ("connector",)
    search_fields = (
        "stac_id",
        "correlation_id",
    )


@admin.register(LoadItem)
class LoadItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "event_title",
        "created_at",
        "guid",
        "item_eligible",
        "is_past_event",
    )
    list_filter = (
        "connector",
        "item_eligible",
        "is_past_event",
    )
    readonly_fields = (
        "connector",
        "item_eligible",
        "related_montandon_events",
        "related_go_events",
    )
    search_fields = (
        "id",
        "correlation_id",
    )


@admin.register(AlertEmailThread)
class AlertEmailThreadAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "correlation_id",
        "root_email_message_id",
    )
    search_fields = (
        "correlation_id",
        "root_email_message_id",
        "user__username",
    )
    list_select_related = ("user",)
    autocomplete_fields = ("user",)


@admin.register(AlertEmailLog)
class AlertEmailLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "message_id",
        "status",
    )
    list_select_related = (
        "user",
        "subscription",
        "item",
        "thread",
    )
    search_fields = (
        "user__username",
        "message_id",
    )
    autocomplete_fields = (
        "user",
        "subscription",
        "item",
        "thread",
    )
    list_filter = ("status",)
