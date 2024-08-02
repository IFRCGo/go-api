from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from per.factories import (
    OpsLearningCacheResponseFactory,
    OpsLearningComponentCacheResponseFactory,
    OpsLearningFactory,
    OpsLearningSectorCacheResponseFactory,
)
from per.models import OpsLearningCacheResponse


class Command(BaseCommand):
    help = "Create dummy OpsLearningSummary"

    def generate_sector_response(self, ops_learnings: list, ops_learning_cache_response):
        """
        Generate dummy OpsLearningSectorCacheResponse
        """
        dummy_ops_learning_sector_cache_response = OpsLearningSectorCacheResponseFactory.create_batch(
            5, filter_response=ops_learning_cache_response
        )
        for ops_learning_sector_cache in dummy_ops_learning_sector_cache_response:
            ops_learning_sector_cache.used_ops_learning.add(*ops_learnings)

    def generate_component_response(self, ops_learnings: list, ops_learning_cache_response: list):
        """
        Generate dummy OpsLearningComponentCacheResponse
        """
        dummy_ops_learning_component_cache_response = OpsLearningComponentCacheResponseFactory.create_batch(
            5, filter_response=ops_learning_cache_response
        )
        for ops_learning_component_cache in dummy_ops_learning_component_cache_response:
            ops_learning_component_cache.used_ops_learning.add(*ops_learnings)

    def generate_ops_learning_summary(self):
        selected_ops_learning = OpsLearningFactory.create_batch(50, is_validated=True)

        # Generating dummy OpsLearningCacheResponse
        dummy_ops_learning_cache_responses = OpsLearningCacheResponseFactory.create_batch(
            5, status=OpsLearningCacheResponse.Status.SUCCESS
        )
        for ops_learning_cache in dummy_ops_learning_cache_responses:
            ops_learning_cache.used_ops_learning.add(*selected_ops_learning[:10])
            self.generate_sector_response(selected_ops_learning[11:20], ops_learning_cache)
            self.generate_component_response(selected_ops_learning[21:50], ops_learning_cache)

        self.stdout.write(self.style.SUCCESS("Successfully created dummy OpsLearningSummary"))

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG and settings.GO_ENVIRONMENT not in ["development", "ALPHA-2"]:
            self.stderr.write(
                "Dummy data generation is not allowed for this instance."
                " Use environment variable DEBUG set to True and GO_ENVIRONMENT to development"
            )
            return
        self.generate_ops_learning_summary()
