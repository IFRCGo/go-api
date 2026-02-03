import logging
import uuid
from typing import Optional

from django.contrib.auth.models import User
from django.db.models import Count
from django.template.loader import render_to_string
from django.utils import timezone

from alert_system.models import AlertEmailLog, AlertEmailThread, LoadItem
from alert_system.utils import get_alert_email_context, get_alert_subscriptions
from notifications.models import AlertSubscription
from notifications.notification import send_notification

logger = logging.getLogger(__name__)


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
                parent_guid=load_item.parent_guid,
                root_email_message_id=message_id,
                root_message_sent_at=timezone.now(),
            )
            email_log.thread = thread
            email_log.save(update_fields=["thread"])
            logger.info(
                f"Alert Email thread created for user [{user.get_full_name()}] " f"with parent_guid [{load_item.parent_guid}]"
            )

        logger.info(f"Alert email sent to [{user.get_full_name()}] for LoadItem ID [{load_item.id}]")

    except Exception:
        email_log.status = AlertEmailLog.Status.FAILED
        email_log.save(update_fields=["status"])
        logger.warning(f"Alert email failed for [{user.get_full_name()}] LoadItem ID [{load_item.id}]", exc_info=True)


def process_email_alert(load_item_id: int) -> None:
    load_item = LoadItem.objects.select_related("connector", "connector__dtype").filter(id=load_item_id).first()

    if not load_item:
        logger.warning(f"LoadItem with ID [{load_item_id}] not found")
        return

    subscriptions = list(get_alert_subscriptions(load_item))
    if not subscriptions:
        logger.info(f"No alert subscriptions matched for LoadItem ID [{load_item_id}]")
        return

    today = timezone.now().date()
    user_ids = [sub.user_id for sub in subscriptions]
    subscription_ids = [sub.id for sub in subscriptions]

    # Daily email counts per user
    daily_counts = (
        AlertEmailLog.objects.filter(
            user_id__in=user_ids,
            subscription_id__in=subscription_ids,
            status=AlertEmailLog.Status.SENT,
            email_sent_at__date=today,
        )
        .values("user_id", "subscription_id")
        .annotate(sent_count=Count("id"))
    )
    daily_count_map = {(item["user_id"], item["subscription_id"]): item["sent_count"] for item in daily_counts}

    # Emails already sent for this item (per user)
    already_sent = set(
        AlertEmailLog.objects.filter(
            user_id__in=user_ids,
            subscription_id__in=subscription_ids,
            item_id=load_item_id,
            status=AlertEmailLog.Status.SENT,
        ).values_list("user_id", "subscription_id")
    )

    # Existing threads for this correlation_id
    existing_threads = {
        thread.user_id: thread
        for thread in AlertEmailThread.objects.filter(
            parent_guid=load_item.parent_guid,
            user_id__in=user_ids,
        )
    }

    for subscription in subscriptions:
        user = subscription.user
        user_id: int = user.id
        subscription_id: int = subscription.id

        # Reply if this specific user has an existing thread
        thread = existing_threads.get(user_id)
        is_reply: bool = thread is not None

        # Skip if daily alert limit reached
        sent_today: int = daily_count_map.get((user_id, subscription_id), 0)
        if subscription.alert_per_day and sent_today >= subscription.alert_per_day:
            logger.info(f"Daily alert limit reached for user [{user.get_full_name()}]")
            continue

        # Skip duplicate emails for same item
        if (user_id, subscription_id) in already_sent:
            logger.info(f"Duplicate alert skipped for user [{user.get_full_name()}] " f"with LoadItem ID [{subscription_id}]")
            continue

        send_alert_email_notification(load_item=load_item, user=user, subscription=subscription, thread=thread, is_reply=is_reply)
