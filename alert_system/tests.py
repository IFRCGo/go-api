from datetime import datetime, timedelta
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from alert_system.models import AlertEmailLog, Connector
from alert_system.tasks import send_alert_email_notification, send_alert_email_replies
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


class AlertEmailNotificationsTestCase(TestCase):

    def setUp(self):
        self.user1 = UserFactory.create(email="testuser1@com")
        self.user2 = UserFactory.create(email="testuser2@com")

        self.region = RegionFactory.create()
        self.country = CountryFactory.create(
            name="Nepal",
            iso3="NEP",
            iso="NP",
            region=self.region,
        )

        self.hazard_type1 = DisasterTypeFactory.create(name="Flood")
        self.hazard_type2 = DisasterTypeFactory.create(name="Earthquake")

        self.connector = ConnectorFactory.create(
            type=Connector.ConnectorType.GDACS_FLOOD,
            dtype=self.hazard_type1,
            status=Connector.Status.SUCCESS,
            source_url="https://test.com/stac",
        )

        self.subscription = AlertSubscriptionFactory.create(
            user=self.user1,
            countries=[self.country],
            hazard_types=[self.hazard_type1],
            alert_per_day=AlertSubscription.AlertPerDay.FIVE,
        )

        self.eligible_item = LoadItemFactory.create(
            connector=self.connector,
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Flood in Nepal",
            event_description="Heavy flooding reported",
            country_codes=["NEP"],
            total_people_exposed=100,
            total_buildings_exposed=50,
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
            event_title="Ignored Event",
            event_description="Should not trigger email",
            country_codes=["IND"],
            total_people_exposed=10,
            total_buildings_exposed=5,
            impact_metadata={
                "summary": "Test impact metadata",
                "source": "unit-test",
            },
        )

    @mock.patch("alert_system.tasks.send_alert_email_notification.delay")
    @mock.patch("alert_system.tasks.send_notification")
    def test_trigger_command_for_eligible_items(
        self,
        mock_send_notification,
        mock_send_alert_email_notification,
    ):

        call_command("alert_notification")
        # Task enqueued once with eligible item
        mock_send_alert_email_notification.assert_called_once_with(load_item_id=self.eligible_item.id)
        send_alert_email_notification(self.eligible_item.id)
        mock_send_notification.assert_called_once()
        self.assertEqual(AlertEmailLog.objects.count(), 1)

    @mock.patch("alert_system.tasks.send_notification")
    def test_alert_email_for_eligible_item(self, mock_send_notification):

        mock_send_notification.return_value = None
        send_alert_email_notification(self.eligible_item.id)
        mock_send_notification.assert_called_once()

        self.assertEqual(AlertEmailLog.objects.count(), 1)
        log = AlertEmailLog.objects.first()

        self.assertEqual(log.user, self.user1)
        self.assertEqual(log.item, self.eligible_item)
        self.assertEqual(log.subscription, self.subscription)
        self.assertEqual(log.status, AlertEmailLog.Status.SENT)
        self.assertIsNotNone(log.sent_at)

    @mock.patch("alert_system.tasks.send_notification")
    def test_duplicate_email_not_sent(self, mock_send_notification):
        # Test Duplicate alerts for same user/item are skipped
        AlertEmailLogFactory.create(
            user=self.user1,
            subscription=self.subscription,
            item=self.eligible_item,
            message_id="alert-duplicate",
            status=AlertEmailLog.Status.SENT,
            email_type=AlertEmailLog.EmailType.NEW,
            sent_at=timezone.now(),
        )

        send_alert_email_notification(self.eligible_item.id)

        self.assertEqual(AlertEmailLog.objects.count(), 1)
        mock_send_notification.assert_not_called()

    @mock.patch("alert_system.tasks.send_notification")
    def test_daily_email_notification_limit(self, mock_send_notification):

        for _ in range(self.subscription.alert_per_day):
            AlertEmailLogFactory.create(
                user=self.user1,
                subscription=self.subscription,
                item=self.eligible_item,
                message_id=f"alert-old-{_}",
                status=AlertEmailLog.Status.SENT,
                email_type=AlertEmailLog.EmailType.NEW,
                sent_at=timezone.now(),
            )

        send_alert_email_notification(self.eligible_item.id)
        self.assertEqual(
            AlertEmailLog.objects.filter(status=AlertEmailLog.Status.SENT).count(),
            self.subscription.alert_per_day,
        )
        mock_send_notification.assert_not_called()


