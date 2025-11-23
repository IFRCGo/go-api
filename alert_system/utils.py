import logging

from .models import EligibleItems

logger = logging.getLogger(__name__)


def copy_to_eligible(item):
    """
    Copy a StacItems instance to EligibleItems.

    Args:
        item: StacItems instance to copy
    """
    try:
        # Check if already exists to avoid duplicates
        if EligibleItems.objects.filter(stac_id=item.stac_id).exists():
            logger.warning(f"EligibleItem with stac_id {item.stac_id} already exists")
            return None

        eligible_item = EligibleItems.objects.create(
            stac_id=item.stac_id,
            collection=item.collection,
            connector=item.connector,
            resp_data=item.resp_data,
            metadata=item.metadata,
            correlation_id=item.correlation_id,
            cluster=item.cluster,
            estimate_type=item.estimate_type,
            severity_unit=item.severity_unit,
            severity_label=item.severity_label,
            severity_value=item.severity_value,
            category=item.category,
            type=item.type,
            value=item.value,
        )

        logger.info(f"Created EligibleItem: {eligible_item.stac_id}")
        return eligible_item

    except Exception as e:
        logger.error(f"Error copying item {item.stac_id} to EligibleItems: {str(e)}")
        raise
