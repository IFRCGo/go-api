from unittest import mock
from uuid import uuid4

from django.test import TestCase
from django.utils import timezone

from alert_system.email_processing import process_email_alert
from alert_system.models import AlertEmailLog, AlertEmailThread, Connector
from api.factories.country import CountryFactory
from api.factories.disaster_type import DisasterTypeFactory
from api.factories.region import RegionFactory
from deployments.factories.user import UserFactory
from notifications.factories import AlertSubscriptionFactory
from notifications.models import AlertSubscription

from .factories import (
    AlertEmailLogFactory,
    AlertEmailThreadFactory,
    ConnectorFactory,
    LoadItemFactory,
)


class AlertEmailNotificationTestCase(TestCase):
    """Comprehensive test suite for alert email notifications (both root and reply emails)"""

    def setUp(self):
        self.user1 = UserFactory.create(email="testuser1@example.com")
        self.user2 = UserFactory.create(email="testuser2@example.com")

        self.region = RegionFactory.create()
        self.country = CountryFactory.create(
            name="Nepal",
            iso3="NEP",
            iso="NP",
            region=self.region,
        )

        self.hazard_type = DisasterTypeFactory.create(name="Flood")

        self.connector = ConnectorFactory.create(
            type=Connector.ConnectorType.GDACS_FLOOD,
            dtype=self.hazard_type,
            status=Connector.Status.SUCCESS,
            source_url="https://test.com/stac",
        )

        self.subscription1 = AlertSubscriptionFactory.create(
            user=self.user1,
            countries=[self.country],
            hazard_types=[self.hazard_type],
            alert_per_day=AlertSubscription.AlertPerDay.FIVE,
        )

        self.subscription2 = AlertSubscriptionFactory.create(
            user=self.user2,
            countries=[self.country],
            hazard_types=[self.hazard_type],
            alert_per_day=AlertSubscription.AlertPerDay.FIVE,
        )

        self.eligible_item = LoadItemFactory.create(
            parent_guid=str(uuid4()),
            connector=self.connector,
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Test Flood Event",
            event_description="Initial flood event",
            country_codes=["NEP"],
            total_people_exposed=10,
            total_buildings_exposed=5,
            impact_metadata={
                "summary": "Test impact metadata",
                "source": "unit-test",
            },
        )

        self.ineligible_item = LoadItemFactory.create(
            connector=self.connector,
            item_eligible=False,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Test Event",
            country_codes=["IND"],
            event_description="Should not trigger email",
            total_people_exposed=10,
            total_buildings_exposed=5,
            impact_metadata={
                "summary": "Test impact metadata",
                "source": "unit-test",
            },
        )

    @mock.patch("alert_system.email_processing.send_notification")
    def test_sent_email_for_eligible_item(self, mock_send_notification):

        process_email_alert(self.eligible_item.id)

        log = AlertEmailLog.objects.get(user=self.user1, item=self.eligible_item)
        thread = AlertEmailThread.objects.get(user=self.user1)

        self.assertEqual(log.user, self.user1)
        self.assertEqual(log.item, self.eligible_item)
        self.assertEqual(log.subscription, self.subscription1)
        self.assertEqual(log.status, AlertEmailLog.Status.SENT)
        self.assertIsNotNone(log.email_sent_at)

        self.assertEqual(thread.user, self.user1)
        self.assertEqual(thread.parent_guid, self.eligible_item.parent_guid)
        self.assertEqual(thread.root_email_message_id, log.message_id)
        self.assertEqual(log.thread, thread)

        mock_send_notification.assert_called()

    @mock.patch("alert_system.email_processing.send_notification")
    def test_sent_email_to_multiple_users(self, mock_send_notification):

        process_email_alert(self.eligible_item.id)

        logs = AlertEmailLog.objects.filter(item=self.eligible_item, status=AlertEmailLog.Status.SENT)
        self.assertEqual(logs.count(), 2)

        threads = AlertEmailThread.objects.filter(parent_guid=self.eligible_item.parent_guid)
        self.assertEqual(threads.count(), 2)

        self.assertEqual(mock_send_notification.call_count, 2)

        # Verify each user got their own thread
        user1_log = logs.get(user=self.user1)
        user2_log = logs.get(user=self.user2)
        user1_thread = threads.get(user=self.user1)
        user2_thread = threads.get(user=self.user2)

        self.assertEqual(user1_log.thread, user1_thread)
        self.assertEqual(user2_log.thread, user2_thread)
        self.assertNotEqual(user1_thread.root_email_message_id, user2_thread.root_email_message_id)

    @mock.patch("alert_system.email_processing.send_notification")
    def test_daily_email_alert_limit(self, mock_send_notification):

        user = UserFactory.create(email="t@example.com")
        country = CountryFactory.create(
            name="Philippines",
            iso3="PHI",
            iso="PH",
            region=self.region,
        )

        subscription = AlertSubscriptionFactory.create(
            user=user,
            countries=[country],
            hazard_types=[self.hazard_type],
            alert_per_day=AlertSubscription.AlertPerDay.FIVE,
        )

        item = LoadItemFactory.create(
            connector=self.connector,
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Test Flood Event",
            country_codes=["PHI"],
            event_description="Should not trigger email",
            total_people_exposed=10,
            total_buildings_exposed=5,
            impact_metadata={
                "summary": "Test impact metadata",
                "source": "unit-test",
            },
        )

        for _ in range(subscription.alert_per_day):
            AlertEmailLogFactory.create(
                user=user,
                subscription=subscription,
                item=item,
                status=AlertEmailLog.Status.SENT,
                email_sent_at=timezone.now(),
                message_id=uuid4(),
            )

        sent_before = AlertEmailLog.objects.filter(
            user=user,
            subscription=subscription,
            status=AlertEmailLog.Status.SENT,
        ).count()

        process_email_alert(item.id)

        sent_after = AlertEmailLog.objects.filter(
            user=user,
            subscription=subscription,
            status=AlertEmailLog.Status.SENT,
        ).count()

        self.assertEqual(sent_before, sent_after)
        mock_send_notification.assert_not_called()

    # Test Reply emails

    @mock.patch("alert_system.email_processing.send_notification")
    def test_reply_email_for_existing_thread(self, mock_send_notification):
        user = UserFactory.create()
        country = CountryFactory.create(
            name="China",
            iso3="CHN",
            iso="CH",
            region=self.region,
        )

        subscription = AlertSubscriptionFactory.create(
            user=user,
            countries=[country],
            hazard_types=[self.hazard_type],
            alert_per_day=AlertSubscription.AlertPerDay.FIVE,
        )

        initial_item = LoadItemFactory.create(
            parent_guid=str(uuid4()),
            connector=self.connector,
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Initial Flood",
            country_codes=["CHN"],
            total_people_exposed=10,
            total_buildings_exposed=5,
            impact_metadata={"summary": "Initial", "source": "unit-test"},
        )

        thread = AlertEmailThreadFactory.create(
            user=user,
            parent_guid=initial_item.parent_guid,
            root_email_message_id=str(uuid4()),
            root_message_sent_at=timezone.now(),
        )

        AlertEmailLogFactory.create(
            user=user,
            subscription=subscription,
            item=initial_item,
            thread=thread,
            message_id=str(uuid4()),
            status=AlertEmailLog.Status.SENT,
            email_sent_at=timezone.now(),
        )

        update_item = LoadItemFactory.create(
            parent_guid=initial_item.parent_guid,
            connector=self.connector,
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Flood Update",
            country_codes=["CHN"],
            total_people_exposed=20,
            total_buildings_exposed=10,
            impact_metadata={"summary": "Update", "source": "unit-test"},
        )

        process_email_alert(update_item.id)

        reply_log = AlertEmailLog.objects.get(user=user, item=update_item)
        self.assertEqual(reply_log.status, AlertEmailLog.Status.SENT)
        self.assertIsNotNone(reply_log.email_sent_at)

        mock_send_notification.assert_called_once()

        threads = AlertEmailThread.objects.filter(parent_guid=initial_item.parent_guid)
        self.assertEqual(threads.count(), 1)

    @mock.patch("alert_system.email_processing.send_notification")
    def test_reply_email_to_multiple_users(self, mock_send_notification):

        parent_guid = str(uuid4())

        # Create initial item
        initial_item = LoadItemFactory.create(
            parent_guid=parent_guid,
            connector=self.connector,
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Initial Event",
            country_codes=["NEP"],
            total_people_exposed=10,
            total_buildings_exposed=5,
            impact_metadata={"summary": "Initial", "source": "unit-test"},
        )

        # Create threads for both users
        thread1 = AlertEmailThreadFactory.create(
            user=self.user1,
            parent_guid=parent_guid,
            root_email_message_id="message-id-1",
            root_message_sent_at=timezone.now(),
        )

        thread2 = AlertEmailThreadFactory.create(
            user=self.user2,
            parent_guid=parent_guid,
            root_email_message_id="message-id-2",
            root_message_sent_at=timezone.now(),
        )

        AlertEmailLogFactory.create(
            user=self.user1,
            subscription=self.subscription1,
            item=initial_item,
            thread=thread1,
            message_id="message-id-1",
            status=AlertEmailLog.Status.SENT,
            email_sent_at=timezone.now(),
        )

        AlertEmailLogFactory.create(
            user=self.user2,
            subscription=self.subscription2,
            item=initial_item,
            thread=thread2,
            message_id="message-id-2",
            status=AlertEmailLog.Status.SENT,
            email_sent_at=timezone.now(),
        )

        related_item = LoadItemFactory.create(
            parent_guid=parent_guid,
            connector=self.connector,
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Update Event",
            country_codes=["NEP"],
            total_people_exposed=20,
            total_buildings_exposed=10,
            impact_metadata={"summary": "Update", "source": "test"},
        )

        process_email_alert(related_item.id)

        replies = AlertEmailLog.objects.filter(item=related_item, status=AlertEmailLog.Status.SENT)
        self.assertEqual(replies.count(), 2)
        self.assertEqual(mock_send_notification.call_count, 2)

        reply_user1 = replies.get(user=self.user1)
        reply_user2 = replies.get(user=self.user2)
        self.assertNotEqual(reply_user1.message_id, reply_user2.message_id)

    @mock.patch("alert_system.email_processing.send_notification")
    def test_duplicate_reply(self, mock_send_notification):

        parent_guid = str(uuid4())

        user = UserFactory.create()
        country = CountryFactory.create(
            name="Pakistan",
            iso3="PAK",
            region=self.region,
        )
        subscription = AlertSubscriptionFactory.create(
            user=user,
            countries=[country],
            hazard_types=[self.hazard_type],
            alert_per_day=AlertSubscription.AlertPerDay.FIVE,
        )

        LoadItemFactory.create(
            parent_guid=parent_guid,
            connector=self.connector,
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Initial",
            country_codes=["PAK"],
            total_people_exposed=10,
            total_buildings_exposed=5,
            impact_metadata={"summary": "Initial", "source": "unit-test"},
        )

        thread = AlertEmailThreadFactory.create(
            user=user,
            parent_guid=parent_guid,
            root_email_message_id="root-123",
            root_message_sent_at=timezone.now(),
        )

        update_item = LoadItemFactory.create(
            parent_guid=parent_guid,
            connector=self.connector,
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Update",
            country_codes=["PAK"],
            total_people_exposed=20,
            total_buildings_exposed=10,
            impact_metadata={"summary": "Update", "source": "unit-test"},
        )

        # Existing reply for user1
        AlertEmailLogFactory.create(
            user=user,
            subscription=subscription,
            item=update_item,
            thread=thread,
            message_id="reply-123",
            status=AlertEmailLog.Status.SENT,
            email_sent_at=timezone.now(),
        )

        user2 = UserFactory.create()
        AlertSubscriptionFactory.create(
            user=user2,
            countries=subscription.countries.all(),
            regions=subscription.regions.all(),
            hazard_types=subscription.hazard_types.all(),
            alert_per_day=subscription.alert_per_day,
        )

        process_email_alert(update_item.id)

        # user should NOT get a duplicate
        replies_user1 = AlertEmailLog.objects.filter(user=user, item=update_item)
        self.assertEqual(replies_user1.count(), 1)

        # user2 should get an email
        replies_user2 = AlertEmailLog.objects.filter(user=user2, item=update_item)
        self.assertEqual(replies_user2.count(), 1)

        mock_send_notification.assert_called_once()
