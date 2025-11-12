from django.db import models
from django.utils import timezone


class Connector(models.Model):
    class ConnectorType(models.TextChoices):
        GDACS_FLOOD = "GDACS_FLOOD", "GDACS_FLOOD"
        GDACS_CYCLONE = "GDACS_CYCLONE", "GDACS_CYCLONE"
        USGS_EARTHQUAKE = "USGS_EARTHQUAKE", "USGS_EARTHQUAKE"

    class Status(models.IntegerChoices):
        SUCCESS = 1
        FAILURE = 2
        RUNNING = 3

    type = models.CharField(
        max_length=20,
        choices=ConnectorType.choices,
        unique=True,
    )
    last_success_run = models.DateTimeField(null=True, blank=True)
    filters = models.JSONField(blank=True, null=True)

    status = models.IntegerField(choices=Status.choices)
    source_url = models.URLField(blank=False, null=False)

    def __str__(self):
        return self.type


class EligibleEventBase(models.Model):
    event_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    resp_data = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        abstract = True


class EligibleEventMonty(EligibleEventBase):
    connector = models.ForeignKey(
        Connector,
        on_delete=models.CASCADE,
        related_name="monty_events",
    )

    def __str__(self):
        return f"Monty Event {self.event_id}"
