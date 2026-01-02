from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from alert_system.factories import (
    ConnectorFactory,
    EmailAlertLogFactory,
    LoadItemFactory,
)
from alert_system.models import Connector, EmailAlertLog
from alert_system.tasks import send_alert_email_notification
from api.factories.country import CountryFactory
from api.factories.disaster_type import DisasterTypeFactory
from api.factories.region import RegionFactory
from deployments.factories.user import UserFactory
from notifications.factories import AlertSubscriptionFactory
from notifications.models import AlertSubscription


class AlertNotificationsTest(TestCase):
    """Test alert email notification workflow"""

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

    @patch("alert_system.tasks.send_alert_email_notification.delay")
    @patch("alert_system.tasks.send_notification")
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
        self.assertEqual(EmailAlertLog.objects.count(), 1)

    @patch("alert_system.tasks.send_notification")
    def test_alert_email_sent_for_eligible_item(self, mock_send_notification):

        mock_send_notification.return_value = None
        send_alert_email_notification(self.eligible_item.id)
        mock_send_notification.assert_called_once()

        self.assertEqual(EmailAlertLog.objects.count(), 1)
        log = EmailAlertLog.objects.first()

        self.assertEqual(log.user, self.user1)
        self.assertEqual(log.item, self.eligible_item)
        self.assertEqual(log.subscription, self.subscription)
        self.assertEqual(log.status, EmailAlertLog.Status.SENT)
        self.assertIsNotNone(log.sent_at)

    @patch("alert_system.tasks.send_notification")
    def test_duplicate_email_not_sent(self, mock_send_notification):
        # Test Duplicate alerts for same user/item are skipped
        EmailAlertLogFactory.create(
            user=self.user1,
            subscription=self.subscription,
            item=self.eligible_item,
            message_id="alert-duplicate",
            status=EmailAlertLog.Status.SENT,
            sent_at=timezone.now(),
        )

        send_alert_email_notification(self.eligible_item.id)

        self.assertEqual(EmailAlertLog.objects.count(), 1)
        mock_send_notification.assert_not_called()

    @patch("alert_system.tasks.send_notification")
    def test_daily_email_notification_limit(self, mock_send_notification):

        for _ in range(self.subscription.alert_per_day):
            EmailAlertLogFactory.create(
                user=self.user1,
                subscription=self.subscription,
                item=self.eligible_item,
                message_id=f"alert-old-{_}",
                status=EmailAlertLog.Status.SENT,
                sent_at=timezone.now(),
            )

        send_alert_email_notification(self.eligible_item.id)

        self.assertEqual(
            EmailAlertLog.objects.filter(status=EmailAlertLog.Status.SENT).count(),
            self.subscription.alert_per_day,
        )
        mock_send_notification.assert_not_called()
