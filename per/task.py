from ast import literal_eval

import pandas as pd
from celery import shared_task
from django.db.models import Exists, F, OuterRef

from api.models import Country
from country_plan.models import CountryPlan
from per.models import FormPrioritization, Overview


class OpsLearningSummaryTask:

    @classmethod
    def generate_regional_prioritization_list(self, df: pd.DataFrame):
        """Generates a list of regional prioritizations from the given data."""
        df_exploded = df.explode("components")
        regional_df = df_exploded.groupby(["region", "components"]).size().reset_index(name="count")
        regional_df = regional_df[regional_df["count"] > 2]
        regional_list = regional_df.groupby("region")["components"].apply(list).reset_index()
        return regional_list

    @classmethod
    def generate_global_prioritization_list(self, regional_df: pd.DataFrame):
        """Generates a global prioritization list from regional data."""
        global_df = regional_df.explode("components").groupby("components").size().reset_index(name="count")
        global_components = global_df[global_df["count"] > 2]["components"].tolist()
        global_list = {"global": global_components}
        return global_list

    @classmethod
    def generate_country_prioritization_list(
        self, regional_df: pd.DataFrame, global_components: list, prioritization_df: pd.DataFrame, country_df: pd.DataFrame
    ):
        """Generates a country-level prioritization list."""
        regional_dict = dict(zip(regional_df["region"], regional_df["components"]))
        merged_df = country_df[["country", "region"]].merge(prioritization_df, on=["country", "region"], how="left")
        no_prioritization_df = merged_df[merged_df["components"].isna()]

        for index, row in no_prioritization_df.iterrows():
            region_id = row["region"]
            components = regional_dict.get(region_id, global_components["global"])
            no_prioritization_df.at[index, "components"] = components

        final_df = pd.concat([merged_df.dropna(subset=["components"]), no_prioritization_df])
        final_df["components"] = final_df["components"].apply(lambda x: literal_eval(str(x)))
        final_df = final_df[["country", "components"]]
        return final_df

    @classmethod
    def generate_priotization_list(self):
        exclusion_list = [
            "IFRC Africa",
            "IFRC Americas",
            "IFRC Asia-Pacific",
            "IFRC Europe",
            "IFRC Geneva",
            "IFRC MENA",
            "Benelux ERU",
            "ICRC",
        ]

        # Get all countries
        country_qs = (
            Country.objects.filter(is_deprecated=False, society_name__isnull=False)
            .exclude(name__in=exclusion_list)
            .annotate(has_country_plan=Exists(CountryPlan.objects.filter(country=OuterRef("pk"), is_publish=True)))
            .values("id")
        )
        country_df = pd.DataFrame(list(country_qs))
        country_df = country_df.rename(columns={"id": "country"}, inplace=True)

        # Get all PER Overview
        per_overview_qs = Overview.objects.select_related("country").values(
            "id",
            "country_id",
            "country__region",
            "assessment_number",
        )
        per_overview_df = pd.DataFrame(list(per_overview_qs))
        per_overview_df = per_overview_df.rename(
            columns={"id": "overview", "country_id": "country", "country__region": "region"}, inplace=True
        )

        # Get all PER Prioritization
        per_priotization_qs = (
            FormPrioritization.objects.filter(
                is_draft=False,
                prioritized_action_responses__isnull=False,
            )
            .annotate(
                components=F("prioritized_action_responses__component"),
            )
            .values(
                "overview__country__id",
                "components",
            )
        )
        per_priotization_df = pd.DataFrame(list(per_priotization_qs))
        per_priotization_df = per_priotization_df.merge(
            per_overview_df[["overview", "country", "region", "assessment_number"]], on="overview", how="left"
        )
        per_priotization_df = per_priotization_df.sort_values("assessment_number").drop_duplicates(subset="country", keep="last")
        per_priotization_df = per_priotization_df[["region", "country", "components"]]

        # Generate the prioritization list
        regional_list = self.generate_regional_prioritization_list(per_priotization_df)
        global_list = self.generate_global_prioritization_list(regional_list)
        country_list = self.generate_country_prioritization_list(regional_list, global_list, per_priotization_df, country_df)

        return regional_list, global_list, country_list


@shared_task
def generate_summary(filter_data, hash_value):
    regional_list, global_list, country_list = OpsLearningSummaryTask.generate_priotization_list()
