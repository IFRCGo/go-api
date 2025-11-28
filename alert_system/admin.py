from django.contrib import admin

<<<<<<< HEAD
from .models import Connector, ExtractionItem, LoadItem
||||||| parent of 72d5c50d (feat(etl): refactor existing extraction into ETL.)
from .models import Connector, EligibleItems, StacItems
=======
from .models import Connector, ExtractionItem, LoadItems
>>>>>>> 72d5c50d (feat(etl): refactor existing extraction into ETL.)


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


<<<<<<< HEAD
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
        "related_montandon_events",
        "related_go_events",
    )
    search_fields = (
        "id",
        "correlation_id",
    )
||||||| parent of 72d5c50d (feat(etl): refactor existing extraction into ETL.)
@admin.register(EligibleItems)
class EligibleAdmin(admin.ModelAdmin):
    list_display = ("stac_id", "created_at", "collection")
    list_filter = ("connector",)
    readonly_fields = ("connector",)
    search_fields = ("stac_id",)
=======
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
>>>>>>> 72d5c50d (feat(etl): refactor existing extraction into ETL.)
