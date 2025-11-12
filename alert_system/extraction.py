import datetime
import logging

import httpx
from django.utils import timezone

from .models import Connector, EligibleEventMonty

logger = logging.getLogger(__name__)


def fetch_stac_data(url, params):
    current_payload = params.copy()
    current_url = url

    while current_url:
        response = httpx.get(current_url, params=current_payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        features = data.get("features", [])
        yield from features

        # Find the next page link
        next_link = None
        for link in data.get("links", []):
            if link.get("rel") == "next":
                next_link = link.get("href")
                break
        current_url = next_link
        current_payload = None


def process_connector(connector):
    logger.info(f"Running ETL for {connector.type}")
    connector.status = Connector.Status.RUNNING
    connector.save(update_fields=["status"])

    filters = dict(connector.filters or {})
    start_time = (
        connector.last_success_run.isoformat()
        if connector.last_success_run
        else (timezone.now() - datetime.timedelta(days=30)).isoformat()
    )  # TODO: Assign start_time instead of timedelta?
    end_time = timezone.now().isoformat()
    filters["datetime"] = f"{start_time}/{end_time}"
    logger.info(f"Fetching data from {start_time} to {end_time}")
    count = 0
    try:
        result = fetch_stac_data(connector.source_url, filters)
        for feature in result:
            count += 1
            try:
                EligibleEventMonty.objects.update_or_create(
                    event_id=feature.get("id"),
                    connector=connector,
                    defaults={
                        "resp_data": feature,
                        "metadata": {
                            "retrieved_at": timezone.now().isoformat(),
                            "source_url": connector.source_url,
                        },
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to save event {feature.get('id')}: {e}")
        connector.status = Connector.Status.SUCCESS
        connector.last_success_run = timezone.now()
        connector.save(update_fields=["status", "last_success_run"])
        logger.info(f"{count} features processed for {connector.type}")
    except Exception as e:
        connector.status = Connector.Status.FAILURE
        connector.save(update_fields=["status"])
        logger.exception(f"ETL failed for {connector.type}: {e}")
