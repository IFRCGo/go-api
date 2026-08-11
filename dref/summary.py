"""
DREF AI summary generation.
"""

import hashlib
import json
import logging
from typing import Callable, Dict, List, Optional, Union

import tiktoken
from django.db.models import F

from api.utils import get_model_name
from dref.models import Dref, DrefFinalReport, DrefOperationalUpdate, DrefSummary
from main.llm import get_dref_summary_llm_client

logger = logging.getLogger(__name__)

ENCODING_NAME = "cl100k_base"

MAX_INPUT_TOKENS = 10000

# The models a DrefSummary can be generated from.
DrefSummarySource = Union[Dref, DrefOperationalUpdate, DrefFinalReport]

SOURCE_BY_MODEL: Dict[type, DrefSummary.SourceModel] = {
    Dref: DrefSummary.SourceModel.DREF,
    DrefOperationalUpdate: DrefSummary.SourceModel.DREF_OPERATIONAL_UPDATE,
    DrefFinalReport: DrefSummary.SourceModel.DREF_FINAL_REPORT,
}

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
    "operations. You write short executive summaries for IFRC staff and National Society personnel "
    "who will read the full document separately, so your task is to condense and synthesise, never "
    "to restate the source. Use only the information "
    "provided in the data; do not invent facts, figures, or details. Where supporting information "
    "for a section is absent, return an empty string for that section rather than speculating."
)

# Section prompt builders


def _section_data_json(kwargs: dict) -> str:
    data = {k: v for k, v in kwargs.items() if v not in (None, "", [], {})}
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)


def _build_situational_overview_prompt(**kwargs) -> str:
    data_json = _section_data_json(kwargs)
    return f'Data for "situational_overview" — the disaster situation and rationale for the operation:\n{data_json}'


def _build_operational_strategy_prompt(**kwargs) -> str:
    data_json = _section_data_json(kwargs)
    return f'Data for "operational_strategy" — the objective and strategy of the response:\n{data_json}'


def _build_people_centered_approach_prompt(**kwargs) -> str:
    data_json = _section_data_json(kwargs)
    return f'Data for "people_centered_approach" — the targeting, selection and engagement of affected people:\n{data_json}'


def _build_challenges_identified_prompt(**kwargs) -> str:
    data_json = _section_data_json(kwargs)
    return f'Data for "challenges_identified" — challenges recorded per planned intervention:\n{data_json}'


def _build_lessons_learned_prompt(**kwargs) -> str:
    data_json = _section_data_json(kwargs)
    return f'Data for "lessons_learned" — lessons recorded per planned intervention:\n{data_json}'


# Registry
SECTION_PROMPT_BUILDERS: Dict[str, Callable[..., str]] = {
    "situational_overview": _build_situational_overview_prompt,
    "operational_strategy": _build_operational_strategy_prompt,
    "people_centered_approach": _build_people_centered_approach_prompt,
    "challenges_identified": _build_challenges_identified_prompt,
    "lessons_learned": _build_lessons_learned_prompt,
}

GLOBAL_PROMPT = (
    "The DREF data above is organised by summary section. Using ONLY that data, write five "
    "condensed summary sections. Return a single JSON object (and nothing else) with exactly these "
    "keys, each summarising the block of the same name:\n"
    "\n"
    '  "situational_overview": The disaster situation and the rationale for the operation. Use the '
    'data under the "situational_overview" key.\n'
    '  "operational_strategy": The overall objective and strategic approach of the response. Use the '
    'data under the "operational_strategy" key.\n'
    '  "people_centered_approach": Who is targeted and how they are selected and engaged. Use the '
    'data under the "people_centered_approach" key.\n'
    '  "challenges_identified": The challenges recorded per planned intervention. Use the data under '
    'the "challenges_identified" key.\n'
    '  "lessons_learned": The lessons learned recorded per planned intervention. Use the data under '
    'the "lessons_learned" key.\n'
    "\n"
    "Requirements:\n"
    "- Summarise only what each section's data actually contains; do not add topics or details it "
    "does not mention.\n"
    "- Synthesise, do not concatenate: group related points into a coherent narrative instead of "
    "restating the source line by line or field by field. Merge repeated or overlapping points into "
    "a single statement.\n"
    "- Each section is at most three paragraphs, whatever the length of its source data. A thin "
    "source should yield a single paragraph; a rich one may use the full three, but no source "
    "justifies more.\n"
    "- Open each section with its single most important point, then add supporting context.\n"
    "- Preserve important facts and figures exactly as given; never invent or alter them.\n"
    "- If a section's data block is empty or holds no usable content, set that key to an empty "
    "string. Never write a sentence stating that data is missing, not provided or not recorded.\n"
    "- Each value must be plain text (no markdown, no bullet lists, no nested JSON): one to three "
    "well-structured paragraphs in professional humanitarian language, separated by a blank line, "
    "or an empty string when that section has no data.\n"
    "- Return ONLY the JSON object, with no surrounding prose or code fences."
)


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


SITUATIONAL_COMMON_FIELDS: List[str] = ["event_description", "event_scope"]

# Imminent DREF applications created on the v2 use hazard_date_and_location.
IMMINENT_SITUATIONAL_FIELDS: List[str] = ["hazard_date_and_location"]

OPERATIONAL_COMMON_FIELDS: List[str] = ["operation_objective", "response_strategy"]

PEOPLE_COMMON_FIELDS: List[str] = ["people_assisted", "selection_criteria"]


