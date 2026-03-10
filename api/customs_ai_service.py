"""
Service for generating AI-powered customs updates using OpenAI.
Uses Brave Search API for web search and OpenAI for evidence extraction.
"""

import hashlib
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import openai
import requests
from django.conf import settings

from api.models import (
    CountryCustomsEvidenceSnippet,
    CountryCustomsSnapshot,
    CountryCustomsSource,
)
from api.utils import fetch_goadmin_maps

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
    "in-kind",
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

# Retry settings for external API calls
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1  # seconds; actual delay = base * 2^attempt
_RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}


def _retry_api_call(fn, *, max_retries=_MAX_RETRIES, description="API call"):
    """
    Retry a callable up to *max_retries* times with exponential backoff.
    Retries on:
      - requests.HTTPError with a retryable status code
      - openai.APIError / openai.RateLimitError / openai.APITimeoutError
      - requests.ConnectionError / requests.Timeout
    All other exceptions propagate immediately.
    """
    last_exc = None
    for attempt in range(max_retries):
        try:
            return fn()
        except requests.exceptions.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            if status not in _RETRYABLE_HTTP_CODES:
                raise
            last_exc = e
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            last_exc = e
        except (openai.RateLimitError, openai.APITimeoutError) as e:
            last_exc = e
        except openai.APIError as e:
            status = getattr(e, "status_code", None)
            if status and status not in _RETRYABLE_HTTP_CODES:
                raise
            last_exc = e

        delay = _RETRY_BASE_DELAY * (2**attempt)
        logger.warning(f"{description} failed (attempt {attempt + 1}/{max_retries}), " f"retrying in {delay}s: {last_exc}")
        time.sleep(delay)

    logger.error(f"{description} failed after {max_retries} attempts: {last_exc}")
    raise last_exc


# ---------------------------------------------------------------------------
# Prompt templates — kept as module-level constants so they are easy to
# locate, version-control, and review independently of the logic.
# Use .format() or f-string interpolation at call sites.
# ---------------------------------------------------------------------------

_OFFICIAL_DOC_PROMPT = """From these search results, identify the single MOST OFFICIAL customs/import
regulations page from {country_name}'s own government or customs authority.

Prefer:
1. The country's customs authority website (e.g. customs.gov.xx, revenue authority)
2. A government trade/commerce ministry page about import procedures
3. An official government gazette or legal portal with customs regulations

Do NOT select pages from international organisations (UN, WFP, IFRC, UNCTAD, etc.), news outlets, or NGOs.
The page MUST be from {country_name}'s own government domain.

Search results:
{results_json}

If none of the results are from {country_name}'s government, respond with:
{{"url": "", "title": ""}}

Otherwise respond with ONLY valid JSON:
{{"url": "the exact url from the results", "title": "the exact title from the results"}}
"""

_RC_SOCIETY_PROMPT = """From these search results, identify the single MOST RELEVANT page from
{country_name}'s Red Cross or Red Crescent national society that relates to customs,
humanitarian imports, logistics, or relief operations.

Prefer:
1. The national Red Cross or Red Crescent society's official website
2. Pages about logistics, customs, import procedures, or relief operations
3. News or updates from the society about humanitarian shipments or customs

The page MUST be from {country_name}'s Red Cross or Red Crescent society, or from IFRC/ICRC
pages specifically about {country_name}'s society.

Search results:
{results_json}

If none of the results are from {country_name}'s Red Cross/Red Crescent society, respond with:
{{"url": "", "title": ""}}

Otherwise respond with ONLY valid JSON:
{{"url": "the exact url from the results", "title": "the exact title from the results"}}
"""

_EVIDENCE_EXTRACTION_PROMPT = """You are a customs data extraction assistant.

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
    3. Use approx date for relative terms (e.g., "2 days ago" -> {today}).
    4. Default to null.
- Ensure JSON is valid.
"""

