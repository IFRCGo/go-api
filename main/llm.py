import json
import logging
import re
from typing import Dict, List, Optional

from django.conf import settings
from django.utils.functional import cached_property
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

# A chat completion prompt: the ``[{"role": ..., "content": ...}, ...]`` list
# every real call site builds and passes in.
Message = Dict[str, str]
Messages = List[Message]


PLACEHOLDER_TEXT = (
    "This is placeholder text standing in for a real AI-generated summary. It is returned by "
    "the dummy LLM client Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt "
    "ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco "
    "laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in "
    "voluptate velit esse cillum dolore eu fugiat nulla pariatur."
)


class BaseLLMClient:
    def get_response(self, messages: Messages) -> Optional[str]:
        raise NotImplementedError

    @staticmethod
    def _last_user_message(messages: Messages) -> str:
        return next((message["content"] for message in reversed(messages) if message["role"] == "user"), "")

    def _fake_content(self) -> str:
        """Placeholder text every dummy response uses in place of real LLM output."""
        return f"DUMMY RESPONSE, {PLACEHOLDER_TEXT}"


class AzureOpenAiChat(BaseLLMClient):
    """The real Azure OpenAI-backed client, shared by every feature."""

    def __init__(self, temperature: float = 0.5):
        self.temperature = temperature

        if settings.TESTING:
            # Tests never hit Azure, so a missing/placeholder config shouldn't fail construction.
            return

        if not settings.AZURE_OPENAI_ENDPOINT or not settings.AZURE_OPENAI_KEY or not settings.AZURE_OPENAI_DEPLOYMENT_NAME:
            raise Exception("Azure OpenAI configuration missing")

    @cached_property
    def client(self):
        return AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_KEY,
            api_version="2023-05-15",
        )

    def get_response(self, messages: Messages) -> Optional[str]:
        if settings.USE_DUMMY_LLM_CLIENT or settings.TESTING:
            logger.info(f"{type(self).__name__}: dummy mode is on; returning a fake response instead of calling Azure OpenAI.")
            return self._fake_content()

        try:
            response = self.client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages,
                temperature=self.temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error while generating LLM response: {e}", exc_info=True)
            return None


class BaseDummyLLMClient(BaseLLMClient):
    """Summaries generated for local development/testing, without hitting Azure OpenAI. Each subclass implements
    ``_fake_response()`` to return a JSON object with the expected fields for that feature
    """

    def get_response(self, messages: Messages) -> Optional[str]:
        return self._fake_response(messages)

    def _fake_response(self, messages: Messages) -> str:
        raise NotImplementedError


class DummyDrefSummaryLLMClient(BaseDummyLLMClient):
    """Fake response for DREF summary generation: a JSON object with all of
    DREF's summary fields, each set to the same fake content, so
    ``dref.summary.DrefSummaryGenerator`` parses/saves it unchanged.
    """

    def _fake_response(self, messages: Messages) -> str:
        from dref.summary import SUMMARY_FIELDS

        logger.info("DummyDrefSummaryLLMClient: generating fake response for DREF summary fields")
        fake_content = self._fake_content()
        payload: Dict[str, str] = {field_name: fake_content for field_name in SUMMARY_FIELDS}
        return json.dumps(payload)


class DummyOpsLearningLLMClient(BaseDummyLLMClient):
    """Fake response for PER Ops Learning summaries."""

    _EXCERPT_ID_RE = re.compile(r"^(\d+)\. In ", re.MULTILINE)

    def _prompt_excerpt_ids(self, user_content: str) -> List[int]:
        return [int(excerpt_id) for excerpt_id in self._EXCERPT_ID_RE.findall(user_content)]

    def _fake_response(self, messages: Messages) -> str:
        from per.models import OpsLearning
        from per.ops_learning_summary import OpsLearningSummaryTask

        logger.info("DummyOpsLearningLLMClient: generating fake response for Ops Learning summary")
        user_content = self._last_user_message(messages)
        fake_content = self._fake_content()
        excerpt_ids = self._prompt_excerpt_ids(user_content)
        logger.info(f"DummyOpsLearningLLMClient: found {len(excerpt_ids)} excerpt id(s) in the prompt")

        all_excerpts_id = ", ".join(str(excerpt_id) for excerpt_id in excerpt_ids)

        payload: Dict[str, Dict[str, str]]
        if OpsLearningSummaryTask.component_prompt in user_content:
            logger.info("DummyOpsLearningLLMClient: detected the component prompt shape.")
            excerpts = list(
                OpsLearning.objects.filter(id__in=excerpt_ids, is_validated=True, per_component_validated__isnull=False)
                .prefetch_related("per_component_validated")
                .distinct()
            )
            component = excerpts[0].per_component_validated.first() if excerpts else None
            subtype = component.title if component else "Logistics"
            excerpts_id = ", ".join(str(excerpt.id) for excerpt in excerpts) or all_excerpts_id
            logger.info(
                f"DummyOpsLearningLLMClient: {len(excerpts)} excerpt(s) matched a validated component; "
                f"using subtype '{subtype}'."
            )
            payload = {"0": {"type": "component", "subtype": subtype, "excerpts id": excerpts_id, "content": fake_content}}

        elif OpsLearningSummaryTask.sector_prompt in user_content:
            logger.info("DummyOpsLearningLLMClient: detected the sector prompt shape.")
            excerpts = list(
                OpsLearning.objects.filter(id__in=excerpt_ids, is_validated=True, sector_validated__isnull=False)
                .prefetch_related("sector_validated")
                .distinct()
            )
            sector = excerpts[0].sector_validated.first() if excerpts else None
            subtype = sector.title if sector else "Shelter"
            excerpts_id = ", ".join(str(excerpt.id) for excerpt in excerpts) or all_excerpts_id
            logger.info(
                f"DummyOpsLearningLLMClient: {len(excerpts)} excerpt(s) matched a validated sector; "
                f"using subtype '{subtype}'."
            )
            payload = {"0": {"type": "sector", "subtype": subtype, "excerpts id": excerpts_id, "content": fake_content}}
        else:
            logger.info(
                f"DummyOpsLearningLLMClient: detected the primary prompt shape; "
                f"returning 3 fake findings with excerpts id(s) [{all_excerpts_id}]."
            )
            payload = {
                str(i): {
                    "title": f"Dummy Finding {i + 1}",
                    "excerpts id": all_excerpts_id,
                    "content": fake_content,
                    "confidence level": "1/5",
                }
                for i in range(3)
            }
        return json.dumps(payload)


def get_dref_summary_llm_client() -> BaseLLMClient:
    if settings.USE_DUMMY_LLM_CLIENT or settings.TESTING:
        return DummyDrefSummaryLLMClient()
    return AzureOpenAiChat(temperature=0.5)


def get_ops_learning_llm_client() -> BaseLLMClient:
    if settings.USE_DUMMY_LLM_CLIENT or settings.TESTING:
        return DummyOpsLearningLLMClient()
    return AzureOpenAiChat(temperature=0.7)
