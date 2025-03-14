import time

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.crypto import get_random_string

from api.management.commands.index_and_notify import Command as Notify
from notifications.models import (
    Country,
    DisasterType,
    RecordType,
    Region,
    Subscription,
    SubscriptionType,
)

from .models import Appeal, FieldReport


def get_user():
    user_number = get_random_string(8)
    username = "user%s" % user_number
    email = "%s@email.com" % username
    return User.objects.create(username=username, password="12345678", email=email)


class FieldReportNotificationTest(TestCase):
    def setUp(self):
        region = Region.objects.create(name=1)
        country1 = Country.objects.create(name="c1", region=region)
        country2 = Country.objects.create(name="c2")
        dtype = DisasterType.objects.create(name="d1", summary="foo")
        report = FieldReport.objects.create(
            rid="test",
            dtype=dtype,
        )
        report.countries.add(country1)
        report.countries.add(country2)

    def test_new_record_subscription(self):
        # Subscription to NEW_EMERGENCIES (orig: new field reports)
        user = get_user()
        Subscription.objects.create(
            user=user,
            rtype=RecordType.NEW_EMERGENCIES,  # FIELD_REPORT,
            stype=SubscriptionType.NEW,
        )
        notify = Notify()
        emails = notify.gather_subscribers(
            FieldReport.objects.filter(created_at__gte=notify.diff_5_minutes()),
            RecordType.NEW_EMERGENCIES,  # FIELD_REPORT,
            SubscriptionType.NEW,
        )
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0], user.email)

    def test_country_subscription(self):
        # Subscription to a country
        user = get_user()
        Subscription.objects.create(
            user=user,
            rtype=RecordType.NEW_EMERGENCIES,  # FIELD_REPORT,
            stype=SubscriptionType.NEW,
        )
        c = Country.objects.get(name="c2")
        Subscription.objects.create(
            user=user,
            country=c,
            lookup_id="c%s" % c.id,
        )
        notify = Notify()
        emails = notify.gather_subscribers(
            FieldReport.objects.filter(created_at__gte=notify.diff_5_minutes()),
            RecordType.NEW_EMERGENCIES,  # FIELD_REPORT,
            SubscriptionType.NEW,
        )
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0], user.email)

    def test_region_subscription(self):
        # Subscription to a region
        user = get_user()
        Subscription.objects.create(
            user=user,
            rtype=RecordType.NEW_EMERGENCIES,  # FIELD_REPORT,
            stype=SubscriptionType.NEW,
        )
        r = Region.objects.get(name=1)
        Subscription.objects.create(
            user=user,
            region=r,
            lookup_id="r%s" % r.id,
        )
        notify = Notify()
        emails = notify.gather_subscribers(
            FieldReport.objects.filter(created_at__gte=notify.diff_5_minutes()),
            RecordType.NEW_EMERGENCIES,  # FIELD_REPORT,
            SubscriptionType.NEW,
        )
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0], user.email)

    def test_dtype_subscription(self):
        # Subscription to a disaster type
        user = get_user()
        Subscription.objects.create(
            user=user,
            rtype=RecordType.NEW_EMERGENCIES,  # FIELD_REPORT,
            stype=SubscriptionType.NEW,
        )
        d = DisasterType.objects.get(name="d1")
        Subscription.objects.create(
            user=user,
            dtype=d,
            lookup_id="d%s" % d.id,
        )
        notify = Notify()
        emails = notify.gather_subscribers(
            FieldReport.objects.filter(created_at__gte=notify.diff_5_minutes()),
            RecordType.NEW_EMERGENCIES,  # FIELD_REPORT,
            SubscriptionType.NEW,
        )
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0], user.email)

    def test_multiple_subscription(self):
        user1 = get_user()
        user2 = get_user()

        Subscription.objects.create(
            user=user1,
            rtype=RecordType.NEW_EMERGENCIES,  # FIELD_REPORT,
            stype=SubscriptionType.NEW,
        )

        Subscription.objects.create(
            user=user2,
            rtype=RecordType.NEW_EMERGENCIES,  # FIELD_REPORT,
            stype=SubscriptionType.NEW,
        )

        d = DisasterType.objects.get(name="d1")
        r = Region.objects.get(name=1)

        # User 1: Disaster type subscription
        Subscription.objects.create(
            user=user1,
            dtype=d,
            lookup_id="d%s" % d.id,
        )

        # User 1: Region subscription
        Subscription.objects.create(
            user=user1,
            region=r,
            lookup_id="r%s" % r.id,
        )

        # User 2: NEW_EMERGENCIES subscription (instead of the original New field report subscription)
        Subscription.objects.create(
            user=user2,
            rtype=RecordType.NEW_EMERGENCIES,  # FIELD_REPORT,
            stype=SubscriptionType.NEW,
        )

        notify = Notify()
        emails = notify.gather_subscribers(
            FieldReport.objects.filter(created_at__gte=notify.diff_5_minutes()),
            RecordType.NEW_EMERGENCIES,  # FIELD_REPORT,
            SubscriptionType.NEW,
        )
        self.assertEqual(len(emails), 2)
        self.assertEqual(emails.sort(), [user1.email, user2.email].sort())


