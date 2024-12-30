import ast
import re
import typing
from itertools import chain, zip_longest

import pandas as pd
import tiktoken
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils.functional import cached_property
from openai import AzureOpenAI

from api.logger import logger
from api.models import Country
from api.utils import get_model_name
from deployments.models import SectorTag
from lang.tasks import translate_model_fields
from per.cache import OpslearningSummaryCacheHelper
from per.models import (
    FormComponent,
    FormPrioritization,
    OpsLearning,
    OpsLearningCacheResponse,
    OpsLearningComponentCacheResponse,
    OpsLearningPromptResponseCache,
    OpsLearningSectorCacheResponse,
    Overview,
)


class AzureOpenAiChat:

    @cached_property
    def client(self):
        return AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT, api_key=settings.AZURE_OPENAI_KEY, api_version="2023-05-15"
        )

    def get_response(self, message):
        try:
            response = self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME, messages=message, temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error while generating response: {e}", exc_info=True)


class OpsLearningSummaryTask:

    PROMPT_DATA_LENGTH_LIMIT = 5000
    PROMPT_LENGTH_LIMIT = 7500
    ENCODING_NAME = "cl100k_base"

    MIN_DIF_COMPONENTS = 3
    MIN_DIF_EXCERPTS = 3

    primary_prompt = (
        "Please aggregate and summarize the provided data into UP TO THREE structured paragraphs.\n"
        "The output MUST strictly adhere to the format below:\n"
        "- *Title*: Each finding should begin with the main finding TITLE in bold.\n"
        "Should be a high level summary of the finding below. "
        "The length of the title MUST be between 20 and 30 characters.\n"
        "- *Excerpts ID*: Identify the ids of the excerpts you took into account for creating the summary.\n"
        "- Content: Aggregate findings so that they are supported by evidence from more than one report. "
        "Always integrate evidence from multiple reports or items into the paragraph, and "
        "include the year and country of the evidence.\n"
        "- *Confidence Level*: Based on the number of excerpts connected to the finding, "
        "assign a score from 1 to 5 where 1 is the lowest and 5 is the highest, e.g. 4/5"
        "At the end of the summary, please highlight any contradictory country reports.\n"
        "Important:\n\n"
        "-- DO NOT mention the excerpts id in the content of the summary.\n"
        "-- DO NOT mention the confidence level in the content of the summary.\n"
        "-- DO NOT use data from any source other than the one provided.\n\n"
        "Output Format:\n"
        "Provide your answer in valid JSON form. Reply with only the answer in valid JSON form and include no other commentary.\n"
        "Example:\n"
        '{"0": {"title": "Flexible and Adaptive Response Planning", "excerpts id":"123, 45" '
        '"content": "Responses in Honduras, Peru, Ecuador, and Panama highlight the importance of adaptable strategies. '
        "The shift from youth-focused MHPSS to inclusive care in Peru in 2021, the pivot from sanitation infrastructure "
        "to direct aid in Ecuador in 2022, and the responsive livelihood support in Panama in 2020, "
        "all underscore the need for continuous reassessment and agile adaptation to the complex, "
        'changing needs of disaster-affected communities.", "confidence level": "4/5"}, '
        '"1": {"title": "...", "excerpts id":"...", "content": "...", "confidence level": "..."}, '
        '"2": {"title": "...", "excerpts id":"...", "content": "...", "confidence level": "..."}, '
        '"contradictory reports": "..."}'
    )

    secondary_prompt = (
        "Please aggregate and summarize this data into structured paragraphs (as few as possible, as many as necessary). \n "
        "The output SHOULD ALWAYS follow the format below:\n"
        "- *Type*: Whether the paragraph is related to a 'sector' or a 'component'\n"
        "- *Subtype*: Provides the name of the sector or of the component to which the paragraph refers.\n"
        "- *Excerpts ID*: Identify the ids of the excerpts you took into account for creating the summary.\n"
        "*Content*: A short summary aggregating findings related to the Subtype, "
        "so that they are supported by evidence coming from more than one report, "
        "and there is ONLY ONE entry per subtype. Always integrate in the paragraph evidence that supports "
        "it from the data available from multiples reports or items, include year and country of the evidence. "
        "The length of each paragraph MUST be between 20 and 30 words.\n"
        " Important:\n\n"
        "- ONLY create one summary per subtype\n"
        "- DO NOT mention the ids of the excerpts in the content of the summary.\n"
        "- DO NOT use data from any source other than the one provided.\n\n"
        "Output Format:\n"
        "Provide your answer in valid JSON form. Reply with ONLY the answer in JSON form and include NO OTHER COMMENTARY.\n"
        '{"0": {"type": "sector", "subtype": "shelter", "excerpts id":"43, 1375, 14543", "content": "lorem ipsum"}, '
        '"1": {"type": "component", "subtype": "Information Management", "excerpts id":"23, 235", "content": "lorem ipsum"}, '
        '"2": {"type": "sector", "subtype": "WASH", "excerpts id":"30, 40",  "content": "lorem ipsum"}}'
    )

    system_message = (
        "# CONTEXT # I want to summarize a set of lessons learned from a set of past emergency response operations "
        "to extract the most useful and actionable insights."
        "# STYLE # Use a writing style that is professional but informal."
        "# TONE # Encouraging and motivating."
        "# AUDIENCE # The audience is emergency response personnel from the Red Cross and Red Crescent. "
        "They are action-oriented people who have very little time so they need concise, "
        "not obvious information that can be easily consumed and acted upon in the time of a response."
    )

    primary_instruction_prompt = (
        "You should:\n"
        "1. Describe, Summarize and Compare: Identify and detail the who, what, where and when "
        "2. Explain and Connect: Analyze why events happened and how they are related "
        "3. Identify gaps: Assess what data is available, what is missing and potential biases "
        "4. Identify key messages: Determine important stories and signals hidden in the data "
        "5. Select top three: Select up to three findings to report "
    )

    secondary_instruction_prompt = (
        "You should for each section in the data (TYPE & SUBTYPE combination):\n"
        "1. Describe, Summarize and Compare: Identify and detail the who, what, where and when "
        "2. Explain and Connect: Analyze why events happened and how they are related "
        "3. Identify gaps: Assess what data is available, what is missing and potential biases "
        "4. Identify key messages: Determine if there are important stories and signals hidden in the data "
        "5. Conclude and make your case "
    )

    @staticmethod
    def count_tokens(string, encoding_name):
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(string))

    @staticmethod
    def change_ops_learning_status(instance: OpsLearningCacheResponse, status: OpsLearningCacheResponse.Status):
        """Changes the status of the OPS learning instance."""
        instance.status = status
        instance.save(update_fields=["status"])

    @staticmethod
    def add_used_ops_learnings(instance: OpsLearningCacheResponse, used_ops_learnings: typing.List[int]):
        """Adds the used OPS learnings to the cache response."""
        instance.used_ops_learning.add(*used_ops_learnings)

    @staticmethod
    def add_used_ops_learnings_sector(
        instance: OpsLearningCacheResponse, content: str, used_ops_learnings: typing.List[int], sector: str
    ):
        """Adds the used OPS learnings to the cache response."""
        sector_instance = (
            SectorTag.objects.exclude(is_deprecated=True)
            .filter(
                title__iexact=sector,
            )
            .first()
        )
        if not sector_instance:
            logger.info(f"Sector '{sector}' not found.")
            return
        ops_learning_instances = OpsLearning.objects.filter(is_validated=True, id__in=used_ops_learnings)
        if len(ops_learning_instances):
            ops_learning_sector, created = (
                OpsLearningSectorCacheResponse.objects.select_related("filter_response", "sector")
                .prefetch_related(
                    "used_ops_learning",
                )
                .get_or_create(
                    sector=sector_instance,
                    filter_response=instance,
                    defaults={"content": content},
                )
            )
            if created:
                ops_learning_sector.used_ops_learning.add(*ops_learning_instances)
                transaction.on_commit(
                    lambda: translate_model_fields.delay(
                        get_model_name(type(ops_learning_sector)),
                        ops_learning_sector.pk,
                    )
                )

    @staticmethod
    def add_used_ops_learnings_component(
        instance: OpsLearningCacheResponse,
        content: str,
        used_ops_learnings: typing.List[int],
        component: str,
    ):
        """Adds the used OPS learnings to the cache response."""
        component_instance = FormComponent.objects.filter(
            title__iexact=component,
        ).first()
        if not component_instance:
            logger.info(f"Component '{component}' not found.")
            return
        ops_learning_instances = OpsLearning.objects.filter(is_validated=True, id__in=used_ops_learnings)
        if len(ops_learning_instances):
            ops_learning_component, created = (
                OpsLearningComponentCacheResponse.objects.select_related("filter_response", "component")
                .prefetch_related(
                    "used_ops_learning",
                )
                .get_or_create(
                    component=component_instance,
                    filter_response=instance,
                    defaults={"content": content},
                )
            )
            if created:
                ops_learning_component.used_ops_learning.add(*ops_learning_instances)
                transaction.on_commit(
                    lambda: translate_model_fields.delay(
                        get_model_name(type(ops_learning_component)),
                        ops_learning_component.pk,
                    )
                )

    @classmethod
    def fetch_ops_learnings(cls, filter_data):
        """Fetches the OPS learnings from the database."""
        ops_learning_qs = (
            OpsLearning.objects.filter(is_validated=True)
            .select_related(
                "per_component_validated", "sector_validated", "appeal_code__country", "appeal_code__region", "appeal_code__dtype"
            )
            .annotate(
                excerpts_id=F("id"),
                component_title=F("per_component_validated__title"),
                sector_title=F("sector_validated__title"),
                country_id=F("appeal_code__country__id"),
                country_name=F("appeal_code__country__name"),
                region_id=F("appeal_code__region__id"),
                region_name=F("appeal_code__region__label"),
                appeal_name=F("appeal_code__name"),
                appeal_year=F("appeal_code__start_date"),
                dtype_name=F("appeal_code__dtype__name"),
            )
        )
        from per.drf_views import OpsLearningFilter

        ops_learning_filtered_qs = OpsLearningFilter(filter_data, queryset=ops_learning_qs).qs
        if not ops_learning_filtered_qs.exists():
            logger.info("No OPS learnings found for the given filter.")
            ops_learning_df = pd.DataFrame(
                columns=[
                    "id",
                    "excerpts_id",
                    "component",
                    "sector",
                    "learning",
                    "country_id",
                    "country_name",
                    "region_id",
                    "region_name",
                    "appeal_name",
                    "appeal_year",
                    "dtype_name",
                ]
            )
            return ops_learning_df
        ops_learning_df = pd.DataFrame.from_records(
            ops_learning_filtered_qs.values(
                "id",
                "excerpts_id",
                "component_title",
                "sector_title",
                "learning_validated",
                "country_id",
                "country_name",
                "region_id",
                "region_name",
                "appeal_name",
                "appeal_year",
                "dtype_name",
            )
        )
        ops_learning_df = ops_learning_df.rename(
            columns={"component_title": "component", "sector_title": "sector", "learning_validated": "learning"}
        )
        ops_learning_df.set_index("id", inplace=True)
        return ops_learning_df

    @classmethod
    def _generate_regional_prioritization_list(cls, df: pd.DataFrame):
        """Generates a list of regional prioritizations from the given data."""
        df_exploded = df.explode("components")
        regional_df = df_exploded.groupby(["region", "components"]).size().reset_index(name="count")
        regional_df = regional_df[regional_df["count"] > 2]
        regional_list = regional_df.groupby("region")["components"].apply(list).reset_index()
        return regional_list

    @classmethod
    def _generate_global_prioritization_list(cls, regional_df: pd.DataFrame):
        """Generates a global prioritization list from regional data."""
        global_df = regional_df.explode("components").groupby("components").size().reset_index(name="count")
        global_components = global_df[global_df["count"] > 2]["components"].tolist()
        global_list = {"global": global_components}
        return global_list

    @classmethod
    def _generate_country_prioritization_list(
        cls, regional_df: pd.DataFrame, global_components: list, prioritization_df: pd.DataFrame, country_df: pd.DataFrame
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
    def generate_priotization_list(cls):
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
        regional_list = cls._generate_regional_prioritization_list(per_priotization_df)
        global_list = cls._generate_global_prioritization_list(regional_list)
        country_list = cls._generate_country_prioritization_list(regional_list, global_list, per_priotization_df, country_df)
        logger.info("Prioritization list generated.")
        return regional_list, global_list, country_list

    @classmethod
    def prioritize(
        cls,
        df: pd.DataFrame,
        components_countries: dict,
        components_regions: dict,
        components_global: dict,
        type_prioritization: typing.Union[list, None],
    ):
        """Prioritizes components based on the type of prioritization."""

        def _add_new_component(prioritized_components, per_prioritized_components, df):
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
            most_frequent_components = _add_new_component(most_frequent_components, per_prioritized_components, df)

        mask = df["component"].isin(most_frequent_components)
        return df[mask]

    @classmethod
    def prioritize_components(
        cls,
        ops_learning_df: pd.DataFrame,
        regional_list,
        global_list,
        country_list,
    ):
        logger.info("Prioritizing components.")

        def _need_component_prioritization(df, MIN_DIF_COMPONENTS, MIN_DIF_EXCERPTS):
            """Determines if prioritization is needed based on unique components and learnings."""
            nb_dif_components = len(df["component"].unique())
            nb_dif_learnings = len(df["learning"].unique())
            return nb_dif_components > MIN_DIF_COMPONENTS and nb_dif_learnings > MIN_DIF_EXCERPTS

        def _identify_type_prioritization(df):
            """Identifies the type of prioritization required based on the data."""
            if len(df["country_id"].unique()) == 1:
                return "single-country"
            elif len(df["region_id"].unique()) == 1:
                return "single-region"
            elif len(df["region_id"].unique()) > 1:
                return "multi-region"
            return None

        def _contextualize_learnings(df):
            """Adds appeal year and event name as a contextualization of the learnings."""
            for index, row in df.iterrows():
                df.at[index, "learning"] = (
                    f"{row['excerpts_id']}. In {row['appeal_year']} in {row['appeal_name']}: {row['learning']}"
                )

            df = df.drop(columns=["appeal_name"])
            logger.info("Contextualization added to DataFrame.")
            return df

        components_countries = country_list.to_dict(orient="records")
        components_countries = {item["country"]: item["components"] for item in components_countries}

        components_regions = regional_list.to_dict(orient="records")
        components_regions = {item["region"]: item["components"] for item in components_regions}

        # Contectualize the learnings
        ops_learning_df = _contextualize_learnings(ops_learning_df)

        if _need_component_prioritization(ops_learning_df, cls.MIN_DIF_COMPONENTS, cls.MIN_DIF_EXCERPTS):
            type_prioritization = _identify_type_prioritization(ops_learning_df)
            prioritized_learnings = cls.prioritize(
                ops_learning_df, components_countries, components_regions, global_list, type_prioritization
            )
        else:
            prioritized_learnings = ops_learning_df
        logger.info("Prioritization of components completed.")
        return prioritized_learnings

    @classmethod
    def slice_dataframe(cls, df, limit=2000, encoding_name="cl100k_base"):
        df.loc[:, "count_temp"] = [cls.count_tokens(x, encoding_name) for x in df["learning"]]
        df.loc[:, "cumsum"] = df["count_temp"].cumsum()

        slice_index = None
        for i in range(1, len(df)):
            if df["cumsum"].iloc[i - 1] <= limit and df["cumsum"].iloc[i] > limit:
                slice_index = i - 1
                break

        if slice_index is not None:
            df_sliced = df.iloc[: slice_index + 1]
        else:
            df_sliced = df
        return df_sliced

    @classmethod
    def primary_prioritize_excerpts(cls, df: pd.DataFrame):
        """Prioritize the most recent excerpts within the token limit for primary insights."""
        logger.info("Prioritizing primary excerpts within token limit.")

        primary_learning_df = df.drop_duplicates(subset="learning")

        # Sort by 'appeal_name' and 'appeal_year' (descending for recency)
        primary_learning_df = primary_learning_df.sort_values(by=["appeal_name", "appeal_year"], ascending=[True, False])

        grouped = primary_learning_df.groupby("appeal_name")

        # Interleaved list of rows
        interleaved = list(chain(*zip_longest(*[group[1].itertuples(index=False) for group in grouped], fillvalue=None)))

        # Convert back to a DataFrame, removing any placeholder rows
        result = (
            pd.DataFrame(interleaved, columns=primary_learning_df.columns).dropna(subset=["appeal_name"]).reset_index(drop=True)
        )

        # Slice the Primary DataFrame
        sliced_primary_learning_df = cls.slice_dataframe(result, cls.PROMPT_DATA_LENGTH_LIMIT, cls.ENCODING_NAME)
        logger.info("Primary excerpts prioritized within token limit.")
        return sliced_primary_learning_df

    @classmethod
    def seconday_prioritize_excerpts(cls, df: pd.DataFrame):
        """Prioritize the most recent excerpts within the token limit for secondary insights."""
        logger.info("Prioritizing secondary excerpts within token limit.")

        # Droping duplicates based on 'appeal_name' 'learning' and 'component' columns for secondary DataFrame
        secondary_learning_df = df.drop_duplicates(subset=["learning", "component", "sector"]).sort_values(
            by=["appeal_name", "component", "appeal_year"], ascending=[True, True, False]
        )
        grouped = secondary_learning_df.groupby("component", "appeal_name")

        # Create an interleaved list of rows
        interleaved = list(chain(*zip_longest(*[group[1].itertuples(index=False) for group in grouped], fillvalue=None)))

        # Convert the interleaved list of rows back to a DataFrame
        result = (
            pd.DataFrame(interleaved, columns=secondary_learning_df.columns).dropna(subset=["component"]).reset_index(drop=True)
        )

        # Slice secondary DataFrame
        sliced_secondary_learning_df = cls.slice_dataframe(result, cls.PROMPT_DATA_LENGTH_LIMIT, cls.ENCODING_NAME)
        logger.info("Excerpts prioritized within token limit.")
        return sliced_secondary_learning_df

    @classmethod
    def _build_intro_section(cls):
        """Builds the introductory section of the prompt."""
        return (
            "I will provide you with a set of instructions, data, and formatting requests in three sections."
            + " I will pass you the INSTRUCTIONS section, are you ready?"
            + "\n\n"
        )

    @classmethod
    def _build_instruction_section(cls, request_filter: dict, df: pd.DataFrame, instruction: str):
        """Builds the instruction section of the prompt based on the request filter and DataFrame."""
        instructions = ["INSTRUCTIONS\n========================\nSummarize essential insights from the DATA"]

        if "appeal_code__dtype__in" in request_filter:
            dtypes = df["dtype_name"].dropna().unique()
            dtype_str = '", "'.join(dtypes)
            instructions.append(f'concerning "{dtype_str}" occurrences')

        if "appeal_code__country__in" in request_filter:
            countries = df["country_name"].dropna().unique()
            country_str = '", "'.join(countries)
            instructions.append(f'in "{country_str}"')

        if "appeal_code__region" in request_filter:
            regions = df["region_name"].dropna().unique()
            region_str = '", "'.join(regions)
            instructions.append(f'in "{region_str}"')

        if "sector_validated__in" in request_filter:
            sectors = df["sector"].dropna().unique()
            sector_str = '", "'.join(sectors)
            instructions.append(f'focusing on "{sector_str}" aspects')

        if "per_component_validated__in" in request_filter:
            components = df["component"].dropna().unique()
            component_str = '", "'.join(components)
            instructions.append(f'and "{component_str}" aspects')

        instructions.append("in Emergency Response. ")
        instructions.append("\n\n" + instruction)
        instructions.append("\n\nI will pass you the DATA section, are you ready?\n\n")
        return "\n".join(instructions)

    @classmethod
    def format_primary_prompt(
        cls,
        ops_learning_summary_instance: OpsLearningCacheResponse,
        primary_learning_df: pd.DataFrame,
        filter_data: dict,
    ):
        """Formats the primary prompt based on request filter and prioritized learnings."""
        logger.info("Formatting primary prompt.")

        # Primary learnings intro section
        prompt_intro = cls._build_intro_section()
        primary_prompt_instruction = cls._build_instruction_section(
            filter_data, primary_learning_df, cls.primary_instruction_prompt
        )

        # Primary learnings section
        primary_learnings_data = "\n----------------\n".join(primary_learning_df["learning"].dropna())

        primary_learning_data = primary_learning_df["excerpts_id"].dropna().tolist()

        # Adding the used extracts in primary insights
        cls.add_used_ops_learnings(
            ops_learning_summary_instance,
            used_ops_learnings=primary_learning_data,
        )

        # format the prompts
        primary_learning_prompt = "".join([prompt_intro, primary_prompt_instruction, primary_learnings_data, cls.primary_prompt])
        logger.info("Primary Prompt formatted.")
        return primary_learning_prompt

    @classmethod
    def format_secondary_prompt(
        cls,
        secondary_learning_df: pd.DataFrame,
        filter_data: dict,
    ):
        """Formats the prompt based on request filter and prioritized learnings."""
        logger.info("Formatting secondary prompt.")

        def get_main_sectors(df: pd.DataFrame):
            """Get only information from technical sectorial information"""
            temp = df[df["component"] == "NS-specific areas of intervention"]
            available_sectors = list(temp["sector"].unique())
            nb_sectors = len(available_sectors)
            if nb_sectors == 0:
                logger.info("There were not specific technical sectorial learnings")
                return []
            logger.info("Main sectors for secondary summaries selected")
            return available_sectors

        def get_main_components(df: pd.DataFrame):
            temp = df[df["component"] != "NS-specific areas of intervention"]
            available_components = list(temp["component"].unique())
            nb_components = len(available_components)
            if nb_components == 0:
                logger.info("There were not specific components")
                return []
            logger.info("All components for secondary summaries selected")
            return available_components

        def process_learnings_sector(sector, df, max_length_per_section):
            df = df[df["sector"] == sector].dropna()
            df_sliced = cls.slice_dataframe(df, max_length_per_section, cls.ENCODING_NAME)

            if df_sliced["learning"].empty:
                return ""

            learnings_sector = (
                "\n----------------\n"
                + "SUBTYPE: "
                + sector
                + "\n----------------\n"
                + "\n----------------\n".join(df_sliced["learning"])
                + "\n\n"
            )
            return learnings_sector

        def process_learnings_component(component, df, max_length_per_section):
            df = df[df["component"] == component].dropna()
            df_sliced = cls.slice_dataframe(df, max_length_per_section, cls.ENCODING_NAME)

            if df_sliced["learning"].empty:
                return ""

            learnings_component = (
                "\n----------------\n"
                + "SUBTYPE: "
                + component
                + "\n----------------\n"
                + "\n----------------\n".join(df_sliced["learning"])
                + "\n\n"
            )
            return learnings_component

        def _build_data_section(secondary_df: pd.DataFrame):
            # Secondary learnings section
            sectors = get_main_sectors(secondary_df)
            components = get_main_components(secondary_df)
            max_length_per_section = cls.PROMPT_DATA_LENGTH_LIMIT

            if (len(sectors) + len(components)) > 0:
                max_length_per_section = cls.PROMPT_DATA_LENGTH_LIMIT / (len(components) + len(sectors))

            learnings_sectors = (
                "\n----------------\n\n"
                + "TYPE: SECTORS"
                + "\n----------------\n".join(
                    [process_learnings_sector(x, secondary_df, max_length_per_section) for x in sectors if pd.notna(x)]
                )
            )
            learnings_components = (
                "\n----------------\n\n"
                + "TYPE: COMPONENT"
                + "\n----------------\n".join(
                    [process_learnings_component(x, secondary_df, max_length_per_section) for x in components if pd.notna(x)]
                )
            )
            secondary_learnings_data = learnings_sectors + learnings_components
            return secondary_learnings_data

        prompt_intro = cls._build_intro_section()
        secondary_prompt_instruction = cls._build_instruction_section(
            filter_data, secondary_learning_df, cls.secondary_instruction_prompt
        )
        secondary_learnings_data = _build_data_section(secondary_learning_df)

        # format the prompts
        secondary_learning_prompt = "".join(
            [prompt_intro, secondary_prompt_instruction, secondary_learnings_data, cls.secondary_prompt]
        )
        logger.info("Secondary Prompt formatted.")
        return secondary_learning_prompt

    @classmethod
    def generate_summary(cls, prompt, type: OpsLearningPromptResponseCache.PromptType) -> dict:
        """Generates summaries using the provided system message and prompt."""
        logger.info(f"Generating summaries for {type.name} prompt.")

        def _validate_length_prompt(messages, prompt_length_limit, type):
            """Validates the length of the prompt."""
            message_content = [msg["content"] for msg in messages]
            text = " ".join(message_content)
            count = cls.count_tokens(text, cls.ENCODING_NAME)
            logger.info(f"{type.name} Token count: {count}")
            return count <= prompt_length_limit

        def _summarize(prompt, type: OpsLearningPromptResponseCache.PromptType, system_message="You are a helpful assistant"):
            """Summarizes the prompt using the provided system message."""
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
                {
                    "role": "assistant",
                    "content": "Understood, thank you for providing the data, and formatting requests. "
                    + "I am ready to proceed with the task.",
                },
            ]

            if not _validate_length_prompt(messages, cls.PROMPT_LENGTH_LIMIT, type):
                logger.warning("The length of the prompt might be too long.")
                return "{}"

            # Using Azure OpenAI to summarize the prompt
            client = AzureOpenAiChat()
            response = client.get_response(message=messages)
            return response

        def _validate_format(summary, MAX_RETRIES=3):
            """
            Validates the format of the summary and modifies it if necessary.
            """

            def _validate_text_is_dictionary(text) -> bool:
                """
                Try to parse the text as a dictionary and check if it is a valid dictionary
                """
                try:
                    formatted_text = ast.literal_eval(text)
                    return isinstance(formatted_text, dict)
                except (SyntaxError, ValueError):
                    return False

            def _modify_format(summary) -> str:
                try:
                    # Find the index of the last closing brace before the "Note"
                    end_index = summary.rfind("}")

                    # Truncate the string to include only the dictionary part
                    formatted_summary = summary[: end_index + 1]

                    logger.info("Modification realized to response")
                    return formatted_summary

                # NOTE: If the modification fails, it returns empty and it retries to generate the summary again
                except Exception:
                    return "{}"

            formatted_summary = {}
            retires = 0

            # Attempt to parse the summary as a dictionary
            if _validate_text_is_dictionary(summary):
                formatted_summary = ast.literal_eval(summary)
            else:
                formatted_summary = _modify_format(summary)
                formatted_summary = ast.literal_eval(formatted_summary)

            # Checking if the generated summary is empty
            if bool(formatted_summary):
                return formatted_summary

            # NOTE: Generating the summary if summary is empty
            while retires < MAX_RETRIES:
                cls.generate_summary(prompt, type)
                retires += 1
                logger.info(f"Retrying.... Attempt {retires}/{MAX_RETRIES}")

        def _modify_summary(summary: dict) -> dict:
            """
            Checks if the "Confidence level" is present in the primary response and skipping for the secondary summary
            """
            for key, value in summary.items():
                if key == "contradictory reports":
                    continue

                content = value.get("content", "")
                excerpt_ids = value.get("excerpts id", "")
                excerpt_id_list = (
                    list(set(excerpt_ids))
                    if isinstance(excerpt_ids, list)
                    else list(set(int(id.strip()) for id in excerpt_ids.split(",") if excerpt_ids and excerpt_ids != ""))
                )

                # Check if any excerpt id is present in the content and regenerate the summary if found
                if any(re.search(rf"\b{id}\b", content) for id in excerpt_id_list):
                    return cls.generate_summary(prompt, type)

                value["content"] = content
                value["excerpts id"] = excerpt_id_list

                # Extract and remove if `confidence level` exists in the content
                confidence_level = "confidence level"
                if confidence_level not in value and confidence_level in content.lower():
                    parts = re.split(rf"(?i)\b{confidence_level}\b", content, maxsplit=1)
                    value["content"] = parts[0].strip() + "."
                    value["confidence level"] = parts[1].strip()

            return summary

        summary = _summarize(prompt, type, cls.system_message)
        formatted_summary = _validate_format(summary)
        processed_summary = _modify_summary(formatted_summary)
        logger.info(f"Summaries generated for {type.name}")
        return processed_summary

    @classmethod
    def _get_or_create_summary(
        cls, prompt: str, prompt_hash: str, type: OpsLearningPromptResponseCache.PromptType, overwrite_prompt_cache: bool = False
    ) -> dict:
        instance, created = OpsLearningPromptResponseCache.objects.update_or_create(
            prompt_hash=prompt_hash,
            type=type,
            defaults={"prompt": prompt},
        )
        """
        NOTE:
        1. If the prompt response is not found in the cache, it regenerates the summary
        2. If overwrite_prompt_cache is True, it regenerates the summary
        3. If new obj is created, it generates the summary
        """
        if overwrite_prompt_cache or created or bool(instance.response) is False:
            summary = cls.generate_summary(prompt, type)
            instance.response = summary
            instance.save(update_fields=["response"])
            return summary
        return instance.response

    @classmethod
    def primary_response_save_to_db(
        cls,
        ops_learning_summary_instance: OpsLearningCacheResponse,
        primary_summary: dict,
    ):
        """Saves the primary response to the database."""
        logger.info("Saving primary response to the database.")

        # Mapping between summary keys and model fields
        fields_mapping = {
            "0": {
                "title": OpsLearningCacheResponse.insights1_title,
                "content": OpsLearningCacheResponse.insights1_content,
                "confidence level": OpsLearningCacheResponse.insights1_confidence_level,
            },
            "1": {
                "title": OpsLearningCacheResponse.insights2_title,
                "content": OpsLearningCacheResponse.insights2_content,
                "confidence level": OpsLearningCacheResponse.insights2_confidence_level,
            },
            "2": {
                "title": OpsLearningCacheResponse.insights3_title,
                "content": OpsLearningCacheResponse.insights3_content,
                "confidence level": OpsLearningCacheResponse.insights3_confidence_level,
            },
            "contradictory reports": OpsLearningCacheResponse.contradictory_reports,
        }
        for summary_key, model_fields in fields_mapping.items():
            if summary_key in primary_summary:
                summary_data = primary_summary[summary_key]

                if isinstance(model_fields, dict):
                    for summary_field, model_field in model_fields.items():
                        if summary_field in summary_data:
                            setattr(ops_learning_summary_instance, model_field.field.name, summary_data[summary_field].strip())
                else:
                    setattr(ops_learning_summary_instance, model_fields.field.name, primary_summary[summary_key])
        ops_learning_summary_instance.save()

        logger.info("Primary response saved to the database.")

    @classmethod
    def secondary_response_save_to_db(
        cls,
        ops_learning_summary_instance: OpsLearningCacheResponse,
        secondary_summary: dict,
    ):
        logger.info("Saving secondary response to the database.")
        # Secondary summary
        for _, value in secondary_summary.items():
            type = value["type"].strip()
            subtype = value["subtype"].strip()
            content = value["content"].strip()
            excerpt_id_list = value["excerpts id"]

            if type == "component" and len(excerpt_id_list) > 0:
                cls.add_used_ops_learnings_component(
                    instance=ops_learning_summary_instance,
                    content=content,
                    used_ops_learnings=excerpt_id_list,
                    component=subtype,
                )

            if type == "sector" and len(excerpt_id_list) > 0:
                cls.add_used_ops_learnings_sector(
                    instance=ops_learning_summary_instance,
                    content=content,
                    used_ops_learnings=excerpt_id_list,
                    sector=subtype,
                )
        logger.info("Secondary response saved to the database.")

    @classmethod
    def get_or_create_primary_summary(
        cls,
        ops_learning_summary_instance: OpsLearningCacheResponse,
        primary_learning_prompt: str,
        overwrite_prompt_cache: bool = False,
    ):
        """Retrieves or Generates the primary summary based on the provided prompt."""
        logger.info("Retrieving or generating primary summary.")

        # generating hash for primary prompt
        primary_prompt_hash = OpslearningSummaryCacheHelper.generate_hash(primary_learning_prompt)

        # Checking the response for primary prompt
        primary_summary = cls._get_or_create_summary(
            prompt=primary_learning_prompt,
            prompt_hash=primary_prompt_hash,
            type=OpsLearningPromptResponseCache.PromptType.PRIMARY,
            overwrite_prompt_cache=overwrite_prompt_cache,
        )

        # Saving into the database
        cls.primary_response_save_to_db(
            ops_learning_summary_instance=ops_learning_summary_instance,
            primary_summary=primary_summary,
        )

        # Translating the primary summary
        transaction.on_commit(
            lambda: translate_model_fields.delay(
                get_model_name(type(ops_learning_summary_instance)),
                ops_learning_summary_instance.pk,
            )
        )

    @classmethod
    def get_or_create_secondary_summary(
        cls,
        ops_learning_summary_instance: OpsLearningCacheResponse,
        secondary_learning_prompt: str,
        overwrite_prompt_cache: bool = False,
    ):
        """Retrieves or Generates the summary based on the provided prompts."""
        logger.info("Retrieving or generating secondary summary.")

        # generating hash for secondary prompt
        secondary_prompt_hash = OpslearningSummaryCacheHelper.generate_hash(secondary_learning_prompt)

        # Checking the response for secondary prompt
        secondary_summary = cls._get_or_create_summary(
            prompt=secondary_learning_prompt,
            prompt_hash=secondary_prompt_hash,
            type=OpsLearningPromptResponseCache.PromptType.SECONDARY,
            overwrite_prompt_cache=overwrite_prompt_cache,
        )
        if overwrite_prompt_cache:
            logger.info("Clearing the cache for secondary summary.")
            # NOTE: find a better way to update the cache
            OpsLearningComponentCacheResponse.objects.filter(filter_response=ops_learning_summary_instance).delete()
            OpsLearningSectorCacheResponse.objects.filter(filter_response=ops_learning_summary_instance).delete()

        # Saving into the database
        cls.secondary_response_save_to_db(
            ops_learning_summary_instance=ops_learning_summary_instance,
            secondary_summary=secondary_summary,
        )
