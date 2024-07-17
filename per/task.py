import typing

import pandas as pd
from celery import shared_task
from django.db.models import F

from api.logger import logger
from api.models import Country
from per.models import FormPrioritization, OpsLearning, Overview


class OpsLearningSummaryTask:

    MIN_DIF_COMPONENTS = 3
    MIN_DIF_EXCERPTS = 3

    @classmethod
    def fetch_ops_learnings(self, filter_data):
        """Fetches the OPS learnings from the database."""
        ops_learning_qs = OpsLearning.objects.all()
        from per.drf_views import OpsLearningFilter

        ops_learning_filtered_qs = OpsLearningFilter(filter_data, queryset=ops_learning_qs).qs
        ops_learning_df = pd.DataFrame(
            list(
                ops_learning_filtered_qs.values(
                    "id", "per_component", "learning", "appeal_code__country_id", "appeal_code__country__region_id"
                )
            )
        )
        ops_learning_df = ops_learning_df.rename(
            columns={
                "per_component": "component",
                "appeal_code__country_id": "country_id",
                "appeal_code__country__region_id": "region_id",
            }
        )
        ops_learning_df.set_index("id", inplace=True)
        return ops_learning_df

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
        merged_df = country_df.merge(prioritization_df, on=["country", "region"], how="left")
        no_prioritization_df = merged_df[merged_df["components"].isna()].astype(object)

        for index, row in no_prioritization_df.iterrows():
            region_id = row["region"]
            components = regional_dict.get(region_id, global_components["global"])
            no_prioritization_df.at[index, "components"] = components

        final_df = pd.concat([merged_df.dropna(subset=["components"]), no_prioritization_df])
        final_df["components"] = final_df["components"].apply(lambda x: int(x) if isinstance(x, float) else x)
        final_df = final_df[["country", "components"]]
        return final_df

    @classmethod
    def generate_priotization_list(self):
        logger.info("Generating prioritization list.")
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
            Country.objects.filter(is_deprecated=False, society_name__isnull=False, region__isnull=False)
            .exclude(name__in=exclusion_list)
            .values("id", "region_id")
        )
        country_df = pd.DataFrame(list(country_qs))
        country_df = country_df.rename(columns={"id": "country", "region_id": "region"})

        # Get all PER Overview
        per_overview_qs = Overview.objects.select_related("country").values(
            "id",
            "country_id",
            "country__region",
            "assessment_number",
        )
        per_overview_df = pd.DataFrame(list(per_overview_qs))
        per_overview_df = per_overview_df.rename(columns={"id": "overview", "country_id": "country", "country__region": "region"})

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
                "overview",
                "components",
            )
        )
        per_priotization_df = pd.DataFrame(list(per_priotization_qs))
        per_priotization_df = per_priotization_df.merge(
            per_overview_df[["overview", "country", "region", "assessment_number"]], on="overview", how="left"
        )
        per_priotization_df = per_priotization_df.sort_values("assessment_number").drop_duplicates(subset="country", keep="last")
        per_priotization_df = per_priotization_df[["region", "country", "components"]]

        # Generate the prioritization list that are in dataframes
        regional_list = self.generate_regional_prioritization_list(per_priotization_df)
        global_list = self.generate_global_prioritization_list(regional_list)
        country_list = self.generate_country_prioritization_list(regional_list, global_list, per_priotization_df, country_df)
        logger.info("Prioritization list generated.")
        return regional_list, global_list, country_list

    @classmethod
    def prioritize(
        self,
        df: pd.DataFrame,
        components_countries: dict,
        components_regions: dict,
        components_global: dict,
        type_prioritization: typing.Union[list, None],
    ):
        """Prioritizes components based on the type of prioritization."""

        def add_new_component(prioritized_components, per_prioritized_components, df):
            """Adds new components to the prioritized list based on availability and frequency."""
            available_components = list(df["component"].unique())
            remaining_components = [item for item in available_components if item not in prioritized_components]

            intersect_components = list(set(per_prioritized_components) & set(remaining_components))

            if intersect_components:
                mask = df["component"].isin(intersect_components)
            else:
                mask = df["component"].isin(remaining_components)

            component_counts = df[mask]["component"].value_counts()
            most_frequent_components = component_counts[component_counts == component_counts.max()].index.tolist()

            return prioritized_components + most_frequent_components

        if type_prioritization == "single-country":
            country_id = str(df["country_id"].iloc[0])
            per_prioritized_components = components_countries.get(country_id, [])
        elif type_prioritization == "single-region":
            region_id = str(df["region_id"].iloc[0])
            per_prioritized_components = components_regions.get(region_id, [])
        per_prioritized_components = components_global.get("global", [])

        component_counts = df["component"].value_counts()
        most_frequent_components = component_counts[component_counts == component_counts.max()].index.tolist()

        while len(most_frequent_components) < 3:
            most_frequent_components = add_new_component(most_frequent_components, per_prioritized_components, df)

        mask = df["component"].isin(most_frequent_components)
        return df[mask]

    @classmethod
    def prioritize_components(
        self,
        filter_data: dict,
        regional_list,
        global_list,
        country_list,
    ):
        logger.info("Prioritizing components.")

        def need_component_prioritization(df, MIN_DIF_COMPONENTS, MIN_DIF_EXCERPTS):
            """Determines if prioritization is needed based on unique components and learnings."""
            nb_dif_components = len(df["component"].unique())
            nb_dif_learnings = len(df["learning"].unique())
            return nb_dif_components > MIN_DIF_COMPONENTS and nb_dif_learnings > MIN_DIF_EXCERPTS

        def identify_type_prioritization(df):
            """Identifies the type of prioritization required based on the data."""
            if len(df["country_id"].unique()) == 1:
                return "single-country"
            elif len(df["region_id"].unique()) == 1:
                return "single-region"
            elif len(df["region_id"].unique()) > 1:
                return "multi-region"
            return None

        components_countries = country_list.to_dict(orient="records")
        components_countries = {item["country"]: item["components"] for item in components_countries}

        components_regions = regional_list.to_dict(orient="records")
        components_regions = {item["region"]: item["components"] for item in components_regions}

        ops_learning_df = self.fetch_ops_learnings(filter_data)

        if need_component_prioritization(ops_learning_df, self.MIN_DIF_COMPONENTS, self.MIN_DIF_EXCERPTS):
            type_prioritization = identify_type_prioritization(ops_learning_df)
            prioritized_learnings = self.prioritize(
                ops_learning_df, components_countries, components_regions, global_list, type_prioritization
            )
        prioritized_learnings = ops_learning_df
        logger.info("Prioritization of components completed.")
        return prioritized_learnings


@shared_task
def generate_summary(filter_data: dict, hash_value: str):
    regional_list, global_list, country_list = OpsLearningSummaryTask.generate_priotization_list()
    OpsLearningSummaryTask.prioritize_components(filter_data, regional_list, global_list, country_list)
