from unittest import mock
from uuid import uuid4

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from alert_system.models import AlertEmailLog, AlertEmailThread, Connector
from alert_system.tasks import process_email_alert
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
            correlation_id="corr-001",
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

    @mock.patch("alert_system.utils.send_notification")
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
        self.assertEqual(thread.correlation_id, self.eligible_item.correlation_id)
        self.assertEqual(thread.root_email_message_id, log.message_id)
        self.assertEqual(log.thread, thread)

        mock_send_notification.assert_called()

    @mock.patch("alert_system.utils.send_notification")
    def test_sent_email_to_multiple_users(self, mock_send_notification):

        process_email_alert(self.eligible_item.id)

        logs = AlertEmailLog.objects.filter(item=self.eligible_item, status=AlertEmailLog.Status.SENT)
        self.assertEqual(logs.count(), 2)

        threads = AlertEmailThread.objects.filter(correlation_id=self.eligible_item.correlation_id)
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

    @mock.patch("alert_system.utils.send_notification")
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

    @mock.patch("alert_system.utils.send_notification")
    def test_reply_email_for_existing_thread(self, mock_send_notification):

        initial_item = LoadItemFactory.create(
            correlation_id="corr-reply-001",
            connector=self.connector,
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Initial Flood",
            country_codes=["NEP"],
            total_people_exposed=10,
            total_buildings_exposed=5,
            impact_metadata={"summary": "Initial", "source": "unit-test"},
        )

        thread = AlertEmailThreadFactory.create(
            user=self.user1,
            correlation_id=initial_item.correlation_id,
            root_email_message_id="root-msg-123",
            root_message_sent_at=timezone.now(),
        )

        AlertEmailLogFactory.create(
            user=self.user1,
            subscription=self.subscription1,
            item=initial_item,
            thread=thread,
            message_id="root-msg-123",
            status=AlertEmailLog.Status.SENT,
            email_sent_at=timezone.now(),
        )

        # Create update item with same correlation_id
        update_item = LoadItemFactory.create(
            correlation_id="corr-reply-001",
            connector=self.connector,
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Flood Update",
            country_codes=["NEP"],
            total_people_exposed=20,
            total_buildings_exposed=10,
            impact_metadata={"summary": "Update", "source": "unit-test"},
        )

        process_email_alert(update_item.id)

        reply_log = AlertEmailLog.objects.get(user=self.user1, item=update_item)
        self.assertEqual(reply_log.status, AlertEmailLog.Status.SENT)
        self.assertIsNotNone(reply_log.email_sent_at)
        mock_send_notification.assert_called_once()
        # Verify no new thread was created
        threads = AlertEmailThread.objects.filter(correlation_id=initial_item.correlation_id)
        self.assertEqual(threads.count(), 1)

    @mock.patch("alert_system.utils.send_notification")
    def test_reply_email_to_multiple_users(self, mock_send_notification):

        correlation_id = str(uuid4())

        # Create initial item
        initial_item = LoadItemFactory.create(
            correlation_id=correlation_id,
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
            correlation_id=correlation_id,
            root_email_message_id="message-id-1",
            root_message_sent_at=timezone.now(),
        )

        thread2 = AlertEmailThreadFactory.create(
            user=self.user2,
            correlation_id=correlation_id,
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
            correlation_id=correlation_id,
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

    @mock.patch("alert_system.utils.send_notification")
    def test_duplicate_reply(self, mock_send_notification):

        correlation_id = "corr-dup-reply"

        LoadItemFactory.create(
            correlation_id=correlation_id,
            connector=self.connector,
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Initial",
            country_codes=["NEP"],
            total_people_exposed=10,
            total_buildings_exposed=5,
            impact_metadata={"summary": "Initial", "source": "unit-test"},
        )

        thread = AlertEmailThreadFactory.create(
            user=self.user1,
            correlation_id=correlation_id,
            root_email_message_id="root-123",
            root_message_sent_at=timezone.now(),
        )

        update_item = LoadItemFactory.create(
            correlation_id=correlation_id,
            connector=self.connector,
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Update",
            country_codes=["NEP"],
            total_people_exposed=20,
            total_buildings_exposed=10,
            impact_metadata={"summary": "Update", "source": "unit-test"},
        )

        # Create existing reply log
        AlertEmailLogFactory.create(
            user=self.user1,
            subscription=self.subscription1,
            item=update_item,
            thread=thread,
            message_id="reply-123",
            status=AlertEmailLog.Status.SENT,
            email_sent_at=timezone.now(),
        )

        process_email_alert(update_item.id)

        replies = AlertEmailLog.objects.filter(user=self.user1, item=update_item)
        self.assertEqual(replies.count(), 1)
        mock_send_notification.assert_not_called()

    @mock.patch("alert_system.utils.send_notification")
    def test_reply_email_for_daily_limit(self, mock_send_notification):

        correlation_id = "corr-limit-reply"
        LoadItemFactory.create(
            correlation_id=correlation_id,
            connector=self.connector,
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Initial",
            country_codes=["NEP"],
            total_people_exposed=10,
            total_buildings_exposed=5,
            impact_metadata={"summary": "Initial", "source": "unit-test"},
        )

        AlertEmailThreadFactory.create(
            user=self.user1,
            correlation_id=correlation_id,
            root_email_message_id="root-123",
            root_message_sent_at=timezone.now(),
        )

        for i in range(self.subscription1.alert_per_day):
            other_item = LoadItemFactory.create(
                correlation_id=f"corr-other-{i}",
                connector=self.connector,
                item_eligible=True,
                is_past_event=False,
                start_datetime=timezone.now(),
                event_title=f"Event {i}",
                country_codes=["NEP"],
                total_people_exposed=10,
                total_buildings_exposed=5,
                impact_metadata={"summary": "Test", "source": "unit-test"},
            )
            AlertEmailLogFactory.create(
                user=self.user1,
                subscription=self.subscription1,
                item=other_item,
                status=AlertEmailLog.Status.SENT,
                email_sent_at=timezone.now(),
                message_id=str(uuid4()),
            )

        related_item = LoadItemFactory.create(
            correlation_id=correlation_id,
            connector=self.connector,
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Update",
            country_codes=["NEP"],
            total_people_exposed=20,
            total_buildings_exposed=10,
            impact_metadata={"summary": "Update", "source": "unit-test"},
        )

        process_email_alert(related_item.id)

        # Should not create reply log
        reply_exists = AlertEmailLog.objects.filter(user=self.user1, item=related_item).exists()
        self.assertFalse(reply_exists)
        mock_send_notification.assert_not_called()

    @mock.patch("alert_system.utils.send_notification")
    def test_reply_without_subscription(self, mock_send_notification):

        correlation_id = str(uuid4())
        item = LoadItemFactory.create(
            correlation_id=correlation_id,
            connector=self.connector,
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Initial",
            country_codes=["NEP"],
            total_people_exposed=10,
            total_buildings_exposed=5,
            impact_metadata={"summary": "Initial", "source": "unit-test"},
        )

        AlertEmailThreadFactory.create(
            user=self.user1,
            correlation_id=correlation_id,
            root_email_message_id="root-123",
            root_message_sent_at=timezone.now(),
        )

        # Delete subscription
        self.subscription1.delete()

        process_email_alert(item.id)
        reply_exists = AlertEmailLog.objects.filter(item=item).exists()
        self.assertFalse(reply_exists)
        mock_send_notification.assert_not_called()

    # Test command trigger
    @mock.patch("alert_system.tasks.process_email_alert.delay")
    def test_command_triggers_task_for_eligible_items(self, mock_task_delay):
        """Test that management command queues eligible items"""
        call_command("alert_notification")

        mock_task_delay.assert_called_once_with(load_item_id=self.eligible_item.id)

    @mock.patch("alert_system.tasks.process_email_alert.delay")
    def test_command_for_ineligible_items(self, mock_task_delay):

        # Delete eligible item
        self.eligible_item.delete()

        call_command("alert_notification")

        mock_task_delay.assert_not_called()

    @mock.patch("alert_system.tasks.process_email_alert.delay")
    def test_command_trigger_for_past_events(self, mock_task_delay):

        self.eligible_item.is_past_event = True
        self.eligible_item.save()

        call_command("alert_notification")

        mock_task_delay.assert_not_called()

    @mock.patch("alert_system.utils.send_notification")
    def test_email_send_failed(self, mock_send_notification):

        mock_send_notification.side_effect = Exception("Email service error")

        process_email_alert(self.eligible_item.id)

        log = AlertEmailLog.objects.get(user=self.user1, item=self.eligible_item)
        self.assertEqual(log.status, AlertEmailLog.Status.FAILED)
        self.assertIsNone(log.email_sent_at)
