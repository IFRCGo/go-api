import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q

from alert_system.models import LoadItem
from api.models import Country
from notifications.models import AlertSubscription

logger = logging.getLogger(__name__)


def get_latest_episode_load_item(load_item: LoadItem) -> LoadItem:
    """
    Given a load_item, return the sibling LoadItem with the highest
    episode_number for the same parent_event_id.
    Falls back to the original load_item if no siblings exist.
    """
    latest = LoadItem.objects.filter(parent_event_id=load_item.parent_event_id).order_by("-episode_number").first()
    return latest or load_item


def get_alert_email_context(load_item: LoadItem, user: User):

    country_names = []

    if load_item.country_codes:
        country_names = list(Country.objects.filter(iso3__in=load_item.country_codes).values_list("name", flat=True))

    # Fetch related_montandon_events from the latest episode
    latest_episode_item = get_latest_episode_load_item(load_item)

    email_context = {
        "user_name": user.get_full_name(),
        "event_title": load_item.event_title,
        "event_description": load_item.event_description,
        "country_name": country_names,
        "total_people_exposed": load_item.total_people_exposed,
        "total_buildings_exposed": load_item.total_buildings_exposed,
        "hazard_types": load_item.connector.dtype,
        "related_go_events": load_item.related_go_events.all(),
        "related_montandon_events": latest_episode_item.related_montandon_events.filter(item_eligible=True).order_by(
            "-total_people_exposed"
        ),
        "frontend_url": settings.GO_WEB_URL,
        "start_datetime": load_item.start_datetime,
        "end_datetime": load_item.end_datetime,
    }
    return email_context


def get_alert_subscriptions(load_item: LoadItem):

    region_ids = Country.objects.filter(iso3__in=load_item.country_codes).values_list("region_id", flat=True)

    return (
        AlertSubscription.objects.filter(hazard_types=load_item.connector.dtype)
        .filter(Q(countries__iso3__in=load_item.country_codes) | Q(regions__in=region_ids))
        .select_related("user")
        .distinct()
    )
