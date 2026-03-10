"""
Service for generating AI-powered customs updates using OpenAI.
Uses Brave Search API for web search and OpenAI for evidence extraction.
"""

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import openai
import requests
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
    "humanitarian",
    "relief",
    "duty-free",
    "tax exempt",
    "ngo",
    "red cross",
    "red crescent",
    "ocha",
    "consignment",
    "donation",
    "in-kind",acc
    "medical supplies",
    "temporary admission",
    "transit",
    "pre-clearance",
}

# Grouped keyword categories for relevance scoring.
# Each category is scored independently to reward breadth of coverage
# and avoid over-rewarding repetitive use of the same terms.
RELEVANCE_KEYWORD_CATEGORIES = {
    "customs_clearance": [
        "customs",
        "clearance",
        "import",
        "declaration",
        "tariff",
        "harmonized",
        "customs broker",
        "customs agent",
    ],
    "humanitarian_relief": [
        "humanitarian",
        "relief",
        "emergency",
        "disaster",
        "aid",
        "ngo",
        "red cross",
        "red crescent",
        "ocha",
        "donation",
        "in-kind",
    ],
    "permits_documentation": [
        "permit",
        "license",
        "certificate",
        "documentation",
        "waiver",
        "pre-clearance",
        "authorization",
        "approval",
    ],
    "duty_tax_exemptions": [
        "exemption",
        "duty-free",
        "tax exempt",
        "duty free",
        "tax-free",
        "tax waiver",
        "concession",
        "zero-rated",
    ],
    "logistics_entry": [
        "port",
        "airport",
        "border",
        "corridor",
        "terminal",
        "entry point",
        "crossing",
        "transit",
        "consignment",
        "shipment",
        "cargo",
    ],
}

# Humanitarian org domains scored as medium-high authority.
# Matched against URL hostname with endswith() to avoid false positives.
HUMANITARIAN_ORG_DOMAINS = [
    "ifrc.org",
    "icrc.org",
    "wfp.org",
    "unocha.org",
    "who.int",
    "unicef.org",
    "unhcr.org",
    "iom.int",
    "un.org",
    "unctad.org",
    "wcoomd.org",
]

# Humanitarian information platforms — slightly lower than org domains.
HUMANITARIAN_PLATFORM_DOMAINS = [
    "reliefweb.int",
    "logcluster.org",
    "humanitarianresponse.info",
]

# Common alternative country names, abbreviations, and official names.
# Keys are the canonical name (lowercase); values are lists of alternates.
# Used by _score_country_specificity for flexible matching.
COUNTRY_ALIASES: Dict[str, List[str]] = {
    "united states": ["usa", "us", "united states of america", "u.s.", "u.s.a."],
    "united kingdom": ["uk", "u.k.", "great britain", "britain", "england"],
    "democratic republic of the congo": ["drc", "dr congo", "congo-kinshasa", "congo kinshasa"],
    "republic of the congo": ["congo-brazzaville", "congo brazzaville"],
    "south korea": ["republic of korea", "korea", "rok"],
    "north korea": ["dprk", "democratic people's republic of korea"],
    "ivory coast": ["côte d'ivoire", "cote d'ivoire", "cote divoire"],
    "myanmar": ["burma"],
    "eswatini": ["swaziland"],
    "czechia": ["czech republic"],
    "türkiye": ["turkey", "turkiye"],
    "timor-leste": ["east timor"],
    "cabo verde": ["cape verde"],
    "bosnia and herzegovina": ["bih", "bosnia"],
    "trinidad and tobago": ["trinidad"],
    "papua new guinea": ["png"],
    "central african republic": ["car"],
    "south sudan": ["s. sudan", "s sudan"],
    "north macedonia": ["macedonia", "fyrom"],
    "saudi arabia": ["ksa"],
    "united arab emirates": ["uae"],
    "new zealand": ["aotearoa"],
    "philippines": ["the philippines"],
}

BRAVE_SEARCH_API_BASE_URL = "https://api.search.brave.com/res/v1"


