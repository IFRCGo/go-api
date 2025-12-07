from django.contrib import admin

from .models import Connector, ExtractionItem, LoadItem


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
        "correlation_id",
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
        "correlation_id",
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
        "related_events",
    )
    search_fields = (
        "id",
        "correlation_id",
    )