class AlertEmailReplyTestCase(TestCase):

    def setUp(self):

        self.user = UserFactory.create(email="replyuser@test.com")

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

        self.subscription = AlertSubscriptionFactory.create(
            user=self.user,
            countries=[self.country],
            hazard_types=[self.hazard_type],
        )

        self.item_1 = LoadItemFactory.create(
            connector=self.connector,
            correlation_id="corr-001",
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Flood in Nepal",
            country_codes=["NEP"],
            total_people_exposed=100,
            total_buildings_exposed=50,
            impact_metadata={
                "summary": "Test impact metadata",
                "source": "unit-test",
            },
        )

        # Item for reply
        self.item_2 = LoadItemFactory.create(
            connector=self.connector,
            correlation_id="corr-001",
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Flood Update",
            country_codes=["NEP"],
            total_people_exposed=100,
            total_buildings_exposed=50,
            impact_metadata={
                "summary": "Test impact metadata",
                "source": "unit-test",
            },
        )

        # Thread + root email log
        self.thread = AlertEmailThreadFactory.create(
            user=self.user,
            correlation_id=self.item_1.correlation_id,
            root_email_message_id="root-msg-123",
            root_message_sent_at=timezone.now(),
            reply_until=timezone.now() + timedelta(days=30),
        )

        self.root_email_log = AlertEmailLogFactory.create(
            user=self.user,
            subscription=self.subscription,
            item=self.item_1,
            thread=self.thread,
            message_id="root-msg-123",
            email_type=AlertEmailLog.EmailType.NEW,
            status=AlertEmailLog.Status.SENT,
            sent_at=timezone.now(),
        )

    @mock.patch("alert_system.tasks.send_notification")
    def test_reply_without_root_email(self, mock_send_notification):
        """No reply sent if root email doesn't exist"""
        # Create item with different correlation_id
        new_item = LoadItemFactory.create(
            connector=self.connector,
            correlation_id="corr-999",
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="No root email item",
            country_codes=["NEP"],
            total_people_exposed=100,
            total_buildings_exposed=50,
            impact_metadata={
                "summary": "Test impact metadata",
                "source": "unit-test",
            },
        )

        send_alert_email_replies(new_item.id)

        self.assertFalse(AlertEmailLog.objects.filter(email_type=AlertEmailLog.EmailType.REPLY).exists())
        mock_send_notification.assert_not_called()

    @mock.patch("alert_system.tasks.send_alert_email_replies.delay")
    def test_new_related_item_reply(self, mock_send_alert_email_replies):

        old_item = LoadItemFactory.create(
            connector=self.connector,
            correlation_id="corr-0012323",
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="No root email item",
            country_codes=["NEP"],
            total_people_exposed=100,
            total_buildings_exposed=50,
            impact_metadata={
                "summary": "Test impact metadata",
                "source": "unit-test",
            },
        )

        AlertEmailLogFactory.create(
            user=self.user,
            subscription=self.subscription,
            item=old_item,
            status=AlertEmailLog.Status.SENT,
            email_type=AlertEmailLog.EmailType.NEW,
        )

        new_item = LoadItemFactory.create(
            connector=self.connector,
            correlation_id="corr-0012323",
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="No root email item",
            country_codes=["NEP"],
            total_people_exposed=100,
            total_buildings_exposed=50,
            impact_metadata={
                "summary": "Test impact metadata",
                "source": "unit-test",
            },
        )

        call_command("alert_notification_reply")

        mock_send_alert_email_replies.assert_called_with(load_item_id=new_item.id)

    @mock.patch("alert_system.tasks.send_notification")
    def test_reply_email_within_30_days(self, mock_send_notification):
        """Reply is sent when inside 30-day window"""
        # Mock timezone.now()
        patcher = mock.patch("django.utils.timezone.now")
        mock_timezone_now = patcher.start()
        mock_now = datetime(2026, 1, 15, 12, 0, 0)  # inside 30-day window
        mock_timezone_now.return_value = timezone.make_aware(mock_now)

        send_alert_email_replies(self.item_2.id)

        # Fetch reply specifically for the user and item
        reply_logs = AlertEmailLog.objects.filter(
            email_type=AlertEmailLog.EmailType.REPLY, user=self.user, item=self.item_2, thread=self.thread
        )
        self.assertEqual(reply_logs.count(), 1)
        mock_send_notification.assert_called_once()
        patcher.stop()

    @mock.patch("alert_system.tasks.send_notification")
    def test_reply_email_after_30_days(self, mock_send_notification):
        """Reply is NOT sent when outside 30-day window"""
        # Mock now to a datetime after the 30-day reply window
        patcher = mock.patch("django.utils.timezone.now")
        mock_timezone_now = patcher.start()
        mock_now = datetime(2026, 2, 15, 12, 0, 0)
        mock_timezone_now.return_value = timezone.make_aware(mock_now)

        reply_exists = AlertEmailLog.objects.filter(
            email_type=AlertEmailLog.EmailType.REPLY, user=self.user, item=self.item_2, thread=self.thread
        ).exists()
        self.assertFalse(reply_exists)
        mock_send_notification.assert_not_called()
        patcher.stop()

    @mock.patch("alert_system.tasks.send_notification")
    def test_duplicate_reply(self, mock_send_notification):

        # Already sent reply
        AlertEmailLogFactory.create(
            user=self.user,
            subscription=self.subscription,
            item=self.item_2,
            thread=self.thread,
            message_id="reply-msg-001",
            email_type=AlertEmailLog.EmailType.REPLY,
            status=AlertEmailLog.Status.SENT,
            sent_at=timezone.now(),
        )

        send_alert_email_replies(self.item_2.id)

        replies = AlertEmailLog.objects.filter(email_type=AlertEmailLog.EmailType.REPLY)
        self.assertEqual(replies.count(), 1)
        mock_send_notification.assert_not_called()

    @mock.patch("alert_system.tasks.send_notification")
    def test_reply_to_multiple_users_separate_threads(self, mock_send_notification):
        # Mock timezone
        patcher = mock.patch("django.utils.timezone.now")
        mock_timezone_now = patcher.start()
        mock_now = datetime(2026, 1, 15, 12, 0, 0)  # inside 30-day window
        mock_timezone_now.return_value = timezone.make_aware(mock_now)

        # New item for this test
        new_item = LoadItemFactory.create(
            connector=self.connector,
            correlation_id="corr-multi-users",
            item_eligible=True,
            is_past_event=False,
            start_datetime=timezone.now(),
            event_title="Flood Multi-user",
            country_codes=["NEP"],
            total_people_exposed=100,
            total_buildings_exposed=50,
            impact_metadata={"summary": "Test", "source": "unit-test"},
        )

        # Thread for self.user
        thread_user1 = AlertEmailThreadFactory.create(
            user=self.user,
            correlation_id=new_item.correlation_id,
            root_email_message_id="root-msg-user1",
            root_message_sent_at=timezone.now(),
            reply_until=timezone.now() + timedelta(days=30),
        )
        AlertEmailLogFactory.create(
            user=self.user,
            subscription=self.subscription,
            item=new_item,
            thread=thread_user1,
            message_id="root-msg-user1",
            email_type=AlertEmailLog.EmailType.NEW,
            status=AlertEmailLog.Status.PROCESSING,
        )

        # Second user + thread
        user2 = UserFactory.create(email="second@test.com")
        subscription2 = AlertSubscriptionFactory.create(
            user=user2,
            countries=[self.country],
            hazard_types=[self.hazard_type],
        )
        thread_user2 = AlertEmailThreadFactory.create(
            user=user2,
            correlation_id=new_item.correlation_id,
            root_email_message_id="root-msg-user2",
            root_message_sent_at=timezone.now(),
            reply_until=timezone.now() + timedelta(days=30),
        )
        AlertEmailLogFactory.create(
            user=user2,
            subscription=subscription2,
            item=new_item,
            thread=thread_user2,
            message_id="root-msg-user2",
            email_type=AlertEmailLog.EmailType.NEW,
            status=AlertEmailLog.Status.PROCESSING,
        )

        # Send replies
        send_alert_email_replies(new_item.id)

        replies = AlertEmailLog.objects.filter(email_type=AlertEmailLog.EmailType.REPLY, item=new_item)
        self.assertEqual(replies.count(), 2)
        self.assertEqual(mock_send_notification.call_count, 2)

        reply_user1 = replies.get(user=self.user)
        reply_user2 = replies.get(user=user2)

        self.assertEqual(reply_user1.thread, thread_user1)
        self.assertEqual(reply_user2.thread, thread_user2)
        self.assertEqual(reply_user1.in_reply_to, thread_user1.root_email_message_id)
        self.assertEqual(reply_user2.in_reply_to, thread_user2.root_email_message_id)
        self.assertNotEqual(reply_user1.message_id, reply_user2.message_id)
        patcher.stop()