class AppealNotificationTest(TestCase):
    def setUp(self):
        region = Region.objects.create(name="1")
        country1 = Country.objects.create(name="1", region=region)
        country2 = Country.objects.create(name="2", region=region)
        dtype = DisasterType.objects.create(name="1")

        # Country 1 appeal
        Appeal.objects.create(aid="test1", name="appeal", atype=1, code="1", dtype=dtype, country=country1)

        # Country 2 appeal
        Appeal.objects.create(aid="test2", name="appeal", atype=2, code="2", dtype=dtype, country=country2)

    def test_region_subscription(self):
        user = get_user()
        Subscription.objects.create(
            user=user,
            rtype=RecordType.NEW_OPERATIONS,
            stype=SubscriptionType.NEW,
        )
        r = Region.objects.get(name="1")
        Subscription.objects.create(user=user, region=r, lookup_id="r%s" % r.id)
        notify = Notify()
        emails = notify.gather_subscribers(
            Appeal.objects.filter(created_at__gte=notify.diff_5_minutes()),
            RecordType.APPEAL,
            SubscriptionType.NEW,
        )
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0], user.email)

    def test_region_and_country_subscription(self):
        user = get_user()
        Subscription.objects.create(
            user=user,
            rtype=RecordType.NEW_OPERATIONS,
            stype=SubscriptionType.NEW,
        )
        r = Region.objects.get(name="1")
        c = Country.objects.get(name="2")
        Subscription.objects.create(user=user, region=r, lookup_id="r%s" % r.id)
        Subscription.objects.create(user=user, country=c, lookup_id="c%s" % c.id)
        notify = Notify()
        emails = notify.gather_subscribers(
            Appeal.objects.filter(created_at__gte=notify.diff_5_minutes()),
            RecordType.APPEAL,
            SubscriptionType.NEW,
        )
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0], user.email)


class FilterJustCreatedTest(TestCase):
    def setUp(self):
        # create two appeals, modify one 2 seconds later.
        region = Region.objects.create(name="1")
        country1 = Country.objects.create(name="1", region=region)
        country2 = Country.objects.create(name="2", region=region)
        appeal1 = Appeal.objects.create(aid="test1", name="appeal", atype=2, code="1", country=country1)
        Appeal.objects.create(aid="test2", name="appeal", atype=2, code="2", country=country2)
        time.sleep(1)
        appeal1.name = "something new"
        appeal1.save()

    def test_filter_just_created(self):
        notify = Notify()
        filtered = notify.filter_just_created(Appeal.objects.filter(created_at__gte=notify.diff_5_minutes()))
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].aid, "test2")
