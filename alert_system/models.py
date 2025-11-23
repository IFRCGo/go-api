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

    filter_hazard = models.JSONField(
        default=dict, blank=True, verbose_name=_("Hazard Filter"), help_text=_("JSON filters to apply when fetching hazard data")
    )

    filter_impact = models.JSONField(
        default=dict, blank=True, verbose_name=_("Impact Filter"), help_text=_("JSON filters to apply when fetching impact data")
    )

    filter_event = models.JSONField(
        default=dict, blank=True, verbose_name=_("Event Filter"), help_text=_("JSON filters to apply when fetching event data")
    )

    class Meta:
        verbose_name = _("Connector")
        verbose_name_plural = _("Connectors")
        ordering = ["type"]


class BaseStacItem(models.Model):
    """
    Abstract base model for items fetched from STAC API.

    """

    class CollectionType(models.IntegerChoices):
        EVENT = 100, _("Impacts")
        HAZARD = 200, _("Hazard")
        IMPACT = 300, _("Impact")

    stac_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name=_("Event ID"),
        help_text=_("Unique identifier for the event item"),
    )

    collection = models.IntegerField(
        choices=CollectionType.choices,
        verbose_name=_("Collection"),
        help_text=_("Collection type of the item"),
    )

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

    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Updated At"), help_text=_("Timestamp when the record was last updated")
    )

    resp_data = models.JSONField(
        null=True, blank=True, verbose_name=_("Response Data"), help_text=_("Raw JSON response from the STAC API")
    )

    metadata = models.JSONField(
        default=dict, blank=True, verbose_name=_("Metadata"), help_text=_("Additional metadata for internal use")
    )

    correlation_id = models.CharField(
        max_length=255,
        verbose_name=_("Correlation ID"),
        help_text=_("Correlation identifier linking all models"),
    )

    cluster = models.CharField(
        max_length=255, null=True, blank=True, verbose_name=_("Cluster"), help_text=_("Cluster classification of the hazard")
    )

    estimate_type = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Estimate Type"),
        help_text=_("Type of severity estimate (e.g., preliminary, confirmed)"),
    )

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

    category = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Category"),
        help_text=_("The category of the impact"),
    )

    type = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("type"),
        help_text=_("The type of the impact"),
    )

    value = models.IntegerField(null=True, blank=True, verbose_name=_("Value"), help_text=_("Value of the associated type"))

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return self.stac_id


class StacItems(BaseStacItem):
    """
    Concrete model for STAC items.
    """

    processed = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Stac Item")
        verbose_name_plural = _("Stac Items")


class EligibleItems(BaseStacItem):
    """
    Concrete model for eligible STAC items.
    """

    class Meta:
        verbose_name = _("Eligible Item")
        verbose_name_plural = _("Eligible Items")
