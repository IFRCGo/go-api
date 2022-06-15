from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.db import models
from django.utils import timezone
from enumfields import EnumIntegerField
from enumfields import IntEnum
from api.models import Country, Region, Event, DisasterType
from deployments.models import MolnixTag

class SurgeAlertType(IntEnum):
    FACT = 0
    SIMS = 1
    ERU = 2
    DHEOPS = 3
    HEOPS = 4
    SURGE = 5
    RAPID_RESPONSE = 6

    class Labels:
        FACT = _('fact')
        SIMS = _('SIMS')
        ERU = _('ERU')
        DHEOPS = _('DHEOPS')
        HEOPS = _('HEOPS')
        SURGE = _('surge')
        RAPID_RESPONSE = _('rapid response')


class SurgeAlertCategory(IntEnum):
    INFO = 0
    DEPLOYMENT = 1
    ALERT = 2
    SHELTER = 3
    STAND_DOWN = 4

    class Labels:
        INFO = _('information')
        DEPLOYMENT = _('deployment')
        ALERT = _('alert')
        SHELTER = _('shelter')
        STAND_DOWN = _('stand down')


class SurgeAlert(models.Model):

    atype = EnumIntegerField(SurgeAlertType, verbose_name=_('alert type'), default=0)
    category = EnumIntegerField(SurgeAlertCategory, verbose_name=_('category'), default=0)
    operation = models.CharField(verbose_name=_('operation'), max_length=100)
    message = models.TextField(verbose_name=_('message'))
    deployment_needed = models.BooleanField(verbose_name=_('deployment needed'), default=False)
    is_private = models.BooleanField(verbose_name=_('is private?'), default=False)
    event = models.ForeignKey(Event, verbose_name=_('event'), null=True, blank=True, on_delete=models.SET_NULL)
    country = models.ForeignKey(Country, verbose_name=_('country'), null=True, blank=True, on_delete=models.SET_NULL)
    # Fields specific to Molnix integration:
    # ID in Molnix system, if parsed from Molnix.
    molnix_id = models.IntegerField(blank=True, null=True)

    # Status field from Molnix - `unfilled` denotes Stood-Down
    molnix_status = models.CharField(blank=True, null=True, max_length=32)    

    # It depends on molnix_status. Check "save" method below.
    is_stood_down = models.BooleanField(verbose_name=_('is stood down?'), default=False)
    opens = models.DateTimeField(blank=True, null=True)
    closes = models.DateTimeField(blank=True, null=True)
    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    molnix_tags = models.ManyToManyField(MolnixTag, blank=True)

    # Set to inactive when position is no longer in Molnix
    is_active = models.BooleanField(default=True)

    # Don't set `auto_now_add` so we can modify it on save
    created_at = models.DateTimeField(verbose_name=_('created at'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Surge Alert')
        verbose_name_plural = _('Surge Alerts')

    def save(self, *args, **kwargs):
        # On save, if `created` is not set, make it the current time
        if (not self.id and not self.created_at) or (self.created_at > timezone.now()):
            self.created_at = timezone.now()
        self.is_stood_down = self.molnix_status == 'unfilled'
        return super(SurgeAlert, self).save(*args, **kwargs)

    def __str__(self):
        if self.operation and self.operation != '':
            return self.operation
        else:
            return self.event.name


class SubscriptionType(IntEnum):
    """ New or edit to existing record """
    NEW = 0
    EDIT = 1

    class Labels:
        NEW = _('new')
        EDIT = _('edit')


class RecordType(IntEnum):
    """ Types of notifications a user can subscribe to """
    EVENT = 0         # not to use in rtype_of_subscr, migrated to NEW_EMERGENCIES
    APPEAL = 1        # not to use in rtype_of_subscr, migrated to                 NEW_OPERATIONS
    FIELD_REPORT = 2  # not to use in rtype_of_subscr, migrated to NEW_EMERGENCIES
    SURGE_ALERT = 3
    COUNTRY = 4
    REGION = 5
    DTYPE = 6
    PER_DUE_DATE = 7
    FOLLOWED_EVENT = 8
    SURGE_DEPLOYMENT_MESSAGES = 9
    SURGE_APPROACHING_END_OF_MISSION = 10
    WEEKLY_DIGEST = 11
    NEW_EMERGENCIES = 12
    NEW_OPERATIONS = 13
    GENERAL_ANNOUNCEMENTS = 14

    class Labels:
        EVENT = _('event')
        APPEAL = _('appeal')
        FIELD_REPORT = _('field report')
        SURGE_ALERT = _('surge alert')
        COUNTRY = _('country')
        REGION = _('region')
        DTYPE = _('disaster type')
        PER_DUE_DATE = _('per due date')
        FOLLOWED_EVENT = _('followed event')
        SURGE_DEPLOYMENT_MESSAGES = _('surge deployment messages')
        SURGE_APPROACHING_END_OF_MISSION = _('surge approaching end of mission')
        WEEKLY_DIGEST = _('weekly digest')
        NEW_EMERGENCIES = _('new emergencies')
        NEW_OPERATIONS = _('new operations')
        GENERAL_ANNOUNCEMENTS = _('general announcements')

# Migration
# update      notification_subscription set rtype=12, stype=0 where rtype=0; -- EVENT    > EMERGENCY
# delete from notification_subscription                       where rtype=0; -- EVENT    > EMERGENCY
# update      notification_subscription set rtype=13, stype=0 where rtype=1; -- APPEAL   >            OPERATION
# delete from notification_subscription                       where rtype=1; -- APPEAL   >            OPERATION
# update      notification_subscription set rtype=12, stype=0 where rtype=2; -- FIELDREP > EMERGENCY
# delete from notification_subscription                       where rtype=2; -- FIELDREP > EMERGENCY


class Subscription(models.Model):
    """ User subscriptions """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('user'),
        on_delete=models.CASCADE,
        related_name='subscription',
    )

    stype = EnumIntegerField(SubscriptionType, verbose_name=_('subscription type'), default=0)
    rtype = EnumIntegerField(RecordType, verbose_name=_('record type'), default=0)

    country = models.ForeignKey(Country, verbose_name=_('country'), null=True, blank=True, on_delete=models.SET_NULL)
    region = models.ForeignKey(Region, verbose_name=_('region'), null=True, blank=True, on_delete=models.SET_NULL)
    dtype = models.ForeignKey(DisasterType, verbose_name=_('disaster type'), null=True, blank=True, on_delete=models.SET_NULL)
    event = models.ForeignKey(Event, verbose_name=_('event'), null=True, blank=True, on_delete=models.SET_NULL)

    lookup_id = models.CharField(verbose_name=_('lookup id'), max_length=20, null=True, blank=True, editable=False)

    class Meta:
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')

    # Given a request containing new subscriptions, validate and
    # sync the subscriptions.
    def sync_user_subscriptions(user, body, deletePrevious):
        rtype_map = {
            'event': RecordType.EVENT,
            'appeal': RecordType.APPEAL,
            'fieldReport': RecordType.FIELD_REPORT,
            'surge': RecordType.SURGE_ALERT,
            'country': RecordType.COUNTRY,
            'region': RecordType.REGION,
            'disasterType': RecordType.DTYPE,
            'perDueDate': RecordType.PER_DUE_DATE,
            'followedEvent': RecordType.FOLLOWED_EVENT,
            'surgeDM': RecordType.SURGE_DEPLOYMENT_MESSAGES,
            'surgeAEM': RecordType.SURGE_APPROACHING_END_OF_MISSION,
            'weeklyDigest': RecordType.WEEKLY_DIGEST,
            'newEmergencies': RecordType.NEW_EMERGENCIES,
            'newOperations': RecordType.NEW_OPERATIONS,
            'general': RecordType.GENERAL_ANNOUNCEMENTS,
        }

        stype_map = {
            'new': SubscriptionType.NEW,
            'modified': SubscriptionType.EDIT,
        }

        new = []
        errors = []
        for req in body:
            rtype = rtype_map.get(req['type'], None)
            fields = {'rtype': rtype, 'user': user}
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
                    new = []  # Not needed in ordinary cases, just a defense for malicious "halfway set data" sending
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

            elif rtype == RecordType.SURGE_DEPLOYMENT_MESSAGES:
                fields['stype'] = SubscriptionType.NEW

            elif rtype == RecordType.SURGE_APPROACHING_END_OF_MISSION:
                fields['stype'] = SubscriptionType.NEW

            elif rtype == RecordType.WEEKLY_DIGEST:
                fields['stype'] = SubscriptionType.NEW

            elif rtype == RecordType.NEW_EMERGENCIES:
                fields['stype'] = SubscriptionType.NEW

            elif rtype == RecordType.NEW_OPERATIONS:
                fields['stype'] = SubscriptionType.NEW

            elif rtype == RecordType.GENERAL_ANNOUNCEMENTS:
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

    def del_user_subscriptions(user, body):
        req = body[0]
        errors = []
        error = None
        if 'value' in req:
            lookup_id = 'e%s' % req['value']
            if Subscription.objects.filter(user=user, lookup_id=lookup_id):
                try:
                    Subscription.objects.filter(user=user, lookup_id=lookup_id).delete()
                except Subscription.DoesNotExist:
                    error = 'Could not remove followed subscription with lookup_id %s' % lookup_id
        elif 'perDueDate' in req:
            if Subscription.objects.filter(user=user, rtype=RecordType.PER_DUE_DATE):
                try:
                    Subscription.objects.filter(user=user, rtype=RecordType.PER_DUE_DATE).delete()
                except Subscription.DoesNotExist:
                    error = 'Could not remove PER_DUE_DATE subscription'
        else:
            error = 'Wrong deletion format, value or perDueDate should be given.'

        if error is not None:
            errors.append({
                'error': error,
                'record': req,
            })

        return errors

    def __str__(self):
        return '%s %s (%s)' % (self.user.username, self.rtype, self.user.email)


class NotificationGUID(models.Model):
    """ Email GUIDs from the sender API """
    created_at = models.DateTimeField(auto_now_add=True)
    api_guid = models.CharField(max_length=200,
                                help_text='Can be used to do a GET request to check on the email sender API side.')
    email_type = models.CharField(max_length=600, null=True, blank=True)
    to_list = models.TextField(null=True, blank=True)
