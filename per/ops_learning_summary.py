import ast
import os
import typing
from itertools import chain

import pandas as pd
import tiktoken
from django.conf import settings
from django.db.models import F
from openai import AzureOpenAI

from api.logger import logger
from api.models import Country
from deployments.models import SectorTag
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


class OpsLearningSummaryTask:

    PROMPT_DATA_LENGTH_LIMIT = 5000
    PROMPT_LENGTH_LIMIT = 7500
    ENCODING_NAME = "cl100k_base"

    MIN_DIF_COMPONENTS = 3
    MIN_DIF_EXCERPTS = 3

    primary_prompt = (
        "Please aggregate and summarize the provided data into UP TO THREE structured paragraphs. "
        "The output MUST strictly adhere to the format below: "
        "- Title: Each finding should begin with the main finding TITLE in bold. "
        "- Content: Aggregate findings so that they are supported by evidence from more than one report. "
        "Always integrate evidence from multiple reports or items into the paragraph, and "
        "include the year and country of the evidence."
        "- Confidence Level: For each finding, based on the number of items/reports connected to the finding, "
        "assign a score from 1 to 5 where 1 is the lowest and 5 is the highest. "
        "The format should be 'Confidence level: #/5' (e.g., 'Confidence level: 4/5'). "
        "At the end of the summary, please highlight any contradictory country reports. "
        "DO NOT use data from any source other than the one provided. Provide your answer in JSON form. "
        "Reply with only the answer in valid JSON form and include no other commentary: "
        "Example: "
        '{"0": {"title": "Flexible and Adaptive Response Planning", '
        '"content": "Responses in Honduras, Peru, Ecuador, and Panama highlight the importance of adaptable strategies. '
        "The shift from youth-focused MHPSS to inclusive care in Peru in 2021, the pivot from sanitation infrastructure "
        "to direct aid in Ecuador in 2022, and the responsive livelihood support in Panama in 2020, "
        "all underscore the need for continuous reassessment and agile adaptation to the complex, "
        'changing needs of disaster-affected communities.", "confidence level": "4/5"}, '
        '"1": {"title": "...", "content": "...", "confidence level": "..."}, '
        '"2": {"title": "...", "content": "...", "confidence level": "..."}, '
        '"contradictory reports": "..."}'
    )

    secondary_prompt = (
        "Please aggregate and summarize this data into structured paragraphs (as few as possible, as many as necessary). "
        "The output SHOULD ALWAYS follow the format below: "
        "Type: Whether the paragraph is related to a 'sector' or a 'component'. "
        "Subtype: Provides the name of the sector or of the component to which the paragraph refers. "
        "Content: A short summary aggregating findings related to the Subtype, so that they are supported by "
        "evidence coming from more than one report, "
        "and there is ONLY ONE entry per subtype. Always integrate in the paragraph evidence that supports it "
        "from the data available from multiple reports or items, "
        "include year and country of the evidence. DO NOT use data from any source other than the "
        "one provided. Provide your answer in JSON form. "
        "Reply with ONLY the answer in valid JSON form and include NO OTHER COMMENTARY: "
        '{"0": {"type": "sector", "subtype": "shelter", "content": "lorem ipsum"}, '
        '"1": {"type": "component", "subtype": "Information Management (IM)", "content": "lorem ipsum"}, '
        '"2": {"type": "sector", "subtype": "WASH", "content": "lorem ipsum"}}'
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
        "You should:"
        "1. Describe, Summarize and Compare: Identify and detail the who, what, where, when and how many."
        "2. Explain and Connect: Analyze why events happened and how they are related"
        "3. Identify gaps: Assess what data is available, what is missing and potential biases"
        "4. Identify key messages: Determine important stories and signals hidden in the data"
        "5. Select top three: Select up to three findings to report"
    )

    secondary_instruction_prompt = (
        "You should for each section in the data (TYPE & SUBTYPE combination):"
        "1. Describe, Summarize and Compare: Identify and detail the who, what, where, when and how many."
        "2. Explain and Connect: Analyze why events happened and how they are related"
        "3. Identify gaps: Assess what data is available, what is missing and potential biases"
        "4. Identify key messages: Determine if there are important stories and signals hidden in the data"
        "5. Conclude and make your case"
    )

    client = AzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT, api_key=settings.AZURE_OPENAI_KEY, api_version="2023-05-15"
    )

    def count_tokens(string, encoding_name):
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(string))

    @classmethod
    def fetch_ops_learnings(self, filter_data):
        """Fetches the OPS learnings from the database."""
        ops_learning_qs = OpsLearning.objects.annotate(
            component_title=F("per_component__title"),
            sector_title=F("sector__title"),
            ops_learning_id=F("id"),
        )
        from per.drf_views import OpsLearningFilter

        ops_learning_filtered_qs = OpsLearningFilter(filter_data, queryset=ops_learning_qs).qs
        ops_learning_df = pd.DataFrame(
            list(
                ops_learning_filtered_qs.values(
                    "id",
                    "ops_learning_id",
                    "component_title",
                    "learning",
                    "appeal_code__country_id",
                    "appeal_code__country__region_id",
                    "appeal_code__name",
                    "appeal_code__start_date",
                    "sector_title",
                )
            )
        )
        ops_learning_df = ops_learning_df.rename(
            columns={
                "component_title": "component",
                "sector_title": "sector",
                "appeal_code__country_id": "country_id",
                "appeal_code__country__region_id": "region_id",
                "appeal_code__name": "appeal_name",
                "appeal_code__start_date": "appeal_year",
            }
        )
        ops_learning_df.set_index("id", inplace=True)
        return ops_learning_df

    @classmethod
    def _generate_regional_prioritization_list(self, df: pd.DataFrame):
        """Generates a list of regional prioritizations from the given data."""
        df_exploded = df.explode("components")
        regional_df = df_exploded.groupby(["region", "components"]).size().reset_index(name="count")
        regional_df = regional_df[regional_df["count"] > 2]
        regional_list = regional_df.groupby("region")["components"].apply(list).reset_index()
        return regional_list

    @classmethod
    def _generate_global_prioritization_list(self, regional_df: pd.DataFrame):
        """Generates a global prioritization list from regional data."""
        global_df = regional_df.explode("components").groupby("components").size().reset_index(name="count")
        global_components = global_df[global_df["count"] > 2]["components"].tolist()
        global_list = {"global": global_components}
        return global_list

    @classmethod
    def _generate_country_prioritization_list(
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
        regional_list = self._generate_regional_prioritization_list(per_priotization_df)
        global_list = self._generate_global_prioritization_list(regional_list)
        country_list = self._generate_country_prioritization_list(regional_list, global_list, per_priotization_df, country_df)
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
        self,
        filter_data: dict,
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
            """Adds appeal year and event name as a contextualization of the leannings."""
            for index, row in df.iterrows():
                df.at[index, "learning"] = f"In {row['appeal_year']} in {row['appeal_name']}: {row['learning']}"

            df = df.drop(columns=["appeal_name"])
            logger.info("Contextualization added to DataFrame.")
            return df

        components_countries = country_list.to_dict(orient="records")
        components_countries = {item["country"]: item["components"] for item in components_countries}

        components_regions = regional_list.to_dict(orient="records")
        components_regions = {item["region"]: item["components"] for item in components_regions}

        ops_learning_df = self.fetch_ops_learnings(filter_data)

        if _need_component_prioritization(ops_learning_df, self.MIN_DIF_COMPONENTS, self.MIN_DIF_EXCERPTS):
            type_prioritization = _identify_type_prioritization(ops_learning_df)
            prioritized_learnings = self.prioritize(
                ops_learning_df, components_countries, components_regions, global_list, type_prioritization
            )
        prioritized_learnings = ops_learning_df
        logger.info("Prioritization of components completed.")
        prioritized_learnings = _contextualize_learnings(prioritized_learnings)
        return prioritized_learnings

    @classmethod
    def slice_dataframe(self, df, limit=2000, encoding_name="cl100k_base"):
        df["count_temp"] = [self.count_tokens(x, encoding_name) for x in df["learning"]]
        df["cumsum"] = df["count_temp"].cumsum()

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
    def prioritize_excerpts(self, df: pd.DataFrame):
        """Prioritize the most recent excerpts within the token limit."""
        logger.info("Prioritizing excerpts within token limit.")

        # Droping duplicates based on 'learning' column for primary DataFrame
        primary_learning_df = df.drop_duplicates(subset="learning")
        primary_learning_df = primary_learning_df.sort_values(by="appeal_year", ascending=False)
        primary_learning_df.reset_index(inplace=True, drop=True)

        # Droping duplicates based on 'learning' and 'component' columns for secondary DataFrame
        secondary_learning_df = df.drop_duplicates(subset=["learning", "component"])
        secondary_learning_df = secondary_learning_df.sort_values(by=["component", "appeal_year"], ascending=[True, False])
        grouped = secondary_learning_df.groupby("component")

        # Create an interleaved list of rows
        interleaved = list(chain(*zip(*[group[1].itertuples(index=False) for group in grouped])))

        # Convert the interleaved list of rows back to a DataFrame
        result = pd.DataFrame(interleaved)
        result.reset_index(inplace=True, drop=True)

        # Slice the Primary and secondary dataframes
        sliced_primary_learning_df = self.slice_dataframe(primary_learning_df, self.PROMPT_DATA_LENGTH_LIMIT, self.ENCODING_NAME)
        sliced_secondary_learning_df = self.slice_dataframe(result, self.PROMPT_DATA_LENGTH_LIMIT, self.ENCODING_NAME)
        logger.info("Excerpts prioritized within token limit.")
        return sliced_primary_learning_df, sliced_secondary_learning_df

    @classmethod
    def format_prompt(
        self,
        primary_learning_df: pd.DataFrame,
        secondary_learning_df: pd.DataFrame,
        filter_data: dict,
    ):
        """Formats the prompt based on request filter and prioritized learnings."""
        logger.info("Formatting prompt.")

        def _build_intro_section():
            """Builds the introductory section of the prompt."""
            return (
                "I will provide you with a set of instructions, data, and formatting requests in three sections."
                + " I will pass you the INSTRUCTIONS section, are you ready?"
                + os.linesep
                + os.linesep
            )

        def _build_instruction_section(request_filter: dict, df: pd.DataFrame, instruction: str):
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

            instructions.append("in Emergency Response.")
            instructions.append("\n\n" + instruction)
            instructions.append("\n\nI will pass you the DATA section, are you ready?\n\n")
            return "\n".join(instructions)

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
            available_components = list(df["component"].unique())
            nb_components = len(available_components)
            if nb_components == 0:
                logger.info("There were not specific components")
                return []
            logger.info("All components for secondary summaries selected")
            return available_components

        def process_learnings_sector(sector, df, max_length_per_section):
            df = df[df["sector"] == sector].dropna()
            df_sliced = self.slice_dataframe(df, max_length_per_section, self.ENCODING_NAME)
            learnings_sector = (
                "\n----------------\n"
                + "SUBTYPE: "
                + sector
                + "\n----------------\n"
                + "\n----------------\n".join(df_sliced["learning"])
            )
            return learnings_sector

        def process_learnings_component(component, df, max_length_per_section):
            df = df[df["component"] == component].dropna()
            df_sliced = self.slice_dataframe(df, max_length_per_section, self.ENCODING_NAME)
            learnings_component = (
                "\n----------------\n"
                + "SUBTYPE: "
                + component
                + "\n----------------\n"
                + "\n----------------\n".join(df_sliced["learning"])
            )
            return learnings_component

        def _build_data_section(primary_df: pd.DataFrame, secondary_df: pd.DataFrame):
            # Primary learnings section
            primary_learnings_data = "\n----------------\n".join(primary_df["learning"].dropna())

            # Secondary learnings section
            sectors = get_main_sectors(secondary_df)
            components = get_main_components(secondary_df)
            max_length_per_section = self.PROMPT_DATA_LENGTH_LIMIT / (len(components) + len(sectors))
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
            return primary_learnings_data, secondary_learnings_data

        prompt_intro = _build_intro_section()
        primary_prompt_instruction = _build_instruction_section(filter_data, primary_learning_df, self.primary_instruction_prompt)
        secondary_prompt_instruction = _build_instruction_section(
            filter_data, secondary_learning_df, self.secondary_instruction_prompt
        )
        primary_learnings_data, secondary_learnings_data = _build_data_section(primary_learning_df, secondary_learning_df)

        # format the prompts
        primary_learning_prompt = "".join([prompt_intro, primary_prompt_instruction, primary_learnings_data, self.primary_prompt])
        secondary_learning_prompt = "".join(
            [prompt_intro, secondary_prompt_instruction, secondary_learnings_data, self.secondary_prompt]
        )
        logger.info("Prompt formatted.")
        return primary_learning_prompt, secondary_learning_prompt

    @classmethod
    def generate_summary(self, prompt, type: OpsLearningPromptResponseCache.PromptType) -> dict:
        """Generates summaries using the provided system message and prompt."""
        logger.info(f"Generating summaries for {type.name} prompt.")

        def _validate_length_prompt(messages, prompt_length_limit, type):
            """Validates the length of the prompt."""
            message_content = [msg["content"] for msg in messages]
            text = " ".join(message_content)
            count = self.count_tokens(text, self.ENCODING_NAME)
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

            if not _validate_length_prompt(messages, self.PROMPT_LENGTH_LIMIT, type):
                logger.warning("The length of the prompt might be too long.")
                return "{}"

            try:
                response = self.client.chat.completions.create(
                    model=settings.AZURE_OPENAI_DEPLOYMENT_NAME, messages=messages, temperature=0.7
                )
                summary = response.choices[0].message.content
                return summary
            except Exception as e:
                logger.error(f"Error in summarizing: {e}")
                raise

        def _validate_format(summary) -> bool:
            """
            Validates the format of the summary and modifies it if necessary.
            """

            def _validate_text_is_dictionary(text):
                formatted_text = ast.literal_eval(text)
                return isinstance(formatted_text, dict)

            def _modify_format(summary) -> str:
                try:
                    # Find the index of the last closing brace before the "Note"
                    end_index = summary.rfind("}")

                    # Truncate the string to include only the dictionary part
                    formatted_summary = summary[: end_index + 1]

                    logger.info("Modification realized to response")
                    return formatted_summary

                except Exception as e:
                    logger.error(f"Modification failed: {e}")
                    return "{}"

            formatted_summary = {}
            # Attempt to parse the summary as a dictionary
            if _validate_text_is_dictionary(summary):
                formated_summary = ast.literal_eval(summary)
                return formated_summary
            else:
                formatted_summary = _modify_format(summary)
                formatted_summary = ast.literal_eval(formatted_summary)
                return formatted_summary

        def _modify_summary(summary: dict) -> dict:
            """
            Checks if the "Confidence level" is present in the primary response and skipping for the secondary summary
            """
            for key, value in summary.items():
                if key == "contradictory reports":
                    continue
                if "Confidence level" in value["content"]:
                    confidence_value = value["content"].split("Confidence level:")[-1]
                    value["content"] = value["content"].split("Confidence level:")[0]
                    value["confidence level"] = confidence_value

            return summary

        summary = _summarize(prompt, type, self.system_message)
        formated_summary = _validate_format(summary)
        processed_summary = _modify_summary(formated_summary)
        logger.info(f"Summaries generated for {type.name}")
        return processed_summary

    @classmethod
    def _get_or_create_summary(self, prompt: str, prompt_hash: str, type: OpsLearningPromptResponseCache.PromptType) -> dict:
        instance, created = OpsLearningPromptResponseCache.objects.get_or_create(
            prompt_hash=prompt_hash,
            type=type,
            defaults={"prompt": prompt},
        )
        if not created:
            summary = instance.response
            return summary
        summary = self.generate_summary(prompt=prompt, type=type)
        instance.response = summary
        instance.save(update_fields=["response"])
        return summary

    @classmethod
    def save_to_db(
        self,
        ops_learning_summary_instance: OpsLearningCacheResponse,
        primary_summary: dict,
        secondary_summary: dict,
    ):
        logger.info("Saving to database.")
        # Primary summary
        ops_learning_summary_instance.insights1_title = primary_summary["0"]["title"]
        ops_learning_summary_instance.insights2_title = primary_summary["1"]["title"]
        ops_learning_summary_instance.insights3_title = primary_summary["2"]["title"]
        ops_learning_summary_instance.insights1_content = primary_summary["0"]["content"]
        ops_learning_summary_instance.insights2_content = primary_summary["1"]["content"]
        ops_learning_summary_instance.insights3_content = primary_summary["2"]["content"]
        ops_learning_summary_instance.insights1_confidence_level = primary_summary["0"]["confidence level"]
        ops_learning_summary_instance.insights2_confidence_level = primary_summary["1"]["confidence level"]
        ops_learning_summary_instance.insights3_confidence_level = primary_summary["2"]["confidence level"]
        ops_learning_summary_instance.contradictory_reports = primary_summary["contradictory reports"]
        ops_learning_summary_instance.save(
            update_fields=[
                "insights1_title",
                "insights2_title",
                "insights3_title",
                "insights1_content",
                "insights2_content",
                "insights3_content",
                "insights1_confidence_level",
                "insights2_confidence_level",
                "insights3_confidence_level",
                "contradictory_reports",
            ]
        )

        # Secondary summary
        for key, value in secondary_summary.items():
            type = value["type"]
            subtype = value["subtype"]
            content = value["content"]

            if type == "component":
                component_instance = FormComponent.objects.filter(
                    title__iexact=subtype,
                ).first()
                if not component_instance:
                    logger.error(f"Component '{subtype}' not found.")
                    continue
                OpsLearningComponentCacheResponse.objects.create(
                    component=component_instance,
                    content=content,
                    filter_response=ops_learning_summary_instance,
                )
            elif type == "sector":
                sector_instance = SectorTag.objects.filter(
                    title__iexact=subtype,
                ).first()
                if not sector_instance:
                    logger.error(f"Sector '{subtype}' not found.")
                    continue
                OpsLearningSectorCacheResponse.objects.create(
                    sector=sector_instance,
                    content=content,
                    filter_response=ops_learning_summary_instance,
                )
            else:
                logger.error(f"Invalid type '{type}' on secondary summary.")

        logger.info("Saved to database.")

    @classmethod
    def get_or_create_summary(
        self,
        ops_learning_summary_instance: OpsLearningCacheResponse,
        primary_learning_prompt: str,
        secondary_learning_prompt: str,
    ):
        """Retrieves or Generates the summary based on the provided prompts."""
        logger.info("Retrieving or generating summary.")

        # generating hash for both primary and secondary prompt
        primary_prompt_hash = OpslearningSummaryCacheHelper.generate_hash(primary_learning_prompt)
        secondary_prompt_hash = OpslearningSummaryCacheHelper.generate_hash(secondary_learning_prompt)

        # Checking the response for primary prompt
        primary_summary = self._get_or_create_summary(
            prompt=primary_learning_prompt,
            prompt_hash=primary_prompt_hash,
            type=OpsLearningPromptResponseCache.PromptType.PRIMARY,
        )

        # Checking the response for secondary prompt
        secondary_summary = self._get_or_create_summary(
            prompt=secondary_learning_prompt,
            prompt_hash=secondary_prompt_hash,
            type=OpsLearningPromptResponseCache.PromptType.SECONDARY,
        )

        # Saving into the database
        self.save_to_db(ops_learning_summary_instance, primary_summary, secondary_summary)