class DrefSummaryGenerator:
    """Assembles per-section prompts from a source document and produces all summaries."""

    def __init__(self):
        self.client = get_dref_summary_llm_client()

    @staticmethod
    def _situational_overview_kwargs(source_doc) -> dict:
        """Imminent v2 applications describe the situation in the scenario analysis fields; others use the common ones."""
        if isinstance(source_doc, Dref) and source_doc.type_of_dref == Dref.DrefType.IMMINENT and source_doc.is_dref_imminent_v2:
            return _extract_fields(source_doc, IMMINENT_SITUATIONAL_FIELDS)
        return _extract_fields(source_doc, SITUATIONAL_COMMON_FIELDS)  # event_scope is empty for Assessment; dropped

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
        return {
            "situational_overview": cls._situational_overview_kwargs(dref),
            "operational_strategy": _extract_fields(dref, OPERATIONAL_COMMON_FIELDS),
            "people_centered_approach": _extract_fields(dref, PEOPLE_COMMON_FIELDS),
        }

    @classmethod
    def _extract_dref_ops_kwargs(cls, ops) -> Dict[str, dict]:
        """DrefOperationalUpdate — three sections.

        Challenges and lessons are not generated for Operational Updates.
        """
        return {
            "situational_overview": cls._situational_overview_kwargs(ops),
            "operational_strategy": _extract_fields(ops, OPERATIONAL_COMMON_FIELDS),
            "people_centered_approach": _extract_fields(ops, PEOPLE_COMMON_FIELDS),
        }

    @classmethod
    def _extract_dref_final_kwargs(cls, final) -> Dict[str, dict]:
        """DrefFinalReport — all five sections.

        Challenges and lessons come from ``planned_interventions`` M2M via
        ``_challenges_and_lessons_kwargs``; this is the only document type
        where those two sections are generated.
        """
        kwargs = {
            "situational_overview": cls._situational_overview_kwargs(final),
            "operational_strategy": _extract_fields(final, OPERATIONAL_COMMON_FIELDS),
            "people_centered_approach": _extract_fields(final, PEOPLE_COMMON_FIELDS),
        }
        kwargs.update(cls._challenges_and_lessons_kwargs(final))
        return kwargs

    @classmethod
    def get_section_kwargs(cls, source_doc: DrefSummarySource) -> Dict[str, dict]:
        """Dispatch to the model-specific extractor.

        Public so callers that need both the hash and the generated summary
        for the same ``source_doc`` (see ``compute_source_hash``/``generate_all``)
        can compute this once and pass it to both instead of extracting twice.
        """
        if isinstance(source_doc, Dref):
            return cls._extract_dref_kwargs(source_doc)
        if isinstance(source_doc, DrefOperationalUpdate):
            return cls._extract_dref_ops_kwargs(source_doc)
        if isinstance(source_doc, DrefFinalReport):
            return cls._extract_dref_final_kwargs(source_doc)
        return {}

    @staticmethod
    def get_latest_approved_source(dref: Dref) -> Optional[tuple[DrefSummary.SourceModel, DrefSummarySource]]:
        """Most authoritative (source, source object) pair for ``dref``.

        Priority: Final Report > latest Operational Update > Dref itself.
        """
        final_report = (
            DrefFinalReport.objects.select_related("country", "disaster_type")
            .filter(dref=dref, status=Dref.Status.APPROVED)
            .order_by("-created_at")
            .first()
        )
        if final_report:
            return SOURCE_BY_MODEL[DrefFinalReport], final_report

        latest_ops_update = (
            DrefOperationalUpdate.objects.select_related("country", "disaster_type")
            .filter(dref=dref, status=Dref.Status.APPROVED)
            .order_by(F("operational_update_number").desc(nulls_last=True), "-created_at")
            .first()
        )
        if latest_ops_update:
            return SOURCE_BY_MODEL[DrefOperationalUpdate], latest_ops_update

        if dref.status == Dref.Status.APPROVED:
            return SOURCE_BY_MODEL[Dref], dref

        return None

    @classmethod
    def build_source_text(cls, source_doc: DrefSummarySource) -> str:
        """JSON representation of all section kwargs for inspection and debugging."""
        return json.dumps(cls.get_section_kwargs(source_doc), indent=2, ensure_ascii=False, default=str)

    @classmethod
    def compute_source_hash(cls, source_doc: DrefSummarySource, section_kwargs: Optional[Dict[str, dict]] = None) -> str:
        """Hash of all source content feeding the summary, for change detection."""
        model_label = get_model_name(type(source_doc))
        if section_kwargs is None:
            section_kwargs = cls.get_section_kwargs(source_doc)
        payload = {"model": model_label, "id": source_doc.id, "source": section_kwargs}
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

    def generate_all(self, source_doc: DrefSummarySource, section_kwargs: Optional[Dict[str, dict]] = None) -> Dict[str, str]:
        """Generate every summary for ``source_doc`` in a single LLM call.

        Always returns a value for every ``SUMMARY_FIELDS`` key (empty string
        when a section has no content), so callers overwrite stale values
        instead of leaving them in place on regeneration. ``section_kwargs``
        can be passed in by a caller that already computed it (e.g. via
        ``compute_source_hash``) to avoid re-extracting it from ``source_doc``.
        """
        empty_results: Dict[str, str] = {field_name: "" for field_name in SUMMARY_FIELDS}

        if section_kwargs is None:
            section_kwargs = self.get_section_kwargs(source_doc)
        if not section_kwargs:
            logger.info(f"No source content for ({type(source_doc).__name__}) ({source_doc.id}) summary; skipping generation.")
            return empty_results

        section_blocks = [SECTION_PROMPT_BUILDERS[section](**section_kwargs.get(section, {})) for section in SUMMARY_FIELDS]
        user_content = "\n\n".join(section_blocks) + "\n\n" + GLOBAL_PROMPT

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
            results[field_name] = value.strip()
        return results
