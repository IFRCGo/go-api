from celery import shared_task

from per.ops_learning_summary import OpsLearningSummaryTask


@shared_task
def generate_summary(filter_data: dict, hash_value: str):
    regional_list, global_list, country_list = OpsLearningSummaryTask.generate_priotization_list()
    prioritized_learnings = OpsLearningSummaryTask.prioritize_components(filter_data, regional_list, global_list, country_list)
    primary_learning_df, secondary_learning_df = OpsLearningSummaryTask.prioritize_excerpts(prioritized_learnings)
    primary_learning_prompt, secondary_learning_prompt = OpsLearningSummaryTask.format_prompt(
        primary_learning_df, secondary_learning_df, filter_data
    )
    OpsLearningSummaryTask.generate_summaries(primary_learning_prompt, secondary_learning_prompt)
