from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _


class Connector(models.Model):
    """
    Configuration for different data source connectors.
    """

    class ConnectorType(models.IntegerChoices):
        GDACS_FLOOD = 100, _("GDACS Flood")
        GDACS_CYCLONE = 200, _("GDACS Cyclone")
        USGS_EARTHQUAKE = 300, _("USGS Earthquake")

    class Status(models.IntegerChoices):
        INITIALIZED = 10, _("Initialized")
        SUCCESS = 20, _("Success")
        FAILED = 30, _("Failed")
        RUNNING = 40, _("Running")

    type = models.IntegerField(
        choices=ConnectorType.choices,
        unique=True,
        verbose_name=_("Connector Type"),
        help_text=_("Type of disaster data connector"),
    )

    status = models.IntegerField(
        choices=Status.choices,
        default=Status.INITIALIZED,
        verbose_name=_("Status"),
        help_text=_("Current status of the connector"),
    )

    source_url = models.URLField(verbose_name=_("Source URL"), help_text=_("Base URL for the STAC API endpoint"))

    last_success_run = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Last Successful Run"), help_text=_("Timestamp of the last successful data fetch")
    )

    def __str__(self):
        return self.get_type_display()  # type: ignore[attr-defined]

    class Meta:
        verbose_name = _("Connector")
        verbose_name_plural = _("Connectors")
        ordering = ["type"]


class BaseItem(models.Model):
    """
    Abstract base model for items fetched from STAC API.

    """

    connector = models.ForeignKey(
        Connector,
        on_delete=models.CASCADE,
        related_name="%(class)s_items",
        verbose_name=_("Connector"),
        help_text=_("Data source connector"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Created At"), help_text=_("Timestamp when the record was created")
    )

    correlation_id = models.CharField(
        max_length=255,
        verbose_name=_("Correlation ID"),
        help_text=_("Correlation identifier linking all models"),
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class ExtractionItem(BaseItem):
    """
    Model for Extraction items.
    """

    class CollectionType(models.IntegerChoices):
        EVENT = 100, _("Impacts")
        HAZARD = 200, _("Hazard")
        IMPACT = 300, _("Impact")

    collection = models.IntegerField(
        choices=CollectionType.choices,
        verbose_name=_("Collection"),
        help_text=_("Collection type of the item"),
    )

    stac_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name=_("Event ID"),
        help_text=_("Unique identifier for the event item"),
    )

    resp_data = models.JSONField(
        null=True, blank=True, verbose_name=_("Response Data"), help_text=_("Raw JSON response from the STAC API")
    )

    def __str__(self):
        return self.stac_id


class LoadItems(BaseItem):
    """
    Model for Load items.
    """

    # TODO:  New id to be used in the future.
    event_title = models.CharField(
        max_length=255,
        verbose_name=_("Event Title"),
        help_text=_("Title of the event"),
    )

    event_description = models.TextField(
        verbose_name=_("Event Description"),
        help_text=_("Description of the event"),
    )

    country = ArrayField(models.CharField(max_length=150), null=True, help_text="Country of the item")

    severity_unit = models.CharField(
        max_length=100, null=True, blank=True, verbose_name=_("Severity Unit"), help_text=_("Unit of measurement for severity")
    )

    severity_label = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Severity Label"),
        help_text=_("Human-readable severity label (e.g., Red, Orange, Green)"),
    )

    severity_value = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Severity Value"),
        help_text=_("Human-readable severity value"),
    )

    total_people_exposed = models.IntegerField(
        verbose_name=_("Total People Exposed"),
        help_text=_("Total number of people exposed to event"),
    )

    total_buildings_exposed = models.IntegerField(
        verbose_name=_("Total Buildings Exposed"),
        help_text=_("Total number of buildings exposed to event"),
    )

    # NOTE: This field might change in the future.
    impact_metadata = models.JSONField(
        verbose_name=_("Impact Metadata"),
        help_text=_("Metadata constructed from all events associated"),
    )

    item_eligible = models.BooleanField(
        help_text=_("Is the item eligible for alerting"),
    )

    class Meta:
        verbose_name = _("Eligible Item")
        verbose_name_plural = _("Eligible Items")
