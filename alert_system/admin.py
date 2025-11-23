from django.contrib import admin

from .models import Connector, EligibleItems, StacItems


@admin.register(Connector)
class ConnectorAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "last_success_run", "status")
    readonly_fields = ("last_success_run",)


@admin.register(StacItems)
class EventAdmin(admin.ModelAdmin):
    list_display = ("stac_id", "created_at", "collection")
    list_filter = ("connector", "collection")
    readonly_fields = ("connector",)
    search_fields = ("stac_id",)


@admin.register(EligibleItems)
class EligibleAdmin(admin.ModelAdmin):
    list_display = ("stac_id", "created_at", "collection")
    list_filter = ("connector",)
    readonly_fields = ("connector",)
    search_fields = ("stac_id",)
