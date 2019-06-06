from django.conf import settings
from django.db import models
from django.utils import timezone
from enumfields import EnumIntegerField
from enumfields import IntEnum
from api.models import Country, Region, Event, DisasterType


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
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.SET_NULL)

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
    EVENT = 0
    APPEAL = 1
    FIELD_REPORT = 2
    SURGE_ALERT = 3
    COUNTRY = 4
    REGION = 5
    DTYPE = 6
    PER_DUE_DATE = 7
    FOLLOWED_EVENT = 8

class Subscription(models.Model):
    """ User subscriptions """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription',
    )

    stype = EnumIntegerField(SubscriptionType, default=0)
    rtype = EnumIntegerField(RecordType, default=0)

    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL)
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.SET_NULL)
    dtype = models.ForeignKey(DisasterType, null=True, blank=True, on_delete=models.SET_NULL)
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.SET_NULL)

    lookup_id = models.CharField(max_length=20, null=True, blank=True, editable=False)

    # Given a request containing new subscriptions, validate and
    # sync the subscriptions.
    def sync_user_subscriptions(user, body, deletePrevious):
        rtype_map = {
            'event': RecordType.EVENT,
            'appeal': RecordType.APPEAL,
            'fieldReport': RecordType.FIELD_REPORT,
            'surge': RecordType.SURGE_ALERT,
            'regions': RecordType.REGION,
            'countries': RecordType.COUNTRY,
            'disasterTypes': RecordType.DTYPE,
            'perDueDates': RecordType.PER_DUE_DATE,
            'followedEvent': RecordType.FOLLOWED_EVENT,
        }

        stype_map = {
            'new': SubscriptionType.NEW,
            'modified': SubscriptionType.EDIT,
        }

        new = []
        errors = []
        for req in body:
            rtype = rtype_map.get(req['type'], None)
            fields = { 'rtype': rtype, 'user': user }
            error = None

            if rtype in [RecordType.EVENT, RecordType.APPEAL, RecordType.FIELD_REPORT]:
                fields['stype'] = stype_map.get(req['value'], 0)

            elif rtype == RecordType.COUNTRY:
                try:
                    fields['country'] = Country.objects.get(pk=req['value'])
                except Country.DoesNotExist:
                    error = 'Could not find country with primary key %s' % req['value']
                fields['lookup_id'] = 'c%s' % req['value']

            elif rtype == RecordType.REGION:
                try:
                    fields['region'] = Region.objects.get(pk=req['value'])
                except Region.DoesNotExist:
                    error = 'Could not find region with primary key %s' % req['value']
                fields['lookup_id'] = 'r%s' % req['value']

            elif rtype == RecordType.DTYPE:
                try:
                    fields['dtype'] = DisasterType.objects.get(pk=req['value'])
                except DisasterType.DoesNotExist:
                    error = 'Could not find disaster type with primary key %s' % req['value']
                fields['lookup_id'] = 'd%s' % req['value']

            elif rtype == RecordType.FOLLOWED_EVENT:
                lookup_id = 'e%s' % req['value']
                if Subscription.objects.filter(user=user, lookup_id=lookup_id) and not deletePrevious:
                    # We check existence only when the previous subscriptions are not to be deleted (add only 1!)
                    # In this case there is no need to continue the for loop. See ¤ below.
                    new = [] # Not needed in ordinary cases, just a defense for malicious "halfway set data" sending
                    break
                else:
                    try:
                        fields['event'] = Event.objects.get(pk=req['value'])
                    except Event.DoesNotExist:
                        error = 'Could not find followed emergency with primary key %s' % req['value']
                    fields['lookup_id'] = 'e%s' % req['value']

            elif rtype == RecordType.PER_DUE_DATE:
                fields['stype'] = SubscriptionType.NEW

            elif rtype == RecordType.SURGE_ALERT:
                fields['stype'] = SubscriptionType.NEW

            else:
                error = 'Record type is not valid, must be one of %s' % ', '.join(list(rtype_map.keys())),

            if error is not None:
                errors.append({
                    'error': error,
                    'record': req,
                })
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

    def __str__(self):
        return '%s %s' % (self.user.username, self.rtype)
