import csv
import logging
import os

import markdown
from django.core.management.base import BaseCommand

from main.managers import BulkUpdateManager
from per.models import FormComponent

logger = logging.getLogger(__name__)


def format_description(description):
    markdown_text = markdown.markdown(description)
    return markdown_text


class Command(BaseCommand):
    help = "Load form components from a CSV file"

    def handle(self, *args, **kwargs):
        command_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file_path = os.path.join(command_dir, "../../fixtures/form_components.csv")

        with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            bulk_mgr = BulkUpdateManager(
                [
                    "urban_considerations_guidance_en",
                    "epi_considerations_guidance_en",
                    "climate_environmental_considerations_guidance_en",
                ],
                chunk_size=20,
            )

            for row in reader:
                form_component = FormComponent.objects.filter(title__icontains=row["Component name"].strip()).first()
                if form_component is None:
                    logger.warning(f"Form component with name {row['Component name']} is missing ... Skipping.....")
                    continue
                bulk_mgr.add(
                    FormComponent(
                        id=form_component.id,
                        urban_considerations_guidance_en=format_description(row["Urban Description"]),
                        epi_considerations_guidance=format_description(row["Epidemics Description"]),
                        climate_environmental_considerations_guidance=format_description(
                            row["Climate & Environmental Description"]
                        ),
                    )
                )
            bulk_mgr.done()
            self.stdout.write(self.style.SUCCESS(f"Updated: {bulk_mgr.summary()}"))

        logger.info("PER From Component loaded Successfully")
