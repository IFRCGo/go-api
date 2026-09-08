import csv
import logging
import os

import markdown
from django.core.management.base import BaseCommand

from main.managers import BulkUpdateManager
from per.models import FormComponent

logger = logging.getLogger(__name__)

# Maps a CLI-friendly key to (CSV column name, model field name)
FIELD_MAP = {
    "urban": ("Urban Description", "urban_considerations_guidance_en"),
    "epi": ("Epidemics Description", "epi_considerations_guidance_en"),
    "climate": ("Climate & Environmental Description", "climate_environmental_considerations_guidance_en"),
    "migration": ("Migration Description", "migration_considerations_guidance_en"),
}


def format_description(description):
    markdown_text = markdown.markdown(description)
    return markdown_text


class Command(BaseCommand):
    help = "Load form components from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--only",
            nargs="+",
            choices=list(FIELD_MAP.keys()),
            help="Only update the given guidance field(s) (e.g. --only migration), leaving the rest untouched. Defaults to all.",
        )

    def handle(self, *args, **kwargs):
        selected_keys = kwargs.get("only") or list(FIELD_MAP.keys())
        command_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file_path = os.path.join(command_dir, "../../fixtures/form_components.csv")

        with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            bulk_mgr = BulkUpdateManager(
                [FIELD_MAP[key][1] for key in selected_keys],
                chunk_size=20,
            )

            for row in reader:
                form_component = FormComponent.objects.filter(title__icontains=row["Component name"].strip()).first()
                if form_component is None:
                    logger.warning(f"Form component with name {row['Component name']} is missing ... Skipping.....")
                    continue
                update_kwargs = {FIELD_MAP[key][1]: format_description(row[FIELD_MAP[key][0]]) for key in selected_keys}
                bulk_mgr.add(FormComponent(id=form_component.id, **update_kwargs))
            bulk_mgr.done()
            self.stdout.write(self.style.SUCCESS(f"Updated: {bulk_mgr.summary()}"))

        logger.info("PER From Component loaded Successfully")
