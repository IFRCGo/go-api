from django.core.management.base import BaseCommand
from dref.models import ActivityTimeFrame, PlannedIntervention

from api.logger import logger

class Command(BaseCommand):
    help = 'Convert Old PlannedIntervention description to early action block'

    def handle(self, *args, **options):
        logger.info("Creating early action blocks from planned interventions description")
        interventions_to_create = []
        for pi in PlannedIntervention.objects.filter(description__isnull=False):
            if pi.description:
                descriptions = pi.description.split('•')
                for desc in descriptions[1:]:
                    activity_frame_title = desc.replace('\n', '').strip()
                    interventions_to_create.append(ActivityTimeFrame(title=activity_frame_title))
            if interventions_to_create:
                ActivityTimeFrame.objects.bulk_create(interventions_to_create)
                pi.early_action_block.add(*interventions_to_create)
                logger.info(f"Created {len(interventions_to_create)} early action blocks for planned intervention")
        if not interventions_to_create:
            logger.info(f"No early action blocks created for planned intervention")