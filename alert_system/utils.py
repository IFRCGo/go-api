from django.conf import settings
from django.db.models import Q

from alert_system.models import AlertSubscription, LoadItem
from api.models import Country


def get_alert_email_context(load_item: LoadItem, user):

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


def get_alert_subscriptions_for_load_item(load_item: LoadItem):

    regions = Country.objects.filter(iso3__in=load_item.country_codes).values_list("region_id", flat=True)

    return (
        AlertSubscription.objects.filter(hazard_types=load_item.connector.dtype)
        .filter(Q(countries__iso3__in=load_item.country_codes) | Q(regions__in=regions))
        .select_related("user")
        .distinct()
    )
