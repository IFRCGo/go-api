"""
DREF AI summary generation.
"""

import hashlib
import json
import logging
from typing import Callable, Dict, List, Optional

import tiktoken
from django.conf import settings
from django.utils.functional import cached_property
from openai import AzureOpenAI

from dref.models import Dref, DrefFinalReport, DrefOperationalUpdate

logger = logging.getLogger(__name__)

ENCODING_NAME = "cl100k_base"

MAX_OUTPUT_CHARS_PER_FIELD = 1500
MAX_INPUT_TOKENS = 10000

# DrefSummary fields — order is the iteration order for prompt assembly.
SUMMARY_FIELDS: List[str] = [
    "situational_overview",
    "operational_strategy",
    "people_centered_approach",
    "challenges_identified",
    "lessons_learned",
]

SYSTEM_MESSAGE = (
    "You are an IFRC expert analyst specializing in DREF (Disaster Response Emergency Fund) "
    "operations. Analyze the provided DREF data and produce clear, professional humanitarian "
    "summaries suitable for IFRC staff and National Society personnel. Use only the information "
    "provided in the data; do not invent facts, figures, or details. Where supporting information "
    "for a section is absent, return an empty string for that section rather than speculating."
)

# Section prompt builders


def _build_situational_overview_prompt(**kwargs) -> str:
    data = {k: v for k, v in kwargs.items() if v not in (None, "", [], {})}
    data_json = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    return (
        'Data for "situational_overview" — disaster context, affected areas, '
        f"scale of impact and strategic rationale for the operation:\n{data_json}"
    )


def _build_operational_strategy_prompt(**kwargs) -> str:
    data = {k: v for k, v in kwargs.items() if v not in (None, "", [], {})}
    data_json = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    return (
        'Data for "operational_strategy" — operation objective, response strategy, '
        f"target population, timeframe and budget:\n{data_json}"
    )


def _build_people_centered_approach_prompt(**kwargs) -> str:
    data = {k: v for k, v in kwargs.items() if v not in (None, "", [], {})}
    data_json = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    return (
        'Data for "people_centered_approach" — targeting criteria, beneficiary selection, '
        f"engagement and protection approach:\n{data_json}"
    )


def _build_challenges_identified_prompt(**kwargs) -> str:
    data = {k: v for k, v in kwargs.items() if v not in (None, "", [], {})}
    data_json = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    return (
        'Data for "challenges_identified" — operational challenges, gaps, coordination '
        f"issues and security/safety risks recorded per planned intervention:\n{data_json}"
    )


def _build_lessons_learned_prompt(**kwargs) -> str:
    data = {k: v for k, v in kwargs.items() if v not in (None, "", [], {})}
    data_json = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    return (
        'Data for "lessons_learned" — lessons learnt recorded per planned intervention ' f"(empty if none recorded):\n{data_json}"
    )


# Registry
SECTION_PROMPT_BUILDERS: Dict[str, Callable[..., str]] = {
    "situational_overview": _build_situational_overview_prompt,
    "operational_strategy": _build_operational_strategy_prompt,
    "people_centered_approach": _build_people_centered_approach_prompt,
    "challenges_identified": _build_challenges_identified_prompt,
    "lessons_learned": _build_lessons_learned_prompt,
}

GLOBAL_PROMPT = (
    "The DREF data above is organised by summary section. Using ONLY that data, write five concise "
    "summary sections. Return a single JSON object (and nothing else) with exactly these keys:\n"
    "\n"
    '  "situational_overview": The disaster situation, affected areas and scale of impact, plus the '
    'strategic rationale for the operation. Use the data under the "situational_overview" key. '
    "Write a coherent paragraph; include specific figures where available (e.g. people affected, displaced).\n"
    '  "operational_strategy": The overall objective and strategic approach of the response. Use the '
    'data under the "operational_strategy" key. State the target population, timeframe and headline '
    "interventions where available.\n"
    '  "people_centered_approach": Who is targeted and how they are selected, engaged and protected. '
    'Use the data under the "people_centered_approach" key, including the women/men/girls/boys '
    "breakdown where given.\n"
    '  "challenges_identified": The challenges, gaps, coordination issues and security/safety risks. '
    'Use the data under the "challenges_identified" key.\n'
    '  "lessons_learned": The lessons learned from this operation. Use the data under the '
    '"lessons_learned" key. If none are recorded, return an empty string.\n'
    "\n"
    "Requirements:\n"
    "- Each value must be plain text (no markdown, no bullet lists, no nested JSON).\n"
    "- Each section should be one well-structured paragraph in professional humanitarian language.\n"
    "- Be precise with any facts or numbers; never fabricate them.\n"
    "- Return ONLY the JSON object, with no surrounding prose or code fences."
)


class DrefSummaryLLMClient:
    @cached_property
    def client(self):
        return AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_KEY,
            api_version="2023-05-15",
        )

    def get_response(self, messages) -> Optional[str]:
        try:
            response = self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
                temperature=0.5,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error while generating DREF summary response: {e}", exc_info=True)
            return None


