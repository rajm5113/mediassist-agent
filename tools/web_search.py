"""
tools/web_search.py — Smart Live Medical Web Search

🎓 ARCHITECTURE:
   This tool uses a 2-layer design to minimize unnecessary API calls:

   Layer 1 (in agent/core.py): Keyword pre-filter
     - Checks the user's raw message for trigger words like "latest", "recent",
       "study", "recall", etc. before any LLM call.
     - If no triggers → adds a hint to the message telling the LLM NOT to search.
     - If triggers found → hints the LLM that search is available.

   Layer 2 (here): The actual search tool
     - In-session cache: identical queries never hit the network twice.
     - Rate limiter: max 1 search per 3 seconds to avoid abuse.
     - Smart routing: "research"/"study" keywords → PubMed API (academic)
                     Everything else → DuckDuckGo (general web)
"""

import json
import time
import requests
from duckduckgo_search import DDGS

# ── In-session cache (key: query string, value: result JSON) ──
_search_cache: dict = {}

# ── Rate limiter state ──
_last_search_time: float = 0.0
_MIN_SEARCH_INTERVAL = 3.0  # seconds between searches


# ─────────────────────────────────────────────────────────────────────────────
# TRIGGER KEYWORDS — also used by agent/core.py Layer 1 filter
# ─────────────────────────────────────────────────────────────────────────────
SEARCH_TRIGGER_KEYWORDS = {
    "latest", "recent", "new study", "new research", "2024", "2025", "2026",
    "just approved", "fda approved", "fda recall", "recalled", "recalled by",
    "breaking", "today", "this week", "this month", "current", "emerging",
    "clinical trial", "trial results", "phase 3", "meta-analysis",
    "published", "journal", "paper", "evidence", "shortage", "news"
}


def _is_research_query(query: str) -> bool:
    """Returns True if the query should hit PubMed (academic sources)."""
    research_keywords = {"study", "research", "trial", "clinical", "evidence",
                         "meta-analysis", "journal", "paper", "published",
                         "efficacy", "mechanism", "pathophysiology"}
    q_lower = query.lower()
    return any(kw in q_lower for kw in research_keywords)


def _search_pubmed(query: str, max_results: int = 3) -> list[dict]:
    """
    Query PubMed's free E-utilities API for academic medical articles.
    No API key needed. Returns a list of {title, abstract, url} dicts.
    """
    # Step 1: Search for article IDs
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "pubmed", "term": query,
        "retmax": max_results, "retmode": "json",
        "sort": "relevance"
    }
    search_resp = requests.get(search_url, params=search_params, timeout=8)
    search_resp.raise_for_status()
    ids = search_resp.json().get("esearchresult", {}).get("idlist", [])

    if not ids:
        return []

    # Step 2: Fetch summaries of those IDs
    summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    summary_resp = requests.get(summary_url, params={
        "db": "pubmed", "id": ",".join(ids), "retmode": "json"
    }, timeout=8)
    summary_resp.raise_for_status()
    result_data = summary_resp.json().get("result", {})

    articles = []
    for pmid in ids:
        doc = result_data.get(pmid, {})
        title = doc.get("title", "No title")
        source = doc.get("fulljournalname", doc.get("source", "PubMed"))
        pub_date = doc.get("pubdate", "")
        articles.append({
            "title": title,
            "snippet": f"Published in {source} ({pub_date})",
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        })

    return articles


def _search_duckduckgo(query: str, max_results: int = 4) -> list[dict]:
    """
    Query DuckDuckGo's free search. No API key needed.
    Returns a list of {title, snippet, url} dicts.
    """
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query + " site:mayoclinic.org OR site:nih.gov OR site:medlineplus.gov OR site:healthline.com", max_results=max_results):
            results.append({
                "title": r.get("title", ""),
                "snippet": r.get("body", "")[:300],
                "url": r.get("href", "")
            })
    return results


def web_search(query: str) -> str:
    """
    Main entry point called by the AI agent.
    Performs a smart medical web search and returns a JSON summary.
    Uses caching and rate limiting to minimize API calls.
    """
    global _last_search_time

    # Input sanitization
    query = query.strip()
    if not query:
        return json.dumps({"status": "error", "message": "Empty search query."})

    # ── 1. Cache check (same query in this session → free) ──
    cache_key = query.lower()
    if cache_key in _search_cache:
        print(f"  [WebSearch] Cache hit for: '{query}'")
        return _search_cache[cache_key]

    # ── 2. Rate limiter ──
    elapsed = time.time() - _last_search_time
    if elapsed < _MIN_SEARCH_INTERVAL:
        time.sleep(_MIN_SEARCH_INTERVAL - elapsed)

    try:
        print(f"  [WebSearch] Searching: '{query}'")
        _last_search_time = time.time()

        # ── 3. Route to best search source ──
        if _is_research_query(query):
            results = _search_pubmed(query, max_results=3)
            source = "PubMed (Academic)"
            # Supplement with DuckDuckGo if PubMed returns nothing
            if not results:
                results = _search_duckduckgo(query, max_results=3)
                source = "Web"
        else:
            results = _search_duckduckgo(query, max_results=4)
            source = "Web"

        if not results:
            result = json.dumps({
                "status": "no_results",
                "message": f"No results found for '{query}'. The information may not be online."
            })
        else:
            result = json.dumps({
                "status": "success",
                "query": query,
                "source": source,
                "results": results
            })

        # ── 4. Cache the result ──
        _search_cache[cache_key] = result
        return result

    except Exception as e:
        return json.dumps({"status": "error", "message": f"Search failed: {str(e)}"})
