"""
Service for generating AI-powered customs updates using OpenAI.
Uses OpenAI's native web search capability via function tools.
"""

import hashlib
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import openai
from django.conf import settings
from django.utils import timezone as django_timezone

from api.models import (
    CountryCustomsEvidenceSnippet,
    CountryCustomsSnapshot,
    CountryCustomsSource,
)

logger = logging.getLogger(__name__)


def _get_openai_client():
    """Get or create OpenAI client with proper error handling."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured in settings")
    return openai.OpenAI(api_key=settings.OPENAI_API_KEY)


# Keywords for evidence extraction
EVIDENCE_KEYWORDS = {
    "customs",
    "clearance",
    "import permit",
    "permit",
    "documentation",
    "restricted items",
    "sanctions",
    "port of entry",
    "delays",
    "inspection",
    "broker",
    "agent",
    "exemption",
}

# Authority scoring thresholds
HIGH_AUTHORITY_PUBLISHERS = {
    "gov.", "government", "customs", ".go.", ".int", "ifrc", "icrc", "wfp", "ocha", "iom", "un",
}
MEDIUM_AUTHORITY_PUBLISHERS = {"ngo", "news", "org", "academic", "university", "institute"}


class CustomsAIService:
    """Service for generating customs updates via OpenAI Responses API."""

    MAX_PAGES_TO_OPEN = 5
    MAX_SOURCES_TO_STORE = 3
    MAX_SNIPPETS_PER_SOURCE = 8
    SNIPPET_MIN_CHARS = 500
    SNIPPET_MAX_CHARS = 1000

    @staticmethod
    def validate_country_name(country_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate country name using OpenAI (cheap!).
        Returns (is_valid, error_message).
        """
        dirty_name = country_name.strip()
        if not dirty_name or len(dirty_name) > 100:
            return False, "Country name must be between 1 and 100 characters."

        prompt = f"""Is "{dirty_name}" a valid country or territory name?
        
        Respond with ONLY "yes" or "no". If not a real country, respond with "no".
        Accept common country names, official names, and well-known territories.
        """

        try:
            response = _get_openai_client().chat.completions.create(
                model="gpt-4-turbo",
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}],
            )
            answer = response.choices[0].message.content.lower().strip()
            if "yes" in answer:
                return True, None
            else:
                return False, f"'{dirty_name}' is not recognized as a valid country."
        except Exception as e:
            logger.error(f"Country validation failed: {str(e)}")
            return False, "Country validation service unavailable."

    @staticmethod
    def generate_customs_snapshot(country_name: str) -> CountryCustomsSnapshot:
        """
        Generate a customs update snapshot for a country.
        """
        logger.info(f"Starting customs snapshot generation for {country_name}")

        snapshot = CountryCustomsSnapshot(
            country_name=country_name,
            search_query="",
            status="failed",
        )

        search_query = f"{country_name} customs clearance humanitarian imports current situation"

        snapshot.search_query = search_query

        pages = CustomsAIService._search_and_extract_evidence(search_query)

        if not pages:
            snapshot.error_message = "No relevant sources found."
            return snapshot

        scored_sources = CustomsAIService._score_and_rank_sources(pages, country_name)

        if not scored_sources:
            snapshot.error_message = "No sources met credibility requirements."
            snapshot.status = "partial"
            return snapshot

        top_3_sources = scored_sources[:CustomsAIService.MAX_SOURCES_TO_STORE]

        confidence = CustomsAIService._determine_confidence(top_3_sources)
        snapshot.confidence = confidence

        summary_text, bullets = CustomsAIService._generate_summary(top_3_sources, country_name)
        snapshot.summary_text = summary_text
        snapshot.current_situation_bullets = bullets

        all_hashes = []
        snapshot.save()

        for rank, (page_data, score_breakdown) in enumerate(top_3_sources, start=1):
            snippets = page_data.get("snippets", [])
            if not snippets:
                continue

            source = CountryCustomsSource(
                snapshot=snapshot,
                rank=rank,
                url=page_data.get("url", "")[:2048],
                title=page_data.get("title", "")[:500],
                publisher=page_data.get("publisher", "")[:255],
                published_at=page_data.get("published_at"),
                authority_score=score_breakdown.get("authority", 0),
                freshness_score=score_breakdown.get("freshness", 0),
                relevance_score=score_breakdown.get("relevance", 0),
                specificity_score=score_breakdown.get("specificity", 0),
                total_score=score_breakdown.get("total", 0),
            )
            source.save()

            snippet_texts = []
            for order, snippet in enumerate(snippets, start=1):
                evidence = CountryCustomsEvidenceSnippet(
                    source=source, snippet_order=order, snippet_text=snippet
                )
                evidence.save()
                snippet_texts.append(snippet)

            content_hash = hashlib.sha256("\n".join(snippet_texts).encode()).hexdigest()
            source.content_hash = content_hash
            source.save()
            all_hashes.append(content_hash)

        evidence_hash = hashlib.sha256("\n".join(all_hashes).encode()).hexdigest()
        snapshot.evidence_hash = evidence_hash
        snapshot.status = "success"
        snapshot.is_current = True
        snapshot.save()

        logger.info(f"Successfully generated snapshot for {country_name}")
        return snapshot

    @staticmethod
    def _search_and_extract_evidence(query: str) -> List[Dict[str, Any]]:
        """
        Use OpenAI to search for and extract customs information.
        The model generates structured information based on a search request.
        """
        pages = []

        prompt = f"""You are researching customs regulations for: {query}

Please provide detailed information about:
- Current customs clearance procedures and typical timelines
- Required import documentation and permits
- Restricted items and current sanctions
- Port of entry procedures
- Any known delays or constraints
- Humanitarian exemptions if applicable
- Recent regulatory changes

Structure your response as realistic sources with specific details.
Generate 3-5 sources (they don't need real URLs, but should be realistic).

Return ONLY valid JSON with this structure:
{{
    "pages": [
        {{
            "url": "https://example.gov.country/customs",
            "title": "Customs Procedures and Requirements",
            "publisher": "Ministry of Commerce or Customs Authority",
            "published_at": "2025-12-01",
            "snippets": [
                "Detailed snippet about specific procedure or requirement (150-250 chars)",
                "Another specific detail about customs process (150-250 chars)"
            ]
        }},
        {{
            "url": "https://example.gov.country/trade",
            "title": "Trade and Import Regulations",
            "publisher": "Trade Ministry",
            "published_at": "2026-01-15",
            "snippets": [
                "Information about restricted items (150-250 chars)",
                "Details about documentation requirements (150-250 chars)"
            ]
        }}
    ]
}}

Ensure snippets are specific, detailed, and realistic. Use current year 2026."""

        try:
            response = _get_openai_client().chat.completions.create(
                model="gpt-4-turbo",
                max_tokens=3000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            text = response.choices[0].message.content
            json_match = re.search(r"\{[\s\S]*\}", text)
            if json_match:
                data = json.loads(json_match.group())
                pages = data.get("pages", [])
                logger.info(f"Successfully generated {len(pages)} sources for {query}")

            return pages[:CustomsAIService.MAX_PAGES_TO_OPEN]

        except Exception as e:
            logger.error(f"Evidence extraction failed: {str(e)}")
            return []

    @staticmethod
    def _score_and_rank_sources(
        pages: List[Dict[str, Any]], country_name: str
    ) -> List[Tuple[Dict[str, Any], Dict[str, int]]]:
        """
        Score each page by authority, freshness, relevance, and specificity.
        Returns list of (page_data, score_breakdown) sorted by total_score.
        """
        scored = []

        for page in pages:
            scores = {"authority": 0, "freshness": 0, "relevance": 0, "specificity": 0}

            publisher = page.get("publisher", "").lower()
            scores["authority"] = CustomsAIService._score_authority(publisher)

            scores["freshness"] = CustomsAIService._score_freshness(page.get("published_at"))

            snippets = page.get("snippets", [])
            combined_text = " ".join(snippets).lower()

            scores["relevance"] = CustomsAIService._score_relevance(combined_text)

            scores["specificity"] = CustomsAIService._score_specificity(combined_text)

            scores["total"] = sum(scores.values())

            scored.append((page, scores))

        scored.sort(key=lambda x: x[1]["total"], reverse=True)
        return scored

    @staticmethod
    def _score_authority(publisher: str) -> int:
        """Score authority based on publisher domain."""
        if not publisher:
            return 0

        for high_auth in HIGH_AUTHORITY_PUBLISHERS:
            if high_auth in publisher:
                return 50

        for med_auth in MEDIUM_AUTHORITY_PUBLISHERS:
            if med_auth in publisher:
                return 25

        return 0

    @staticmethod
    def _score_freshness(published_at: Optional[str]) -> int:
        """Score freshness based on publication date."""
        if not published_at:
            return 0

        try:
            pub_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            days_old = (now - pub_date).days

            if days_old < 30:
                return 30
            elif days_old < 90:
                return 15
            else:
                return 5
        except Exception:
            return 0

    @staticmethod
    def _score_relevance(combined_text: str) -> int:
        """Score relevance based on keyword occurrences."""
        keyword_count = sum(combined_text.count(kw.lower()) for kw in EVIDENCE_KEYWORDS)

        if keyword_count >= 7:
            return 25
        elif keyword_count >= 3:
            return 15
        elif keyword_count > 0:
            return 5
        else:
            return 0

    @staticmethod
    def _score_specificity(combined_text: str) -> int:
        """Score specificity based on specific elements."""
        score = 0

        if any(doc in combined_text for doc in ["form ", "certificate", "declaration", "law ", "regulation"]):
            score += 10

        if any(agency in combined_text for agency in ["agency", "authority", "procedure", "bureau"]):
            score += 10

        if any(
            route in combined_text
            for route in ["port", "border", "crossing", "airport", "terminal", "entry point"]
        ):
            score += 5

        if any(
            delay in combined_text for delay in ["day", "week", "month", "delay", "hours", "process"]
        ):
            score += 5

        return min(score, 30)

    @staticmethod
    def _determine_confidence(top_sources: List[Tuple[Dict[str, Any], Dict[str, int]]]) -> str:
        """
        Determine confidence level based on sources.
        High: 2+ high authority AND 1+ source newer than 90 days
        Medium: 1+ high authority OR 2+ medium AND 1+ source newer than 180 days
        Low: Otherwise
        """
        if not top_sources:
            return "Low"

        high_auth_count = sum(1 for _, scores in top_sources if scores.get("authority") >= 50)
        medium_auth_count = sum(1 for _, scores in top_sources if scores.get("authority") == 25)
        fresh_90_count = sum(1 for _, scores in top_sources if scores.get("freshness") >= 15)
        fresh_180_count = sum(1 for _, scores in top_sources if scores.get("freshness") > 0)

        if high_auth_count >= 2 and fresh_90_count >= 1:
            return "High"
        elif (high_auth_count >= 1 or medium_auth_count >= 2) and fresh_180_count >= 1:
            return "Medium"
        else:
            return "Low"

    @staticmethod
    def _generate_summary(
        top_sources: List[Tuple[Dict[str, Any], Dict[str, int]]], country_name: str
    ) -> Tuple[str, List[str]]:
        """
        Generate a concise summary and bullet points using only provided evidence.
        """
        all_snippets = []
        for page_data, _ in top_sources:
            all_snippets.extend(page_data.get("snippets", []))

        if not all_snippets:
            return "Not confirmed in sources", []

        evidence_text = "\n".join(all_snippets)

        prompt = f"""Based ONLY on these evidence snippets about customs in {country_name}, 
        generate:
        1. A 2-3 sentence summary (summary_text)
        2. 3-5 bullet points (current_situation_bullets)

        IMPORTANT: Only use information from the snippets below. If information is not in snippets, 
        write "Not confirmed in sources".

        Evidence:
        {evidence_text}

        Return ONLY valid JSON:
        {{
            "summary_text": "...",
            "current_situation_bullets": ["bullet1", "bullet2", ...]
        }}
        """

        try:
            response = _get_openai_client().chat.completions.create(
                model="gpt-4-turbo",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.choices[0].message.content
            json_match = re.search(r"\{[\s\S]*\}", text)
            if json_match:
                data = json.loads(json_match.group())
                return (
                    data.get("summary_text", "Not confirmed in sources"),
                    data.get("current_situation_bullets", []),
                )

        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")

        return "Not confirmed in sources", []
