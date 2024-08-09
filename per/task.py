from celery import shared_task

from api.logger import logger
from per.models import OpsLearningCacheResponse
from per.ops_learning_summary import OpsLearningSummaryTask


def validate_primary_summary_generation(filter_data: dict) -> bool:
    """
    Validates if primary summary generation is required or not
    """
    keys = {"appeal_code__country", "appeal_code__region"}
    if any(key in filter_data for key in keys):
        for key in keys:
            filter_data.pop(key, None)
        return bool(filter_data)
    return False


@shared_task
def generate_summary(ops_learning_summary_id: int, filter_data: dict):
    ops_learning_summary_instance = OpsLearningCacheResponse.objects.filter(id=ops_learning_summary_id).first()
    if not ops_learning_summary_instance:
        logger.error("Ops learning summary not found", exc_info=True)
        return False

    # Change Ops Learning Summary Status to STARTED
    OpsLearningSummaryTask.change_ops_learning_status(
        instance=ops_learning_summary_instance, status=OpsLearningCacheResponse.Status.STARTED
    )

    # Fetch ops-learning/extracts data
    ops_learning_df = OpsLearningSummaryTask.fetch_ops_learnings(filter_data=filter_data)

    # Check if ops-learning data is available
    if not ops_learning_df.empty:
        try:
            # Generate prioritization list
            regional_list, global_list, country_list = OpsLearningSummaryTask.generate_priotization_list()

            # Prioritize components
            prioritized_learnings = OpsLearningSummaryTask.prioritize_components(
                ops_learning_df=ops_learning_df, regional_list=regional_list, global_list=global_list, country_list=country_list
            )

            # NOTE: Primary summary generation is only required if region, country and any other filter is provided
            if validate_primary_summary_generation(filter_data):
                # Prioritize excerpts for primary insights
                primary_learning_df = OpsLearningSummaryTask.primary_prioritize_excerpts(prioritized_learnings)
                # Format primary prompt
                primary_learning_prompt = OpsLearningSummaryTask.format_primary_prompt(
                    ops_learning_summary_instance=ops_learning_summary_instance,
                    primary_learning_df=primary_learning_df,
                    filter_data=filter_data,
                )
                # Generate primary summary
                OpsLearningSummaryTask.get_or_create_primary_summary(
                    ops_learning_summary_instance=ops_learning_summary_instance, primary_learning_prompt=primary_learning_prompt
                )

            # Prioritize excerpts for secondary insights
            secondary_learning_df = OpsLearningSummaryTask.seconday_prioritize_excerpts(prioritized_learnings)
            # Format secondary prompt
            secondary_learning_prompt = OpsLearningSummaryTask.format_secondary_prompt(secondary_learning_df, filter_data)
            # Generate secondary summary
            OpsLearningSummaryTask.get_or_create_secondary_summary(
                ops_learning_summary_instance=ops_learning_summary_instance, secondary_learning_prompt=secondary_learning_prompt
            )

            # Change Ops Learning Summary Status to SUCCESS
            OpsLearningSummaryTask.change_ops_learning_status(
                instance=ops_learning_summary_instance, status=OpsLearningCacheResponse.Status.SUCCESS
            )
            return True
        except Exception:
            OpsLearningSummaryTask.change_ops_learning_status(
                instance=ops_learning_summary_instance, status=OpsLearningCacheResponse.Status.FAILED
            )
            logger.error("Ops learning summary process failed", exc_info=True)
            return False
    else:
        OpsLearningSummaryTask.change_ops_learning_status(
            instance=ops_learning_summary_instance, status=OpsLearningCacheResponse.Status.NO_EXTRACT_AVAILABLE
        )
        logger.error("No extracts found", exc_info=True)
        return False
