"""
DREF AI summary generation.
"""

import hashlib
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

import tiktoken
from django.db.models import F

from api.utils import get_model_name
from dref.models import Dref, DrefFinalReport, DrefOperationalUpdate, DrefSummary
from main.llm import get_dref_summary_llm_client

logger = logging.getLogger(__name__)

ENCODING_NAME = "cl100k_base"

# Per-section budget: each section is its own LLM call.
MAX_INPUT_TOKENS = 10000

TARGET_SOURCE_RATIO = 0.4

# Attempts per section before it is recorded as failed, and the pause between them.
SECTION_MAX_ATTEMPTS = 2
RETRY_BACKOFF_SECONDS = 3

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
    "operations. Analyze the provided DREF data and produce clear, professional humanitarian "
    "summaries suitable for IFRC staff and National Society personnel. Use only the information "
    "provided in the data; do not invent facts, figures, or details."
)

# Section prompts

# What each section covers, used both to label its data and to instruct the model.
SECTION_DESCRIPTIONS: Dict[str, str] = {
    "situational_overview": "the disaster situation and the rationale for the operation",
    "operational_strategy": "the overall objective and strategic approach of the response",
    "people_centered_approach": "who is targeted and how they are selected",
    "challenges_identified": "the challenges recorded per planned intervention",
    "lessons_learned": "the lessons learned recorded per planned intervention",
}


def _section_data(kwargs: dict) -> dict:
    return {k: v for k, v in kwargs.items() if v not in (None, "", [], {})}


def _section_data_json(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)


def _word_count(value) -> int:
    """Words in the source text of a section's data, ignoring its keys and JSON punctuation."""
    if isinstance(value, dict):
        return sum(_word_count(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return sum(_word_count(v) for v in value)
    if value is None:
        return 0
    return len(str(value).split())


def target_word_count(source_words: int) -> Optional[int]:
    """Word target for a section with ``source_words`` of source, or ``None`` to leave length to the model."""
    target = round(source_words * TARGET_SOURCE_RATIO)
    return target or None


def build_section_prompt(section: str, data: dict, target_words: Optional[int]) -> str:
    requirements = [
        "Summarise only what the data contains; do not add topics, interpretation or details it does not mention.",
        "Keep the most important figures, locations and timeframes exactly as written and never fabricate them; "
        "leave out secondary details when needed to stay within the length limit.",
        "Write plain text in professional humanitarian language: no markdown, headings or bullet lists. "
        "Separate paragraphs with a blank line.",
        "Never write more than the source data contains; if the data is brief, keep the section brief.",
    ]
    if target_words:
        requirements.append(f"Write approximately {target_words} words.")
    requirements.append("Return only the section text, with no title, preamble or closing remarks.")
    return (
        f'Data for "{section}" — {SECTION_DESCRIPTIONS[section]}:\n'
        f"{_section_data_json(data)}\n\n"
        f'Using ONLY the data above, write the "{section}" section of a DREF summary, covering '
        f"{SECTION_DESCRIPTIONS[section]}.\n\n"
        "Requirements:\n" + "\n".join(f"- {r}" for r in requirements)
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


SectionStatus = DrefSummary.SectionStatus


@dataclass
class SummaryGenerationResult:
    """Outcome of generating every section of a summary.

    ``values`` and ``section_status`` hold an entry for every section in
    ``SUMMARY_FIELDS``; a skipped or failed section has an empty value.
    """

    values: Dict[str, str] = field(default_factory=dict)
    section_status: Dict[str, int] = field(default_factory=dict)

    @property
    def failed_sections(self) -> List[str]:
        return [section for section, status in self.section_status.items() if status == SectionStatus.FAILED]


class SectionGenerationError(Exception):
    pass


class DrefSummaryGenerator:
    """Assembles per-section prompts from a source document and produces the summaries, one LLM call per section."""

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
        planned = sorted(source_doc.planned_interventions.all(), key=lambda pi: pi.id)
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
            DrefFinalReport.objects.prefetch_related("planned_interventions")
            .filter(dref=dref, status=Dref.Status.APPROVED)
            .order_by("-created_at")
            .first()
        )
        if final_report:
            return SOURCE_BY_MODEL[DrefFinalReport], final_report

        latest_ops_update = (
            DrefOperationalUpdate.objects.filter(dref=dref, status=Dref.Status.APPROVED)
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

    def _generate_section(self, source_doc: DrefSummarySource, section: str, data: dict) -> str:
        """Generate one section, retrying up to ``SECTION_MAX_ATTEMPTS``; raises ``SectionGenerationError`` if none succeeds."""
        prompt = build_section_prompt(section, data, target_word_count(_word_count(data)))
        if count_tokens(SYSTEM_MESSAGE + prompt) > MAX_INPUT_TOKENS:
            logger.warning(f"({type(source_doc).__name__}) ({source_doc.id}) {section} prompt too long; truncating source text.")
            prompt = prompt[: MAX_INPUT_TOKENS * 4 - len(SYSTEM_MESSAGE)]
        messages = [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": prompt},
        ]

        for attempt in range(1, SECTION_MAX_ATTEMPTS + 1):
            if attempt > 1:
                time.sleep(RETRY_BACKOFF_SECONDS * (attempt - 1))
            # The client logs and swallows API errors, returning None, so an empty
            # response is the one failure signal for a section.
            response = (self.client.get_response(messages) or "").strip()
            if response:
                return response
            logger.warning(
                f"({type(source_doc).__name__}) ({source_doc.id}) {section} summary attempt "
                f"{attempt}/{SECTION_MAX_ATTEMPTS} got no LLM response"
            )
        raise SectionGenerationError("no LLM response")

    def generate_all(
        self,
        source_doc: DrefSummarySource,
        section_kwargs: Optional[Dict[str, dict]] = None,
    ) -> SummaryGenerationResult:
        """Generate every summary section for ``source_doc``.

        Each section with source content gets its own LLM call, run concurrently.
        A section without source content is SKIPPED and makes no call; one with
        content whose call does not produce usable text is FAILED. Neither
        raises: the caller decides what a failed section means for the summary.
        """
        if section_kwargs is None:
            section_kwargs = self.get_section_kwargs(source_doc)

        result = SummaryGenerationResult()
        to_generate: List[Tuple[str, dict]] = []
        for section in SUMMARY_FIELDS:
            data = _section_data(section_kwargs.get(section, {}))
            if data:
                to_generate.append((section, data))
            else:
                result.values[section] = ""
                result.section_status[section] = SectionStatus.SKIPPED

        if not to_generate:
            return result

        # Only the LLM call runs in the workers: section data is extracted above, so
        # no thread touches the database.
        with ThreadPoolExecutor(max_workers=len(to_generate)) as executor:
            futures = {
                section: executor.submit(self._generate_section, source_doc, section, data) for section, data in to_generate
            }
            for section, future in futures.items():
                try:
                    result.values[section] = future.result()
                    result.section_status[section] = SectionStatus.SUCCESS
                except Exception:
                    logger.warning(
                        f"({type(source_doc).__name__}) ({source_doc.id}) {section} summary failed",
                        exc_info=True,
                    )
                    result.values[section] = ""
                    result.section_status[section] = SectionStatus.FAILED
        return result
