from django.contrib import admin

from .models import Connector, EligibleEventMonty


@admin.register(Connector)
class ConnectorAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "last_success_run", "status")
    readonly_fields = ("last_success_run",)


@admin.register(EligibleEventMonty)
class MontyAdmin(admin.ModelAdmin):
    list_display = ("event_id", "created_at")
    list_filter = ("connector",)
    readonly_fields = ("connector",)
    search_fields = ("event_id",)
