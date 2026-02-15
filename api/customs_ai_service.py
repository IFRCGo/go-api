"""
Service for generating AI-powered customs updates using OpenAI.
Uses OpenAI's native web search capability via function tools.
"""

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import openai
from django.conf import settings

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
    "gov.",
    "government",
    "customs",
    ".go.",
    ".int",
    "ifrc",
    "icrc",
    "wfp",
    "ocha",
    "iom",
    "un",
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

        current_year = datetime.now().year
        query = f"{country_name} customs clearance humanitarian imports current situation {current_year}"

        snapshot.search_query = query

        pages = CustomsAIService._search_and_extract_evidence(query)

        if not pages:
            snapshot.error_message = "No relevant sources found."
            return snapshot

        scored_sources = CustomsAIService._score_and_rank_sources(pages, country_name)

        if not scored_sources:
            snapshot.error_message = "No sources met credibility requirements."
            snapshot.status = "partial"
            return snapshot

        top_3_sources = scored_sources[: CustomsAIService.MAX_SOURCES_TO_STORE]

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
                evidence = CountryCustomsEvidenceSnippet(source=source, snippet_order=order, snippet_text=snippet)
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
        Use DuckDuckGo to search for customs information and OpenAI to structure it.
        """
        pages = []

        # 1. Perform Web Search
        try:
            from ddgs import DDGS

            with DDGS() as ddgs:
                # A. Perform standard web search
                text_results = list(ddgs.text(query, max_results=8, timelimit="y"))
                for r in text_results:
                    r["source_type"] = "text"
                    # text() results usually don't have a structured date field

                # B. Perform news search (better for recent dates)
                try:
                    news_results = list(ddgs.news(query, max_results=5, timelimit="y"))
                    for r in news_results:
                        r["source_type"] = "news"
                        # news() results have a 'date' field
                except Exception as e:
                    logger.warning(f"DDGS News search failed: {str(e)}")
                    news_results = []

                results = text_results + news_results
        except ImportError:
            logger.error("ddgs library not found.")
            return []
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {str(e)}")
            return []

        if not results:
            logger.warning(f"No search results found for query: {query}")
            return []

        # 2. Extract and Structure with OpenAI
        results_text = json.dumps(results, indent=2)
        logger.info(f"Search results context (snippet): {results_text[:500]}...")

        prompt = f"""You are a customs data extraction assistant.

        I have performed a web search for: "{query}"

        Here are the raw search results:
        {results_text}

        Please analyze these search results and extract relevant customs information ABOUT IMPORTS.
        If a source discusses both imports and exports, extract ONLY the import-related portions.
        Select the most relevant 3-5 sources that contain specific details about:
        - Customs clearance procedures for imports
        - Import documentation/permits
        - Restricted items/sanctions on imports
        - Port of entry details
        - Import exemptions (especially humanitarian)

        Structure the output as a valid JSON object matching this exact format:
        {{
            "pages": [
                {{
                    "url": "full url from search result",
                    "title": "title from search result",
                    "publisher": "inferred publisher/domain name",
                    "published_at": "YYYY-MM-DD if available in snippet, else null",
                    "snippets": [
                        "Specific relevant sentence from the snippet (150-250 chars)",
                        "Another specific detail (150-250 chars)"
                    ]
                }}
            ]
        }}

        - Use ONLY the provided search results. Do not hallucinate new sources.
        - Extract import-specific information even if the page also discusses exports.
        - In your snippets, focus exclusively on import procedures and omit any export details.
        - "published_at" source priority:
            1. Use the "date" field from news results if present.
            2. Extract from "body" or "title" (e.g., "Oct 17, 2018").
            3. Use approx date for relative terms (e.g., "2 days ago" -> {datetime.now().strftime('%Y-%m-%d')}).
            4. Default to null.
        - Ensure JSON is valid.
        """

        try:
            response = _get_openai_client().chat.completions.create(
                model="gpt-4-turbo",
                max_tokens=3000,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that structures web search data.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                response_format={"type": "json_object"},
            )

            text = response.choices[0].message.content
            # The model is forced to return JSON object, but we parse carefully
            data = json.loads(text)
            pages = data.get("pages", [])
            logger.info(f"Successfully extracted {len(pages)} sources for {query}")

            return pages[: CustomsAIService.MAX_PAGES_TO_OPEN]

        except Exception as e:
            logger.error(f"Evidence extraction/synthesis failed: {str(e)}")
            return []

    @staticmethod
    def _score_and_rank_sources(pages: List[Dict[str, Any]], country_name: str) -> List[Tuple[Dict[str, Any], Dict[str, int]]]:
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

        # --- Adaptive Selection Strategy ---
        # 1. Separate into "Fresh" (<= 90 days) and "Secondary" (> 90 days or unknown)
        fresh_sources = [(p, s) for p, s in scored if s.get("freshness", 0) >= 15]  # 15+ means < 90 days in our scoring
        secondary_sources = [(p, s) for p, s in scored if s.get("freshness", 0) < 15]

        # 2. Sort both pools by their total quality score
        fresh_sources.sort(key=lambda x: x[1]["total"], reverse=True)
        secondary_sources.sort(key=lambda x: x[1]["total"], reverse=True)

        # 3. Fill the quota (MAX_SOURCES_TO_STORE is 3-5)
        # We prefer Fresh, but if we don't have enough, we dip into Secondary.
        final_selection = fresh_sources[: CustomsAIService.MAX_SOURCES_TO_STORE]

        needed = CustomsAIService.MAX_SOURCES_TO_STORE - len(final_selection)
        if needed > 0:
            final_selection.extend(secondary_sources[:needed])

        logger.info(f"Adaptive Selection: {len(fresh_sources)} fresh found. Using {len(final_selection)} sources total.")
        return final_selection

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
            return 2

        logger.debug(f"Scoring freshness for: '{published_at}'")

        try:
            # Handle YYYY-MM-DD or ISO formats
            if "T" not in published_at and " " not in published_at:
                published_at += "T00:00:00"

            pub_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))

            # Ensure timezone awareness
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            days_old = (now - pub_date).days

            score = 5
            if days_old < 30:
                score = 30
            elif days_old < 90:
                score = 15

            logger.debug(f"Freshness score: {score} (date: {published_at}, days old: {days_old})")
            return score
        except Exception as e:
            logger.debug(f"Failed to parse published_at '{published_at}': {str(e)}")
            return 2

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

        if any(route in combined_text for route in ["port", "border", "crossing", "airport", "terminal", "entry point"]):
            score += 5

        if any(delay in combined_text for delay in ["day", "week", "month", "delay", "hours", "process"]):
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
    def _generate_summary(top_sources: List[Tuple[Dict[str, Any], Dict[str, int]]], country_name: str) -> Tuple[str, List[str]]:
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
        generate a report focusing EXCLUSIVELY on IMPORT regulations and procedures.
        Do NOT include any information about exports.

        generate:
        1. A 2-3 sentence summary specifically about imports (summary_text)
        2. 3-5 bullet points covering import-specific details (current_situation_bullets)

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
