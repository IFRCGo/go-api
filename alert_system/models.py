from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from api.models import DisasterType, Event
from notifications.models import AlertSubscription


class ImpactDetailsEnum:
    class Type(models.TextChoices):
        POTENTIALLY_AFFECTED = "potentially_affected", _("Potentially Affected")
        POTENTIALLY_DAMAGED = "potentially_damaged", _("Potentially Damaged")
        HIGHEST_RISK = "highest_risk", _("Highest Risk")
        AFFECTED_TOTAL = "affected_total", _("Affected Total")
        AFFECTED_DIRECT = "affected_direct", _("Affected Direct")

    class Category(models.TextChoices):
        PEOPLE = "people", _("People")
        BUILDINGS = "buildings", _("buildings")


class Connector(models.Model):
    """
    Configuration for different data source connectors.
    """

    class ConnectorType(models.IntegerChoices):
        GDACS_FLOOD = 100, _("GDACS Flood")
        GDACS_CYCLONE = 200, _("GDACS Cyclone")
        USGS_EARTHQUAKE = 300, _("USGS Earthquake")

    PROCESSOR_REGISTRY = {
        ConnectorType.GDACS_FLOOD: "alert_system.etl.gdacs_flood.extraction.GdacsFloodExtraction",
        ConnectorType.USGS_EARTHQUAKE: "alert_system.etl.usgs_earthquake.extraction.USGSEarthquakeExtraction",
    }  # Add all the extraction classes here

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

    polling_start_datetime = models.DateTimeField(
        verbose_name=_("Polling Start DateTime"), help_text=_("Polling start date-time"), null=True, blank=True
    )
    lookback_weeks = models.IntegerField(
        verbose_name=_("Lookback Weeks"), help_text=_("Lookback weeks for fetching past events."), default=520, blank=True
    )  # NOTE: 10 years default lookback.
    source_url = models.URLField(verbose_name=_("Source URL"), help_text=_("Base URL for the STAC API endpoint"))

    last_success_run = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Last Successful Run"), help_text=_("Timestamp of the last successful data fetch")
    )

    dtype = models.ForeignKey(DisasterType, verbose_name=_("disaster type"), null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.get_type_display()  # type: ignore[attr-defined]

    id: int

    class Meta:
        verbose_name = _("Connector")
        verbose_name_plural = _("Connectors")
        ordering = ["id", "type"]

    def set_connector_status(self, status):
        self.status = status
        update_fields = ["status"]

        if status == Connector.Status.SUCCESS:
            self.last_success_run = timezone.now()
            update_fields.append("last_success_run")

        self.save(update_fields=update_fields)

    def get_extraction_class(self):
        """
        Resolve and instantiate the extraction class for this connector.
        """
        path = self.PROCESSOR_REGISTRY.get(self.type)
        if not path:
            raise RuntimeError(f"No extraction class registered for connector type '{self.type}'")

        try:
            processor_cls = import_string(path)
        except ImportError as exc:
            raise RuntimeError(f"Failed to import extraction class '{path}' for connector type '{self.type}'") from exc

        return processor_cls(self)


class BaseItem(models.Model):
    """
    Abstract base model for items fetched from STAC API.

    """

    extraction_run_id = models.UUIDField(
        null=True, blank=True, db_index=True, help_text="UUID field for tracking the extraction run through ETL pipeline"
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

    correlation_id = models.CharField(
        max_length=255,
        verbose_name=_("Correlation ID"),
        help_text=_("Correlation identifier linking all models"),
    )

    guid = models.CharField(
        verbose_name=_("GUID"),
        help_text=_("Globally unique ID for events"),
    )

    id: int

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class ExtractionItem(BaseItem):
    """
    Model for Extraction items.
    """

    class CollectionType(models.IntegerChoices):
        EVENT = 100, _("event")
        HAZARD = 200, _("Hazard")
        IMPACT = 300, _("Impacts")

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
    # NOTE: This might increase the database size massively.
    resp_data = models.JSONField(
        null=True, blank=True, verbose_name=_("Response Data"), help_text=_("Raw JSON response from the STAC API")
    )

    def __str__(self):
        return self.stac_id


class LoadItem(BaseItem):
    """
    Model for Load items.
    """

    parent_guid = models.CharField(
        verbose_name=_("Parent GUID"),
        help_text=_("GUID without the episode number."),
    )

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
    start_datetime = models.DateTimeField(null=False, blank=False, help_text="Start datetime of the event")

    end_datetime = models.DateTimeField(null=True, blank=False, help_text="End datetime of the event")

    country_codes = ArrayField(
        models.CharField(max_length=150), null=True, help_text="List of country codes(ISO3) of afffected countries"
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

    total_people_exposed = models.IntegerField(
        null=True,
        verbose_name=_("Total People Exposed"),
        help_text=_("Total number of people exposed to event"),
    )

    total_buildings_exposed = models.IntegerField(
        null=True,
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

    is_past_event = models.BooleanField(
        help_text=_("Is the item in load table a past event"),
        default=False,
    )

    related_montandon_events = models.ManyToManyField("self", symmetrical=False, related_name="related_to", blank=True)

    related_go_events = models.ManyToManyField(Event, verbose_name="Related GO Events", blank=True)

    def __str__(self):
        return self.event_title

    class Meta:
        verbose_name = _("Eligible Item")
        verbose_name_plural = _("Eligible Items")
        constraints = [
            models.UniqueConstraint(fields=["guid"], name="unique_guid")
        ]  # NOTE: GUID should be unique in the load table.


class AlertEmailThread(models.Model):
    """
    Represents a single email conversation thread for alert emails.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="alert_email_threads",
    )

    correlation_id = models.CharField(
        max_length=255,
        help_text=_("Identifier linking related LoadItems into the same email thread."),
    )

    root_email_message_id = models.CharField(
        max_length=255,
        unique=True,
        help_text=_("Message-ID of the first email in this thread."),
    )

    root_message_sent_at = models.DateTimeField(
        help_text=_("Timestamp when the root email was sent."),
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # Typing
    user_id: int

    class Meta:
        verbose_name = _("Email Thread")
        verbose_name_plural = _("Email Threads")
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["correlation_id", "user"]),
        ]

    def __str__(self):
        return f"Thread: {self.user.get_full_name()}-{self.correlation_id}"


class AlertEmailLog(models.Model):
    """
    Log of alert emails sent to users, tracking status, type, and threading.
    """

    class Status(models.IntegerChoices):
        PENDING = 100, _("Pending")
        PROCESSING = 200, _("Processing")
        SENT = 300, _("Sent")
        FAILED = 400, _("Failed")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        help_text=_("The recipient of this alert email."),
    )
    subscription = models.ForeignKey[AlertSubscription, AlertSubscription](
        AlertSubscription,
        on_delete=models.CASCADE,
        related_name="email_alert_subscription",
        verbose_name=_("Alert Subscription"),
    )

    item = models.ForeignKey[LoadItem, LoadItem](
        LoadItem,
        on_delete=models.CASCADE,
        related_name="email_alert_load_item",
        verbose_name=_("Load Item"),
    )

    message_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Message ID"),
        help_text=_("Unique Message-ID of email for tracking and threading."),
    )

    status = models.IntegerField(
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name=_("Email Status"),
    )

    email_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Sent At"),
        help_text=_("Timestamp when email was successfully sent."),
    )

    thread = models.ForeignKey(
        AlertEmailThread,
        on_delete=models.CASCADE,
        related_name="email_alert_thread",
        null=True,
        blank=True,
        verbose_name=_("Email Thread"),
    )

    id: int
    user_id: int
    subscription_id: int
    item_id: int
    thread_id: int

    class Meta:
        verbose_name = _("Email Alert Log")
        verbose_name_plural = _("Email Alert Logs")
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["user", "subscription", "email_sent_at"]),
            models.Index(fields=["user", "item", "status"]),
        ]
