import logging
import uuid
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone

from alert_system.models import AlertEmailLog, AlertEmailThread, LoadItem
from api.models import Country
from notifications.models import AlertSubscription
from notifications.notification import send_notification

logger = logging.getLogger(__name__)


def get_alert_email_context(load_item: LoadItem, user: User):

    country_names = []

    if load_item.country_codes:
        country_names = list(Country.objects.filter(iso3__in=load_item.country_codes).values_list("name", flat=True))
    email_context = {
        "user_name": user.get_full_name(),
        "event_title": load_item.event_title,
        "event_description": load_item.event_description,
        "country_name": country_names,
        "total_people_exposed": load_item.total_people_exposed,
        "total_buildings_exposed": load_item.total_buildings_exposed,
        "hazard_types": load_item.connector.dtype,
        "related_go_events": load_item.related_go_events.all(),
        "related_montandon_events": load_item.related_montandon_events.filter(item_eligible=True).order_by(
            "-total_people_exposed"
        ),
        "frontend_url": settings.GO_WEB_URL,
        "start_datetime": load_item.start_datetime,
        "end_datetime": load_item.end_datetime,
    }
    return email_context


def get_alert_subscriptions(load_item: LoadItem):

    regions = Country.objects.filter(iso3__in=load_item.country_codes).values_list("region_id", flat=True)

    return (
        AlertSubscription.objects.filter(hazard_types=load_item.connector.dtype)
        .filter(Q(countries__iso3__in=load_item.country_codes) | Q(regions__in=regions))
        .select_related("user")
        .distinct()
    )


def send_alert_email_notification(
    load_item: LoadItem,
    user: User,
    subscription: AlertSubscription,
    thread: Optional[AlertEmailThread],
    is_reply: bool = False,
) -> None:
    """Helper function to send email and create log entry"""
    message_id: str = str(uuid.uuid4())

    email_log = AlertEmailLog.objects.create(
        user=user,
        subscription=subscription,
        item=load_item,
        status=AlertEmailLog.Status.PROCESSING,
        message_id=message_id,
        thread=thread,
    )

    try:
        if is_reply:
            subject = f"Re: Hazard Alert: {load_item.event_title}"
            template = "email/alert_system/alert_notification_reply.html"
            email_type = "Alert Email Notification Reply"
            in_reply_to = thread.root_email_message_id
        else:
            subject = f"New Hazard Alert: {load_item.event_title}"
            template = "email/alert_system/alert_notification.html"
            email_type = "Alert Email Notification"
            in_reply_to = None

        email_context = get_alert_email_context(load_item, user)
        email_body = render_to_string(template, email_context)

        send_notification(
            subject=subject,
            recipients=user.email,
            message_id=message_id,
            in_reply_to=in_reply_to,
            html=email_body,
            mailtype=email_type,
        )

        email_log.status = AlertEmailLog.Status.SENT
        email_log.email_sent_at = timezone.now()
        email_log.save(update_fields=["status", "email_sent_at"])

        # Create thread for initial emails
        if not is_reply:
            thread = AlertEmailThread.objects.create(
                user=user,
                correlation_id=load_item.correlation_id,
                root_email_message_id=message_id,
                root_message_sent_at=timezone.now(),
            )
            email_log.thread = thread
            email_log.save(update_fields=["thread"])
            logger.info(
                f"Alert Email thread created for user [{user.get_full_name()}] "
                f"with correlation_id [{load_item.correlation_id}]"
            )

        logger.info(f"Alert email sent to [{user.get_full_name()}] for LoadItem ID [{load_item.id}]")

    except Exception:
        email_log.status = AlertEmailLog.Status.FAILED
        email_log.save(update_fields=["status"])
        logger.warning(f"Alert email failed for [{user.get_full_name()}] LoadItem ID [{load_item.id}]", exc_info=True)
