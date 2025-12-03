from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from api.models import Country, DisasterType, Event, Region
from deployments.models import MolnixTag


class SurgeAlertType(models.IntegerChoices):
    FACT = 0, _("fact")
    SIMS = 1, _("SIMS")
    ERU = 2, _("ERU")
    DHEOPS = 3, _("DHEOPS")
    HEOPS = 4, _("HEOPS")
    SURGE = 5, _("surge")
    RAPID_RESPONSE = 6, _("rapid response")


class SurgeAlertCategory(models.IntegerChoices):
    INFO = 0, _("information")
    DEPLOYMENT = 1, _("deployment")
    ALERT = 2, _("alert")
    SHELTER = 3, _("shelter")
    STAND_DOWN = 4, _("stand down")


class SurgeAlertStatus(models.IntegerChoices):
    """
    Note: Ordering value should be in order of Open, Stood Down, Closed to supported custom defined ordering logic
    """

    OPEN = 0, _("Open")
    STOOD_DOWN = 1, _("Stood Down")
    CLOSED = 2, _("Closed")


class SurgeAlert(models.Model):

    atype = models.IntegerField(choices=SurgeAlertType.choices, verbose_name=_("alert type"), default=0)
    category = models.IntegerField(choices=SurgeAlertCategory.choices, verbose_name=_("category"), default=0)
    operation = models.CharField(verbose_name=_("operation"), max_length=100)
    message = models.TextField(verbose_name=_("message"))
    deployment_needed = models.BooleanField(verbose_name=_("deployment needed"), default=False)
    is_private = models.BooleanField(verbose_name=_("is private?"), default=False)
    event = models.ForeignKey(Event, verbose_name=_("event"), null=True, blank=True, on_delete=models.SET_NULL)
    country = models.ForeignKey(Country, verbose_name=_("country"), null=True, blank=True, on_delete=models.SET_NULL)
    # Fields specific to Molnix integration:
    # ID in Molnix system, if parsed from Molnix.
    molnix_id = models.IntegerField(blank=True, null=True)

    opens = models.DateTimeField(blank=True, null=True)
    closes = models.DateTimeField(blank=True, null=True)
    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    molnix_tags = models.ManyToManyField(MolnixTag, blank=True)

    # Don't set `auto_now_add` so we can modify it on save
    created_at = models.DateTimeField(verbose_name=_("created at"))
    molnix_status = models.IntegerField(
        choices=SurgeAlertStatus.choices, verbose_name=_("alert status"), default=SurgeAlertStatus.OPEN
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Surge Alert")
        verbose_name_plural = _("Surge Alerts")

    @staticmethod
    def parse_molnix_status(status_raw: str) -> SurgeAlertStatus:
        """
        A position_status of active should be shown as Open
        A position_status of archived should be shown as Closed
        A position_status of unfilled should be shown as Stood Down
        If the position_status is non other than active, archived, unfilled then show Closed.
        """
        molnix_status_dict = {
            "active": SurgeAlertStatus.OPEN,
            "unfilled": SurgeAlertStatus.STOOD_DOWN,
            "archived": SurgeAlertStatus.CLOSED,
        }

        return molnix_status_dict.get(status_raw.lower(), SurgeAlertStatus.CLOSED)

    def save(self, *args, **kwargs):
        if (not self.id and not self.created_at) or (self.created_at > timezone.now()):
            self.created_at = timezone.now()
        return super(SurgeAlert, self).save(*args, **kwargs)

    def __str__(self):
        if self.operation and self.operation != "":
            return self.operation
        elif self.event:
            return self.event.name
        elif self.message:
            return self.message
        else:
            return "–"


class SubscriptionType(models.IntegerChoices):
    """New or edit to existing record"""

    NEW = 0, _("new")
    EDIT = 1, _("edit")


class RecordType(models.IntegerChoices):
    """Types of notifications a user can subscribe to"""

    EVENT = 0, _("event")  # not to use in rtype_of_subscr, migrated to NEW_EMERGENCIES
    APPEAL = 1, _("appeal")  # not to use in rtype_of_subscr, migrated to                 NEW_OPERATIONS
    FIELD_REPORT = 2, _("field report")  # not to use in rtype_of_subscr, migrated to NEW_EMERGENCIES
    SURGE_ALERT = 3, _("surge alert")
    COUNTRY = 4, _("country")
    REGION = 5, _("region")
    DTYPE = 6, _("disaster type")
    PER_DUE_DATE = 7, _("per due date")
    FOLLOWED_EVENT = 8, _("followed event")
    SURGE_DEPLOYMENT_MESSAGES = 9, _("surge deployment messages")
    SURGE_APPROACHING_END_OF_MISSION = 10, _("surge approaching end of mission")
    WEEKLY_DIGEST = 11, _("weekly digest")
    NEW_EMERGENCIES = 12, _("new emergencies")
    NEW_OPERATIONS = 13, _("new operations")
    GENERAL_ANNOUNCEMENTS = 14, _("general announcements")


# Migration
# update      notification_subscription set rtype=12, stype=0 where rtype=0; -- EVENT    > EMERGENCY
# delete from notification_subscription                       where rtype=0; -- EVENT    > EMERGENCY
# update      notification_subscription set rtype=13, stype=0 where rtype=1; -- APPEAL   >            OPERATION
# delete from notification_subscription                       where rtype=1; -- APPEAL   >            OPERATION
# update      notification_subscription set rtype=12, stype=0 where rtype=2; -- FIELDREP > EMERGENCY
# delete from notification_subscription                       where rtype=2; -- FIELDREP > EMERGENCY


class Subscription(models.Model):
    """User subscriptions"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        on_delete=models.CASCADE,
        related_name="subscription",
    )

    stype = models.IntegerField(choices=SubscriptionType.choices, verbose_name=_("subscription type"), default=0)
    rtype = models.IntegerField(choices=RecordType.choices, verbose_name=_("record type"), default=0)

    country = models.ForeignKey(Country, verbose_name=_("country"), null=True, blank=True, on_delete=models.SET_NULL)
    region = models.ForeignKey(Region, verbose_name=_("region"), null=True, blank=True, on_delete=models.SET_NULL)
    dtype = models.ForeignKey(DisasterType, verbose_name=_("disaster type"), null=True, blank=True, on_delete=models.SET_NULL)
    event = models.ForeignKey(Event, verbose_name=_("event"), null=True, blank=True, on_delete=models.SET_NULL)

    lookup_id = models.CharField(verbose_name=_("lookup id"), max_length=20, null=True, blank=True, editable=False)

    class Meta:
        verbose_name = _("Subscription")
        verbose_name_plural = _("Subscriptions")

    # Given a request containing new subscriptions, validate and
    # sync the subscriptions.
    def sync_user_subscriptions(user, body, deletePrevious):
        rtype_map = {
            "event": RecordType.EVENT,
            "appeal": RecordType.APPEAL,
            "fieldReport": RecordType.FIELD_REPORT,
            "surge": RecordType.SURGE_ALERT,
            "country": RecordType.COUNTRY,
            "region": RecordType.REGION,
            "disasterType": RecordType.DTYPE,
            "perDueDate": RecordType.PER_DUE_DATE,
            "followedEvent": RecordType.FOLLOWED_EVENT,
            "surgeDM": RecordType.SURGE_DEPLOYMENT_MESSAGES,
            "surgeAEM": RecordType.SURGE_APPROACHING_END_OF_MISSION,
            "weeklyDigest": RecordType.WEEKLY_DIGEST,
            "newEmergencies": RecordType.NEW_EMERGENCIES,
            "newOperations": RecordType.NEW_OPERATIONS,
            "general": RecordType.GENERAL_ANNOUNCEMENTS,
        }

        stype_map = {
            "new": SubscriptionType.NEW,
            "modified": SubscriptionType.EDIT,
        }

        new = []
        errors = []
        for req in body:
            rtype = rtype_map.get(req["type"], None)
            fields = {"rtype": rtype, "user": user}
            error = None

            if rtype in [RecordType.EVENT, RecordType.APPEAL, RecordType.FIELD_REPORT]:
                fields["stype"] = stype_map.get(req["value"], 0)

            elif rtype == RecordType.COUNTRY:
                try:
                    fields["country"] = Country.objects.get(pk=req["value"])
                except Country.DoesNotExist:
                    error = "Could not find country with primary key %s" % req["value"]
                fields["lookup_id"] = "c%s" % req["value"]

            elif rtype == RecordType.REGION:
                try:
                    fields["region"] = Region.objects.get(pk=req["value"])
                except Region.DoesNotExist:
                    error = "Could not find region with primary key %s" % req["value"]
                fields["lookup_id"] = "r%s" % req["value"]

            elif rtype == RecordType.DTYPE:
                try:
                    fields["dtype"] = DisasterType.objects.get(pk=req["value"])
                except DisasterType.DoesNotExist:
                    error = "Could not find disaster type with primary key %s" % req["value"]
                fields["lookup_id"] = "d%s" % req["value"]

            elif rtype == RecordType.FOLLOWED_EVENT:
                lookup_id = "e%s" % req["value"]
                if Subscription.objects.filter(user=user, lookup_id=lookup_id) and not deletePrevious:
                    # We check existence only when the previous subscriptions are not to be deleted (add only 1!)
                    # In this case there is no need to continue the for loop. See ¤ below.
                    new = []  # Not needed in ordinary cases, just a defense for malicious "halfway set data" sending
                    break
                else:
                    try:
                        fields["event"] = Event.objects.get(pk=req["value"])
                    except Event.DoesNotExist:
                        error = "Could not find followed emergency with primary key %s" % req["value"]
                    fields["lookup_id"] = "e%s" % req["value"]

            elif rtype == RecordType.PER_DUE_DATE:
                fields["stype"] = SubscriptionType.NEW

            elif rtype == RecordType.SURGE_ALERT:
                fields["stype"] = SubscriptionType.NEW

            elif rtype == RecordType.SURGE_DEPLOYMENT_MESSAGES:
                fields["stype"] = SubscriptionType.NEW

            elif rtype == RecordType.SURGE_APPROACHING_END_OF_MISSION:
                fields["stype"] = SubscriptionType.NEW

            elif rtype == RecordType.WEEKLY_DIGEST:
                fields["stype"] = SubscriptionType.NEW

            elif rtype == RecordType.NEW_EMERGENCIES:
                fields["stype"] = SubscriptionType.NEW

            elif rtype == RecordType.NEW_OPERATIONS:
                fields["stype"] = SubscriptionType.NEW

            elif rtype == RecordType.GENERAL_ANNOUNCEMENTS:
                fields["stype"] = SubscriptionType.NEW

            else:
                error = ("Record type is not valid, must be one of %s" % ", ".join(list(rtype_map.keys())),)

            if error is not None:
                errors.append(
                    {
                        "error": error,
                        "record": req,
                    }
                )
            else:
                new.append(Subscription(**fields))

        # Only sync subscriptions if the entire request is valid
        # We do this by just throwing out the old and creating the new – except in case of adding 1 new event to follow
        if not len(errors):
            if deletePrevious:
                Subscription.objects.filter(user=user).delete()
            if len(new):
                # When we try to add 1 new event which already exists, then "new" remains empty due to the above ¤ break.
                Subscription.objects.bulk_create(new)

        return errors, new

    def del_user_subscriptions(user, body):
        req = body[0]
        errors = []
        error = None
        if "value" in req:
            lookup_id = "e%s" % req["value"]
            if Subscription.objects.filter(user=user, lookup_id=lookup_id):
                try:
                    Subscription.objects.filter(user=user, lookup_id=lookup_id).delete()
                except Subscription.DoesNotExist:
                    error = "Could not remove followed subscription with lookup_id %s" % lookup_id
        elif "perDueDate" in req:
            if Subscription.objects.filter(user=user, rtype=RecordType.PER_DUE_DATE):
                try:
                    Subscription.objects.filter(user=user, rtype=RecordType.PER_DUE_DATE).delete()
                except Subscription.DoesNotExist:
                    error = "Could not remove PER_DUE_DATE subscription"
        else:
            error = "Wrong deletion format, value or perDueDate should be given."

        if error is not None:
            errors.append(
                {
                    "error": error,
                    "record": req,
                }
            )

        return errors

    def __str__(self):
        return "%s %s (%s)" % (self.user.username, self.rtype, self.user.email)


class NotificationGUID(models.Model):
    """Email GUIDs from the sender API"""

    created_at = models.DateTimeField(auto_now_add=True)
    api_guid = models.CharField(
        max_length=200, help_text="Can be used to do a GET request to check on the email sender API side."
    )
    email_type = models.CharField(max_length=600, null=True, blank=True)
    to_list = models.TextField(null=True, blank=True)


class HazardType(models.Model):
    """Model representing a hazard category."""

    class Type(models.IntegerChoices):
        EARTHQUAKE = 100, _("Earthquake")
        FLOOD = 200, _("Flood")
        CYCLONE = 300, _("Cyclone")

    type = models.IntegerField(
        choices=Type.choices,
        unique=True,
        verbose_name=_("Hazard Type"),
    )

    class Meta:
        verbose_name = _("Hazard Type")
        verbose_name_plural = _("Hazard Types")

    def __str__(self):
        return self.get_type_display()


class AlertSubscription(models.Model):
    class AlertSource(models.IntegerChoices):
        MONTANDON = 100, _("Montandon")
        """Alerts provided by the Montandon platform."""

    class AlertPerDay(models.IntegerChoices):
        """Enum representing the maximum number of alerts per day."""

        FIVE = 100, _("Five")
        """Receive up to 5 alerts per day."""

        TEN = 200, _("Ten")
        """Receive up to 10 alerts per day."""

        TWENTY = 300, _("Twenty")
        """Receive up to 20 alerts per day."""

        FIFTY = 400, _("Fifty")
        """Receive up to 50 alerts per day."""

        UNLIMITED = 500, _("Unlimited")
        """No daily alert limit."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("User"),
        on_delete=models.CASCADE,
        related_name="alert_subscriptions_user",
    )
    countries = models.ManyToManyField(
        Country,
        related_name="alert_subscriptions_countries",
        verbose_name=_("Countries"),
    )
    regions = models.ManyToManyField(
        Region,
        related_name="alert_subscriptions_regions",
        blank=True,
        verbose_name=_("Regions"),
    )
    alert_source = models.IntegerField(
        choices=AlertSource.choices,
        default=AlertSource.MONTANDON,
        verbose_name=_("Alert Source"),
    )

    hazard_types = models.ManyToManyField(
        HazardType,
        related_name="alert_subscriptions_hazard_types",
        verbose_name=_("Hazard Types"),
        help_text="Types of hazards the user is subscribed to.",
    )
    alert_per_day = models.IntegerField(
        choices=AlertPerDay.choices,
        default=AlertPerDay.FIVE,
        verbose_name=_("Alerts Per Day"),
        help_text="Maximum number of alerts sent to the user per day.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    # Typing
    id = int

    class Meta:
        ordering = ["-id"]
        verbose_name = _("Alert Subscription")
        verbose_name_plural = _("Alert Subscriptions")

    def __str__(self):
        return f"Alert subscription for {self.user}"