_SUMMARY_PROMPT = """Based ONLY on these evidence snippets about customs in {country_name},
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

            def _search():
                resp = requests.get(
                    f"{BRAVE_SEARCH_API_BASE_URL}/web/search",
                    headers=headers,
                    params={"q": query, "count": 10},
                    timeout=15,
                )
                resp.raise_for_status()
                return resp.json().get("web", {}).get("results", [])

            web_results = _retry_api_call(_search, description="Brave search (official docs)")
        except Exception as e:
            logger.warning(f"Brave search for official docs failed: {str(e)}")
            return None

        if not web_results:
            logger.info(f"No web results for official doc search: {country_name}")
            return None

        logger.info(f"Official doc search returned {len(web_results)} results for {country_name}")

        results_for_llm = [
            {"url": r.get("url", ""), "title": r.get("title", ""), "description": r.get("description", "")} for r in web_results
        ]

        prompt = _OFFICIAL_DOC_PROMPT.format(
            country_name=country_name,
            results_json=json.dumps(results_for_llm, indent=2),
        )

        try:

            def _llm_call():
                return _get_openai_client().chat.completions.create(
                    model="gpt-4-turbo",
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                )

            response = _retry_api_call(_llm_call, description="OpenAI (official doc extraction)")
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

            def _search():
                resp = requests.get(
                    f"{BRAVE_SEARCH_API_BASE_URL}/web/search",
                    headers=headers,
                    params={"q": query, "count": 10},
                    timeout=15,
                )
                resp.raise_for_status()
                return resp.json().get("web", {}).get("results", [])

            web_results = _retry_api_call(_search, description="Brave search (RC society)")
        except Exception as e:
            logger.warning(f"Brave search for RC society failed: {str(e)}")
            return None

        if not web_results:
            logger.info(f"No web results for RC society search: {country_name}")
            return None

        logger.info(f"RC society search returned {len(web_results)} results for {country_name}")

        results_for_llm = [
            {"url": r.get("url", ""), "title": r.get("title", ""), "description": r.get("description", "")} for r in web_results
        ]

        prompt = _RC_SOCIETY_PROMPT.format(
            country_name=country_name,
            results_json=json.dumps(results_for_llm, indent=2),
        )

        try:

            def _llm_call():
                return _get_openai_client().chat.completions.create(
                    model="gpt-4-turbo",
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                )

            response = _retry_api_call(_llm_call, description="OpenAI (RC society extraction)")
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
        Validate country name against the GO Admin API country list.
        Returns (is_valid, error_message).
        """
        dirty_name = country_name.strip()
        if not dirty_name or len(dirty_name) > 100:
            return False, "Country name must be between 1 and 100 characters."

        try:
            _, iso3_to_country_name, _ = fetch_goadmin_maps()
        except Exception:
            return False, "Country validation service unavailable."

        if not iso3_to_country_name:
            return False, "Country validation service unavailable."

        # Check against known country names (case-insensitive)
        known_names = {name.lower() for name in iso3_to_country_name.values()}
        if dirty_name.lower() in known_names:
            return True, None

        # Also check COUNTRY_ALIASES for alternative names
        alias_lower = dirty_name.lower()
        for canonical, aliases in COUNTRY_ALIASES.items():
            if alias_lower == canonical or alias_lower in aliases:
                return True, None

        return False, f"'{dirty_name}' is not recognized as a valid country."

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

        snapshot.current_situation_bullets = []

        # Run summary generation and both Brave lookups concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            summary_future = executor.submit(CustomsAIService._generate_summary, top_3_sources, country_name)
            official_doc_future = executor.submit(CustomsAIService._find_official_customs_doc, country_name)
            rc_society_future = executor.submit(CustomsAIService._find_rc_society_source, country_name)

            snapshot.summary_text = summary_future.result()

            official_doc = official_doc_future.result()
            if official_doc:
                snapshot.official_doc_url = official_doc.get("url", "")[:2048]
                snapshot.official_doc_title = official_doc.get("title", "")[:500]

            rc_society = rc_society_future.result()
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
                # DB has a single specificity_score field (SmallIntegerField).
                # We store specificity + country_specificity summed here.
                # The two sub-scores remain separate in score_breakdown for
                # internal ranking decisions (see _score_and_rank_sources).
                # To recover individual values from score_breakdown later,
                # use score_breakdown["specificity"] and
                # score_breakdown["country_specificity"] directly.
                specificity_score=(score_breakdown.get("specificity", 0) + score_breakdown.get("country_specificity", 0)),
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

        try:

            def _search():
                resp = requests.get(
                    f"{BRAVE_SEARCH_API_BASE_URL}/web/search",
                    headers=headers,
                    params={"q": query, "count": 10, "freshness": "py"},
                    timeout=15,
                )
                resp.raise_for_status()
                return resp.json().get("web", {}).get("results", [])

            raw_results = _retry_api_call(_search, description="Brave search (evidence)")
            for r in raw_results:
                results.append(
                    {
                        "url": r.get("url", ""),
                        "title": r.get("title", ""),
                        "body": r.get("description", ""),
                        "date": r.get("page_age"),
                        "source_type": "text",
                    }
                )
        except Exception as e:
            logger.error(f"Brave web search failed: {str(e)}")

        if not results:
            logger.warning(f"No search results found for query: {query}")
            return []

        # 2. Extract and Structure with OpenAI
        results_text = json.dumps(results, indent=2)
        logger.debug(f"Search results context (snippet): {results_text[:500]}...")

        prompt = _EVIDENCE_EXTRACTION_PROMPT.format(
            query=query,
            results_text=results_text,
            today=datetime.now().strftime("%Y-%m-%d"),
        )

        try:

            def _llm_call():
                return _get_openai_client().chat.completions.create(
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

            response = _retry_api_call(_llm_call, description="OpenAI (evidence extraction)")
            text = response.choices[0].message.content
            data = json.loads(text)
            pages = data.get("pages", [])
            logger.info(f"Successfully extracted {len(pages)} sources for {query}")

            return pages[: CustomsAIService.MAX_PAGES_TO_OPEN]

        except Exception as e:
            logger.error(f"Evidence extraction/synthesis failed: {str(e)}")
            return []

    @staticmethod
    def _extract_base_domain(url: str) -> str:
        """
        Extract the registrable base domain from a URL for deduplication.
        e.g. 'https://www.customs.gov.ke/page' -> 'customs.gov.ke'
        Falls back to full hostname if parsing fails.
        """
        try:
            hostname = urlparse(url).hostname or ""
        except Exception:
            return ""
        parts = hostname.split(".")
        # Government domains often have 3+ parts (customs.gov.ke).
        # Keep the last 3 parts for ccTLD patterns, last 2 otherwise.
        if len(parts) >= 3 and len(parts[-1]) == 2:  # likely ccTLD
            return ".".join(parts[-3:])
        return ".".join(parts[-2:]) if len(parts) >= 2 else hostname

    @staticmethod
    def _score_and_rank_sources(pages: List[Dict[str, Any]], country_name: str) -> List[Tuple[Dict[str, Any], Dict[str, int]]]:
        """
        Score each page by authority, freshness, relevance, specificity, and
        country-specificity.  Returns list of (page_data, score_breakdown).

        Weighting philosophy (for customs/humanitarian research):
          - authority (0-50) and country_specificity (0-40) are dominant
          - relevance (0-30) and specificity (0-30) reward useful content
          - freshness (0-10) is a minor bonus / tie-breaker

        Selection strategy:
          1. Guarantee >=1 high-authority official source (if available)
          2. Guarantee >=1 country-specific source (if available)
          3. Fill remaining slots by total weighted score, preferring
             domain diversity to avoid near-duplicate sources
          4. Freshness breaks ties between otherwise similar sources
        """
        scored = []

        for page in pages:
            scores = {
                "authority": 0,
                "freshness": 0,
                "relevance": 0,
                "specificity": 0,
                "country_specificity": 0,
            }

            scores["authority"] = CustomsAIService._score_authority(page)
            scores["freshness"] = CustomsAIService._score_freshness(page.get("published_at"))

            snippets = page.get("snippets", [])
            combined_text = " ".join(s.lower() for s in snippets)

            scores["relevance"] = CustomsAIService._score_relevance(combined_text)
            scores["specificity"] = CustomsAIService._score_specificity(combined_text)
            scores["country_specificity"] = CustomsAIService._score_country_specificity(page, country_name)

            scores["total"] = sum(scores.values())
            scored.append((page, scores))

        # --- Diversity-aware selection ---
        max_sources = CustomsAIService.MAX_SOURCES_TO_STORE

        # Primary sort by total score; freshness as natural tie-breaker
        scored.sort(key=lambda x: (x[1]["total"], x[1]["freshness"]), reverse=True)

        selected: List[Tuple[Dict[str, Any], Dict[str, int]]] = []
        selected_urls: set = set()
        selected_domains: Dict[str, int] = {}  # domain -> count of selected sources

        def _pick(item, *, force: bool = False) -> bool:
            """Try to add an item to the selected set.
            Rejects duplicate URLs.  Unless *force* is True, also rejects
            a third (or later) source from the same base domain so the
            final set favours diversity across origins."""
            url = item[0].get("url", "")
            if url in selected_urls:
                return False
            if not force:
                domain = CustomsAIService._extract_base_domain(url)
                # Allow at most 1 source per domain in general fill.
                # Guaranteed picks (high-auth / country-specific) use force=True
                # so they are never blocked by this rule.
                if selected_domains.get(domain, 0) >= 1:
                    return False
            domain = CustomsAIService._extract_base_domain(url)
            selected.append(item)
            selected_urls.add(url)
            selected_domains[domain] = selected_domains.get(domain, 0) + 1
            return True

        # 1. Guarantee at least one high-authority official source
        for item in scored:
            if item[1]["authority"] >= 40 and len(selected) < max_sources:
                if _pick(item, force=True):
                    break

        # 2. Guarantee at least one country-specific source
        for item in scored:
            if item[1]["country_specificity"] >= 15 and len(selected) < max_sources:
                if _pick(item, force=True):
                    break

        # 3. Fill remaining slots by total score, preferring domain diversity
        for item in scored:
            if len(selected) >= max_sources:
                break
            _pick(item)  # diversity check applied

        # 4. If diversity filtering left slots unfilled, relax the domain cap
        if len(selected) < max_sources:
            for item in scored:
                if len(selected) >= max_sources:
                    break
                _pick(item, force=True)

        logger.info(
            f"Source selection: {len(scored)} scored, {len(selected)} selected. "
            f"High-auth: {sum(1 for _, s in selected if s['authority'] >= 40)}, "
            f"Country-specific: {sum(1 for _, s in selected if s['country_specificity'] >= 15)}, "
            f"Unique domains: {len(selected_domains)}"
        )
        return selected

    @staticmethod
    def _is_government_hostname(hostname: str) -> bool:
        """
        Return True if the hostname belongs to a recognised government
        domain pattern (e.g. .gov, .gov.xx, .go.xx, .gouv.xx, .govt.xx, .gob.xx).
        """
        gov_patterns = [
            r"\.gov(\.[a-z]{2})?$",
            r"\.go\.[a-z]{2}$",
            r"\.gob\.[a-z]{2}$",
            r"\.gouv\.[a-z]{2}$",
            r"\.govt\.[a-z]{2}$",
        ]
        return any(re.search(p, hostname) for p in gov_patterns)

    @staticmethod
    def _score_authority(page: Dict[str, Any]) -> int:
        """
        Score authority primarily from the URL hostname/domain.

        Tier 1 (50) — Official government domains: recognised .gov/.go/.gouv
            patterns, OR customs/revenue keywords in the hostname *combined*
            with a government domain pattern.
        Tier 2 (40) — Humanitarian org domains (IFRC, ICRC, WFP, UN, …).
        Tier 3 (35) — Humanitarian platforms (ReliefWeb, LogCluster, …),
            OR customs/revenue keywords in hostname on a non-government
            site (could be a statutory body with its own TLD, scored lower
            than confirmed-government to avoid false positives from blogs
            like "customstoday.pk").
        Tier 4 (25-35) — Publisher-text fallback when domain gives no signal.
        Tier 5 (10) — Generic .int / .org domains not otherwise matched.
        Tier 6 (0) — Everything else.
        """
        url = page.get("url", "").lower()
        publisher = page.get("publisher", "").lower()

        try:
            hostname = urlparse(url).hostname or ""
        except Exception:
            hostname = ""

        is_gov = CustomsAIService._is_government_hostname(hostname)

        # --- Tier 1: Official government domains (50) ---
        if is_gov:
            return 50

        # Customs/revenue keywords in hostname parts.
        # Only award 50 if the domain *also* looks governmental;
        # otherwise fall through to tier 3 (35).
        customs_host_words = ["customs", "douane", "aduana", "zoll"]
        hostname_parts = hostname.split(".")
        has_customs_keyword = any(cw in part for part in hostname_parts for cw in customs_host_words)

        # --- Tier 2: Humanitarian organisation domains (40) ---
        for domain in HUMANITARIAN_ORG_DOMAINS:
            if hostname.endswith(domain):
                return 40

        # --- Tier 3: Humanitarian platforms OR non-gov customs/revenue sites (35) ---
        for domain in HUMANITARIAN_PLATFORM_DOMAINS:
            if hostname.endswith(domain):
                return 35

        # Non-gov customs/revenue keyword in hostname — lower than gov to
        # avoid promoting news sites or blogs with "customs" in the name.
        revenue_host_words = ["revenue"]
        has_revenue_keyword = any(rw in part for part in hostname_parts for rw in revenue_host_words)
        if has_customs_keyword or has_revenue_keyword:
            return 35

        # --- Tier 4: Publisher-text fallback ---
        publisher_high = ["government", "customs authority", "ministry of", "revenue authority"]
        for term in publisher_high:
            if term in publisher:
                return 35

        publisher_medium = ["red cross", "red crescent", "world food", "unicef"]
        for term in publisher_medium:
            if term in publisher:
                return 25

        # --- Tier 5: Generic .int / .org ---
        if hostname.endswith(".int") or hostname.endswith(".org"):
            return 10

        return 0

    @staticmethod
    def _get_country_names(country_name: str) -> List[str]:
        """
        Return a list of name variants for a country: the canonical name
        plus any known aliases/abbreviations from COUNTRY_ALIASES.
        All returned in lowercase.
        """
        cn_lower = country_name.lower().strip()
        names = [cn_lower]

        # Direct lookup
        if cn_lower in COUNTRY_ALIASES:
            names.extend(COUNTRY_ALIASES[cn_lower])
            return names

        # Reverse lookup: the user-supplied name might be an alias itself
        for canonical, aliases in COUNTRY_ALIASES.items():
            if cn_lower == canonical or cn_lower in aliases:
                names.append(canonical)
                names.extend(aliases)
                return list(dict.fromkeys(names))  # dedupe, preserve order

        return names

    @staticmethod
    def _country_name_in_text(names: List[str], text: str) -> bool:
        """
        Check whether any of *names* appears in *text* as a whole-word match.
        Short names (<=3 chars, e.g. 'uk', 'uae', 'drc') require word
        boundaries to avoid accidental substring matches.
        """
        for name in names:
            if len(name) <= 3:
                # Word-boundary match for short abbreviations
                if re.search(r"\b" + re.escape(name) + r"\b", text):
                    return True
            else:
                if name in text:
                    return True
        return False

    @staticmethod
    def _score_country_specificity(page: Dict[str, Any], country_name: str) -> int:
        """
        Score how country-specific a source is.  Max 40.

        Uses _get_country_names() to handle alternative names /
        abbreviations, and _country_name_in_text() for safe matching
        (word-boundary for short tokens to avoid false positives).

        Signals (additive, capped at 40):
          - country name in title                               +15
          - country name in snippets                            +10
          - country word in URL path/domain (>3-char tokens)    +10
          - country name in publisher                           + 5
          - country-specific institutional reference            + 5
        """
        if not country_name:
            return 0

        names = CustomsAIService._get_country_names(country_name)
        cn_lower = country_name.lower().strip()

        score = 0
        title = page.get("title", "").lower()
        url = page.get("url", "").lower()
        publisher = page.get("publisher", "").lower()
        snippets = page.get("snippets", [])
        combined_snippets = " ".join(s.lower() for s in snippets)

        if CustomsAIService._country_name_in_text(names, title):
            score += 15

        # Country name in snippet text
        if CustomsAIService._country_name_in_text(names, combined_snippets):
            score += 10

        # Country tokens in URL / domain — only use tokens >3 chars to
        # avoid matching short strings like "uk" inside unrelated path
        # segments (e.g. "/lookup/").
        url_tokens = [w for n in names for w in n.split() if len(w) > 3]
        if url_tokens and any(t in url for t in url_tokens):
            score += 10

        # Country name in publisher
        if CustomsAIService._country_name_in_text(names, publisher):
            score += 5

        # Country-specific institutional references
        all_text = f"{title} {combined_snippets}"
        institutional_terms = [
            f"{cn_lower} customs",
            f"{cn_lower} revenue",
            f"{cn_lower} red cross",
            f"{cn_lower} red crescent",
            "ministry of",
            "national society",
            "customs authority",
            "border agency",
        ]
        if any(term in all_text for term in institutional_terms):
            score += 5

        return min(score, 40)

    @staticmethod
    def _score_freshness(published_at: Optional[str]) -> int:
        """
        Score freshness as a minor bonus / tie-breaker.  Max 10.
        Reduced from the previous 0-30 range so that recent but weak
        sources cannot outrank strong official ones.
        """
        if not published_at:
            return 1

        try:
            # Handle YYYY-MM-DD or ISO formats
            if "T" not in published_at and " " not in published_at:
                published_at += "T00:00:00"

            pub_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))

            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)

            days_old = (datetime.now(timezone.utc) - pub_date).days

            if days_old < 30:
                return 10
            elif days_old < 90:
                return 7
            elif days_old < 180:
                return 5
            elif days_old < 365:
                return 3
            else:
                return 1
        except Exception:
            return 1

    @staticmethod
    def _score_relevance(combined_text: str) -> int:
        """
        Score relevance using grouped keyword categories.  Max 30.
        Rewards breadth of coverage across meaningful categories
        (customs, humanitarian, permits, exemptions, logistics)
        rather than raw repetition of the same terms.
        """
        score = 0
        max_per_category = 8  # cap per category to prevent one dominating

        for keywords in RELEVANCE_KEYWORD_CATEGORIES.values():
            category_hits = sum(1 for kw in keywords if kw in combined_text)
            if category_hits >= 1:
                # First hit = 4 pts, each additional (up to 2 more) = +2 pts
                cat_score = 4 + min(category_hits - 1, 2) * 2
                score += min(cat_score, max_per_category)

        return min(score, 30)

    @staticmethod
    def _score_specificity(combined_text: str) -> int:
        """
        Score operationally useful specificity.  Max 30.
        Rewards concrete details a logistics officer would need:
        document names, named authorities, legal references,
        timelines, and named entry points / corridors.
        """
        score = 0

        # Document names and forms
        doc_terms = [
            "certificate",
            "declaration",
            "form ",
            "invoice",
            "bill of lading",
            "packing list",
            "manifest",
            "letter of credit",
            "waybill",
        ]
        if any(t in combined_text for t in doc_terms):
            score += 8

        # Named authorities or ministries
        authority_terms = [
            "ministry of",
            "minister of",
            "authority",
            "bureau",
            "directorate",
            "commissioner",
            "customs office",
            "revenue service",
            "border agency",
            "department of",
        ]
        if any(t in combined_text for t in authority_terms):
            score += 7

        # Legal references (acts, regulations, decrees)
        legal_terms = [
            "law ",
            "act ",
            "regulation",
            "decree",
            "order no",
            "article ",
            "section ",
            "gazette",
            "statute",
            "protocol",
            "convention",
        ]
        if any(t in combined_text for t in legal_terms):
            score += 5

        # Timelines and processing durations
        timeline_terms = [
            "days",
            "hours",
            "weeks",
            "months",
            "business days",
            "working days",
            "processing time",
            "timeline",
            "deadline",
        ]
        if any(t in combined_text for t in timeline_terms):
            score += 5

        # Entry points, ports, airports, corridors
        entry_terms = [
            "port",
            "airport",
            "border",
            "crossing",
            "terminal",
            "entry point",
            "corridor",
            "checkpoint",
            "gateway",
        ]
        if any(t in combined_text for t in entry_terms):
            score += 5

        return min(score, 30)

    @staticmethod
    def _determine_confidence(top_sources: List[Tuple[Dict[str, Any], Dict[str, int]]]) -> str:
        """
        Determine confidence level based on sources.
        Thresholds aligned with updated score ranges:
          authority 40+ = high-auth org/gov, freshness 7+ = <90 days, 5+ = <180 days.
        High: 2+ high authority AND 1+ source newer than 90 days
        Medium: 1+ high authority OR 2+ medium AND 1+ source newer than 180 days
        Low: Otherwise
        """
        if not top_sources:
            return "Low"

        high_auth_count = sum(1 for _, scores in top_sources if scores.get("authority", 0) >= 40)
        medium_auth_count = sum(1 for _, scores in top_sources if 25 <= scores.get("authority", 0) < 40)
        fresh_90_count = sum(1 for _, scores in top_sources if scores.get("freshness", 0) >= 7)
        fresh_180_count = sum(1 for _, scores in top_sources if scores.get("freshness", 0) >= 5)

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

        prompt = _SUMMARY_PROMPT.format(
            country_name=country_name,
            evidence_text=evidence_text,
        )

        try:

            def _llm_call():
                return _get_openai_client().chat.completions.create(
                    model="gpt-4-turbo",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                )

            response = _retry_api_call(_llm_call, description="OpenAI (summary generation)")
            data = json.loads(response.choices[0].message.content)
            return data.get("summary_text", "Not confirmed in sources")

        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")

        return "Not confirmed in sources"
