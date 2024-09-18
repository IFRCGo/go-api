import csv
import logging
import os

import markdown
from django.core.management.base import BaseCommand

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
            reader = list(csv.DictReader(csvfile))

            form_comp_without_sub_comp = [comp for comp in reader if not comp["Component number"] == "14"]
            form_comp_with_sub_comp = [item for item in reader if item not in form_comp_without_sub_comp]

            component_dict = {}
            component_numbers = []
            component_letters = []

            for row in form_comp_without_sub_comp:
                if row["Component number"] in component_numbers:
                    if row["Considerations"].strip() == "Urban":
                        component_dict[row["Component number"]]["urban_description"] = row["Description"]
                    if row["Considerations"].strip() == "Climate & environmental":
                        component_dict[row["Component number"]]["climate_description"] = row["Description"]
                    continue

                component_dict[row["Component number"]] = {}
                component_dict[row["Component number"]]["component_name"] = row["Component name"]
                component_dict[row["Component number"]]["component_letter"] = row["Component letter"]
                component_dict[row["Component number"]]["epidemics_description"] = row["Description"]
                component_numbers.append(row["Component number"])

            for row in form_comp_with_sub_comp:
                if row["Component letter"] in component_letters:
                    if row["Considerations"].strip() == "Urban":
                        component_dict[row["Component letter"]]["urban_description"] = row["Description"]
                    if row["Considerations"].strip() == "Climate & environmental":
                        component_dict[row["Component letter"]]["climate_description"] = row["Description"]
                    continue

                component_dict[row["Component letter"]] = {}
                component_dict[row["Component letter"]]["component_name"] = row["Component name"]
                component_dict[row["Component letter"]]["component_letter"] = row["Component letter"]
                component_dict[row["Component letter"]]["epidemics_description"] = row["Description"]
                component_letters.append(row["Component letter"])

            for k, v in component_dict.items():
                form_component = FormComponent.objects.filter(title__icontains=v["component_name"].strip()).first()
                form_component.urban_considerations_guidance = format_description(v["urban_description"])
                form_component.epi_considerations_guidance = format_description(v["epidemics_description"])
                form_component.climate_environmental_considerations_guidance = format_description(v["climate_description"])
                form_component.save(
                    update_fields=[
                        "urban_considerations_guidance_en",
                        "epi_considerations_guidance_en",
                        "climate_environmental_considerations_guidance_en",
                    ]
                )
        logger.info("PER From Component loaded Successfully")
