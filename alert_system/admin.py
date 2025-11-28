from django.contrib import admin

from .models import Connector, ExtractionItem, LoadItems


@admin.register(Connector)
class ConnectorAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "last_success_run", "status")
    readonly_fields = ("last_success_run",)


@admin.register(ExtractionItem)
class EventAdmin(admin.ModelAdmin):
    list_display = ("stac_id", "created_at", "collection")
    list_filter = ("connector", "collection")
    readonly_fields = ("connector",)
    search_fields = ("stac_id",)


@admin.register(LoadItems)
class LoadAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "event_title",
        "created_at",
        "correlation_id",
        "item_eligible",
    )
    list_filter = (
        "connector",
        "item_eligible",
    )
    readonly_fields = ("connector", "item_eligible")
    search_fields = ("id",)