def count_tokens(text: str) -> int:
    try:
        return len(tiktoken.get_encoding(ENCODING_NAME).encode(text))
    except Exception as e:
        logger.error(f"Error counting tokens for DREF summary: {e}")
        return len(text) // 4


def _field_val(obj, field_name):
    """Return a model field's value, preferring human-readable display for choice fields."""
    v = getattr(obj, field_name, None)
    if v in (None, ""):
        return None
    display = getattr(obj, f"get_{field_name}_display", None)
    return display() if callable(display) else v


def _extract_fields(obj, field_names: List[str]) -> dict:
    return {name: v for name in field_names if (v := _field_val(obj, name)) is not None}


# Shared field lists.

SITUATIONAL_COMMON_FIELDS: List[str] = ["title", "event_description", "date_of_approval"]

OPERATIONAL_COMMON_FIELDS: List[str] = [
    "operation_objective",
    "response_strategy",
    "total_targeted_population",
    "people_in_need",
    "event_date",
]

PEOPLE_COMMON_FIELDS: List[str] = ["people_assisted", "selection_criteria"]

DEMOGRAPHIC_FIELDS: List[str] = ["women", "men", "girls", "boys"]


class DrefSummaryGenerator:
    """Assembles per-section prompts from a source document and produces all summaries."""

    def __init__(self, client: Optional[DrefSummaryLLMClient] = None):
        self.client = client or DrefSummaryLLMClient()

    @classmethod
    def _model_label(cls, source_doc) -> str:
        return f"{source_doc._meta.app_label}.{type(source_doc).__name__}"

    # Shared helpers — called by multiple extractors

    @staticmethod
    def _situational_overview_kwargs(source_doc) -> dict:
        """Build situational_overview kwargs — common across all document types.

        ``event_scope`` is omitted for Imminent DREFs since the scope is not
        yet known at that stage.
        """
        is_imminent = source_doc.type_of_dref == Dref.DrefType.IMMINENT
        kwargs = _extract_fields(source_doc, SITUATIONAL_COMMON_FIELDS)
        if source_doc.country:
            kwargs["country"] = {"name": source_doc.country.name, "iso": source_doc.country.iso}
        if source_doc.disaster_type:
            kwargs["disaster_type"] = {"name": source_doc.disaster_type.name}
        # event_scope is not yet known for Imminent DREFs, so it is excluded there.
        if not is_imminent:
            kwargs.update(_extract_fields(source_doc, ["event_scope"]))
        return kwargs

    @staticmethod
    def _challenges_and_lessons_kwargs(source_doc) -> Dict[str, dict]:
        """Collect challenges and lessons from ``planned_interventions`` M2M.

        Only called for ``DrefFinalReport``
        """

        def pi_title(pi):
            display = getattr(pi, "get_title_display", None)
            return display() if callable(display) else pi.title

        # Order explicitly: planned_interventions has no Meta.ordering, so an
        # unordered .all() can return rows in different orders across queries,
        # which would change the source hash and trigger needless regeneration.
        planned = list(source_doc.planned_interventions.order_by("id"))
        return {
            "challenges_identified": {
                "planned_interventions": [{"title": pi_title(pi), "challenges": pi.challenges} for pi in planned if pi.challenges]
                or None,
            },
            "lessons_learned": {
                "planned_interventions": [
                    {"title": pi_title(pi), "lessons_learnt": pi.lessons_learnt} for pi in planned if pi.lessons_learnt
                ]
                or None,
            },
        }

    @classmethod
    def _extract_dref_kwargs(cls, dref) -> Dict[str, dict]:
        """Dref Application / Assessment / Imminent — three sections only.

        Challenges and lessons are not applicable at the application stage;
        they are formally recorded only in the Final Report.
        """
        is_imminent = dref.type_of_dref == Dref.DrefType.IMMINENT
        operational = _extract_fields(dref, OPERATIONAL_COMMON_FIELDS + ["amount_requested", "end_date"])
        # Normalise to a single "operation_timeframe" key regardless of source field.
        timeframe = _field_val(dref, "operation_timeframe_imminent" if is_imminent else "operation_timeframe")
        if timeframe is not None:
            operational["operation_timeframe"] = timeframe
        return {
            "situational_overview": cls._situational_overview_kwargs(dref),
            "operational_strategy": operational,
            "people_centered_approach": _extract_fields(dref, PEOPLE_COMMON_FIELDS),
        }

    @classmethod
    def _extract_dref_ops_kwargs(cls, ops) -> Dict[str, dict]:
        """DrefOperationalUpdate — three sections; different field names from Dref.

        Includes demographic breakdown (women/men/girls/boys) in people_centered_approach.
        Challenges and lessons are not generated for Operational Updates.
        """
        operational = _extract_fields(ops, OPERATIONAL_COMMON_FIELDS + ["total_dref_allocation"])
        # Ops Update names these differently; normalise to the shared key names.
        operational.update(
            {
                k: v
                for k, v in {
                    "operation_end_date": _field_val(ops, "new_operational_end_date"),
                    "operation_timeframe": _field_val(ops, "total_operation_timeframe"),
                }.items()
                if v is not None
            }
        )
        return {
            "situational_overview": cls._situational_overview_kwargs(ops),
            "operational_strategy": operational,
            "people_centered_approach": _extract_fields(ops, PEOPLE_COMMON_FIELDS + DEMOGRAPHIC_FIELDS),
        }

    @classmethod
    def _extract_dref_final_kwargs(cls, final) -> Dict[str, dict]:
        """DrefFinalReport — all five sections.

        Challenges and lessons come from ``planned_interventions`` M2M via
        ``_challenges_and_lessons_kwargs``; this is the only document type
        where those two sections are generated.
        """
        is_imminent = final.type_of_dref == Dref.DrefType.IMMINENT
        operational = _extract_fields(final, OPERATIONAL_COMMON_FIELDS + ["total_dref_allocation", "operation_end_date"])
        # Normalise to a single "operation_timeframe" key regardless of source field.
        timeframe = _field_val(final, "total_operation_timeframe_imminent" if is_imminent else "total_operation_timeframe")
        if timeframe is not None:
            operational["operation_timeframe"] = timeframe
        kwargs = {
            "situational_overview": cls._situational_overview_kwargs(final),
            "operational_strategy": operational,
            "people_centered_approach": _extract_fields(final, PEOPLE_COMMON_FIELDS + DEMOGRAPHIC_FIELDS),
        }
        kwargs.update(cls._challenges_and_lessons_kwargs(final))
        return kwargs

    @classmethod
    def _get_section_kwargs(cls, source_doc) -> Dict[str, dict]:
        """Dispatch to the model-specific extractor."""
        if isinstance(source_doc, Dref):
            return cls._extract_dref_kwargs(source_doc)
        if isinstance(source_doc, DrefOperationalUpdate):
            return cls._extract_dref_ops_kwargs(source_doc)
        if isinstance(source_doc, DrefFinalReport):
            return cls._extract_dref_final_kwargs(source_doc)
        return {}

    @classmethod
    def build_source_text(cls, source_doc) -> str:
        """JSON representation of all section kwargs for inspection and debugging."""
        return json.dumps(cls._get_section_kwargs(source_doc), indent=2, ensure_ascii=False, default=str)

    @classmethod
    def compute_source_hash(cls, source_doc) -> str:
        """Hash of all source content feeding the summary, for change detection."""
        model_label = cls._model_label(source_doc)
        payload = {"model": model_label, "id": source_doc.id, "source": cls._get_section_kwargs(source_doc)}
        content = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _parse_response(response: str) -> Dict[str, str]:
        """Parse the model's JSON object, tolerating ```json code fences."""
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text
            text = text.rsplit("```", 1)[0]
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object of summary fields")
        return data

    def generate_all(self, source_doc) -> Dict[str, str]:
        """Generate every summary for ``source_doc`` in a single LLM call.

        Always returns a value for every ``SUMMARY_FIELDS`` key (empty string
        when a section has no content), so callers overwrite stale values
        instead of leaving them in place on regeneration.
        """
        empty_results: Dict[str, str] = {field_name: "" for field_name in SUMMARY_FIELDS}

        section_kwargs = self._get_section_kwargs(source_doc)
        if not section_kwargs:
            logger.info(f"No source content for ({type(source_doc).__name__}) ({source_doc.id}) summary; skipping generation.")
            return empty_results

        # Call each builder with only its section's kwargs, then join blocks.
        section_blocks = [SECTION_PROMPT_BUILDERS[section](**section_kwargs.get(section, {})) for section in SUMMARY_FIELDS]
        user_content = "\n\n".join(section_blocks) + "\n\n" + GLOBAL_PROMPT

        # Respect the token budget: trim the data blocks if the prompt is too long.
        if count_tokens(SYSTEM_MESSAGE + user_content) > MAX_INPUT_TOKENS:
            logger.warning(f"({type(source_doc).__name__}) ({source_doc.id}) summary prompt too long; truncating source text.")
            char_budget = MAX_INPUT_TOKENS * 4 - len(GLOBAL_PROMPT) - len(SYSTEM_MESSAGE)
            data_blocks = "\n\n".join(section_blocks)
            user_content = data_blocks[: max(char_budget, 0)] + "\n\n" + GLOBAL_PROMPT

        messages = [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": user_content},
        ]

        response = self.client.get_response(messages)
        if not response:
            raise RuntimeError(f"No LLM response for ({type(source_doc).__name__}) ({source_doc.id}) summary")

        try:
            parsed = self._parse_response(response)
        except (json.JSONDecodeError, ValueError) as e:
            raise RuntimeError(f"Could not parse ({type(source_doc).__name__}) ({source_doc.id}) summary response: {e}") from e

        results = dict(empty_results)
        for field_name in SUMMARY_FIELDS:
            value = parsed.get(field_name)
            if not isinstance(value, str):
                continue
            summary = value.strip()
            if len(summary) > MAX_OUTPUT_CHARS_PER_FIELD:
                summary = summary[:MAX_OUTPUT_CHARS_PER_FIELD].rstrip()
            results[field_name] = summary
        return results