class CustomsAIService:
    """Service for generating customs updates via OpenAI Responses API."""

    MAX_PAGES_TO_OPEN = 5
    MAX_SOURCES_TO_STORE = 3
    MAX_SNIPPETS_PER_SOURCE = 8
    SNIPPET_MIN_CHARS = 500
    SNIPPET_MAX_CHARS = 1000

    @staticmethod
    def _get_brave_headers() -> dict:
        """Get headers for Brave Search API requests."""
        if not settings.BRAVE_SEARCH_API_KEY:
            raise ValueError("BRAVE_SEARCH_API_KEY is not configured in settings")
        return {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": settings.BRAVE_SEARCH_API_KEY,
        }

    @staticmethod
    def _find_official_customs_doc(country_name: str) -> Optional[Dict[str, str]]:
        """
        Search for the official government customs authority page for a country.
        Returns {"url": "...", "title": "..."} or None.
        """
        query = f"{country_name} official government customs authority import regulations"
        headers = CustomsAIService._get_brave_headers()

        try:
            resp = requests.get(
                f"{BRAVE_SEARCH_API_BASE_URL}/web/search",
                headers=headers,
                params={"q": query, "count": 10},
                timeout=15,
            )
            resp.raise_for_status()
            web_results = resp.json().get("web", {}).get("results", [])
        except Exception as e:
            logger.warning(f"Brave search for official docs failed: {str(e)}")
            return None

        if not web_results:
            logger.info(f"No web results for official doc search: {country_name}")
            return None

        logger.info(f"Official doc search returned {len(web_results)} results for {country_name}")

        results_for_llm = [
            {"url": r.get("url", ""), "title": r.get("title", ""), "description": r.get("description", "")}
            for r in web_results
        ]

        prompt = f"""From these search results, identify the single MOST OFFICIAL customs/import
regulations page from {country_name}'s own government or customs authority.

Prefer:
1. The country's customs authority website (e.g. customs.gov.xx, revenue authority)
2. A government trade/commerce ministry page about import procedures
3. An official government gazette or legal portal with customs regulations

Do NOT select pages from international organisations (UN, WFP, IFRC, UNCTAD, etc.), news outlets, or NGOs.
The page MUST be from {country_name}'s own government domain.

Search results:
{json.dumps(results_for_llm, indent=2)}

If none of the results are from {country_name}'s government, respond with:
{{"url": "", "title": ""}}

Otherwise respond with ONLY valid JSON:
{{"url": "the exact url from the results", "title": "the exact title from the results"}}
"""

        try:
            response = _get_openai_client().chat.completions.create(
                model="gpt-4-turbo",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            url = data.get("url", "").strip()
            title = data.get("title", "").strip()
            if url:
                logger.info(f"Found official doc for {country_name}: {url}")
                return {"url": url, "title": title}
            logger.info(f"No official government doc identified for {country_name}")
        except Exception as e:
            logger.warning(f"Official doc extraction failed: {str(e)}")

        return None

    @staticmethod
    def _find_rc_society_source(country_name: str) -> Optional[Dict[str, str]]:
        """
        Search for the country's Red Cross or Red Crescent society page
        with customs/logistics-related content.
        Returns {"url": "...", "title": "..."} or None.
        """
        query = f"{country_name} Red Cross Red Crescent society customs import humanitarian logistics"
        headers = CustomsAIService._get_brave_headers()

        try:
            resp = requests.get(
                f"{BRAVE_SEARCH_API_BASE_URL}/web/search",
                headers=headers,
                params={"q": query, "count": 10},
                timeout=15,
            )
            resp.raise_for_status()
            web_results = resp.json().get("web", {}).get("results", [])
        except Exception as e:
            logger.warning(f"Brave search for RC society failed: {str(e)}")
            return None

        if not web_results:
            logger.info(f"No web results for RC society search: {country_name}")
            return None

        logger.info(f"RC society search returned {len(web_results)} results for {country_name}")

        results_for_llm = [
            {"url": r.get("url", ""), "title": r.get("title", ""), "description": r.get("description", "")}
            for r in web_results
        ]

        prompt = f"""From these search results, identify the single MOST RELEVANT page from
{country_name}'s Red Cross or Red Crescent national society that relates to customs,
humanitarian imports, logistics, or relief operations.

Prefer:
1. The national Red Cross or Red Crescent society's official website
2. Pages about logistics, customs, import procedures, or relief operations
3. News or updates from the society about humanitarian shipments or customs

The page MUST be from {country_name}'s Red Cross or Red Crescent society, or from IFRC/ICRC
pages specifically about {country_name}'s society.

Search results:
{json.dumps(results_for_llm, indent=2)}

If none of the results are from {country_name}'s Red Cross/Red Crescent society, respond with:
{{"url": "", "title": ""}}

Otherwise respond with ONLY valid JSON:
{{"url": "the exact url from the results", "title": "the exact title from the results"}}
"""

        try:
            response = _get_openai_client().chat.completions.create(
                model="gpt-4-turbo",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            url = data.get("url", "").strip()
            title = data.get("title", "").strip()
            if url:
                logger.info(f"Found RC society source for {country_name}: {url}")
                return {"url": url, "title": title}
            logger.info(f"No RC society source identified for {country_name}")
        except Exception as e:
            logger.warning(f"RC society source extraction failed: {str(e)}")

        return None

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
        query = f"{country_name} humanitarian relief goods customs import clearance procedures exemptions {current_year}"

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

        summary_text = CustomsAIService._generate_summary(top_3_sources, country_name)
        snapshot.summary_text = summary_text
        snapshot.current_situation_bullets = []

        # Find official government customs documentation
        official_doc = CustomsAIService._find_official_customs_doc(country_name)
        if official_doc:
            snapshot.official_doc_url = official_doc.get("url", "")[:2048]
            snapshot.official_doc_title = official_doc.get("title", "")[:500]

        # Find Red Cross/Red Crescent society source
        rc_society = CustomsAIService._find_rc_society_source(country_name)
        if rc_society:
            snapshot.rc_society_url = rc_society.get("url", "")[:2048]
            snapshot.rc_society_title = rc_society.get("title", "")[:500]

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
        Use Brave Search API to search for customs information and OpenAI to structure it.
        """
        pages = []

        # 1. Perform Web Search via Brave Search API
        results = []
        headers = CustomsAIService._get_brave_headers()

        # A. Web search
        try:
            resp = requests.get(
                f"{BRAVE_SEARCH_API_BASE_URL}/web/search",
                headers=headers,
                params={"q": query, "count": 10, "freshness": "py"},
                timeout=15,
            )
            resp.raise_for_status()
            for r in resp.json().get("web", {}).get("results", []):
                results.append({
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "body": r.get("description", ""),
                    "date": r.get("page_age"),
                    "source_type": "text",
                })
        except Exception as e:
            logger.error(f"Brave web search failed: {str(e)}")

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

        Please analyze these search results and extract relevant customs information about HUMANITARIAN IMPORTS.
        If a source discusses both imports and exports, extract ONLY the import-related portions.
        Select the most relevant 3-5 sources that contain specific details about:
        - Customs clearance procedures specifically for humanitarian/relief imports
        - Required documentation and permits for NGO or humanitarian shipments
        - Duty or tax exemptions available for relief goods
        - Restricted or prohibited items relevant to humanitarian operations (e.g., medical supplies, communications equipment)
        - Port of entry or logistics corridor details for humanitarian cargo
        - Typical clearance timelines and known bottlenecks
        - Any recent regulatory changes affecting humanitarian imports

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
        - Prioritise information that would help a humanitarian logistics officer clear relief goods.
        - If a source mentions both commercial and humanitarian import procedures, extract ONLY the humanitarian-specific details.
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

        # --- Adaptive Selection Strategy --- # Redo logic using exponential decay based on whether country is under crisis or not - use ifrc api for this
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
    def _generate_summary(top_sources: List[Tuple[Dict[str, Any], Dict[str, int]]], country_name: str) -> str:
        """
        Generate a concise summary paragraph using only provided evidence.
        """
        all_snippets = []
        for page_data, _ in top_sources:
            all_snippets.extend(page_data.get("snippets", []))

        if not all_snippets:
            return "Not confirmed in sources"

        evidence_text = "\n".join(all_snippets)

        prompt = f"""Based ONLY on these evidence snippets about customs in {country_name},
        generate a report focusing EXCLUSIVELY on IMPORTING HUMANITARIAN AND RELIEF GOODS.
        Do NOT include any information about exports.

        Write a single coherent paragraph of 4-5 sentences aimed at a humanitarian logistics
        officer planning a relief shipment. The summary should cover whichever of the following
        topics are supported by the evidence:
        - Key documents/permits required for humanitarian imports
        - Any duty/tax exemptions for relief goods
        - Restricted items relevant to humanitarian operations
        - Estimated clearance timeframes or known delays
        - Recommended entry points or logistics corridors

        IMPORTANT: Only use information from the snippets below. If a topic is not covered
        in the snippets, omit it rather than guessing. Do not include export information.
        Do NOT use bullet points. Write flowing prose only.

        Evidence:
        {evidence_text}

        Return ONLY valid JSON:
        {{
            "summary_text": "..."
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
                return data.get("summary_text", "Not confirmed in sources")

        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")

        return "Not confirmed in sources"
