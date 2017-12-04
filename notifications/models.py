from django.conf import settings
from django.db import models
from django.utils import timezone
from enumfields import EnumIntegerField
from enumfields import IntEnum


class SurgeAlertType(IntEnum):
    FACT = 0
    SIMS = 1
    ERU = 2
    DHEOPS = 3
    HEOPS = 4
    SURGE = 5


class SurgeAlertCategory(IntEnum):
    INFO = 0
    DEPLOYMENT = 1
    ALERT = 2
    SHELTER = 3
    STAND_DOWN = 4


class SurgeAlert(models.Model):
    """ Manually-entered surge alerts """
    atype = EnumIntegerField(SurgeAlertType, default=0)
    category = EnumIntegerField(SurgeAlertCategory, default=0)
    operation = models.CharField(max_length=100)
    message = models.TextField()
    deployment_needed = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)

    # Don't set `auto_now_add` so we can modify it on save
    created_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # On save, if `created` is not set, make it the current time
        if not self.id and not self.created_at:
            self.created_at = timezone.now()
        return super(SurgeAlert, self).save(*args, **kwargs)

    def __str__(self):
        return self.operation


class SubscriptionType(IntEnum):
    """ New or edit to existing record """
    NEW = 0
    EDIT = 1


class RecordType(IntEnum):
    """ Types of notifications a user can subscribe to """
    DISASTER = 0
    APPEAL = 1
    FIELD_REPORT = 2
    SURGE_ALERT = 3


class Subscription(models.Model):
    """ User subscriptions """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription',
    )

    stype = EnumIntegerField(SubscriptionType, default=0)
    rtype = EnumIntegerField(RecordType, default=0)

    def __str__(self):
        return '%s %s' % (self.user.username, self.event_type)
