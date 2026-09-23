from typing import List, Dict, Any, Optional
from app.config import settings
from datetime import datetime
import asyncio
import re
import requests


class EvidenceRetriever:
    def __init__(self):
        pass

    async def search(self, claim: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search evidence via DuckDuckGo (free, no API key) in two passes for more coverage"""
        query = self._build_search_query(claim)

        results = await asyncio.gather(
            self._search_ddg(query, max_results=10),
            self._search_ddg(query, max_results=15, region="wt-wt"),
            return_exceptions=True
        )

        all_evidence = []
        for result in results:
            if isinstance(result, list):
                all_evidence.extend(result)

        # Deduplicate by URL
        seen_urls = set()
        unique_evidence = []
        for ev in all_evidence:
            if ev['source_url'] not in seen_urls:
                seen_urls.add(ev['source_url'])
                unique_evidence.append(ev)

        unique_evidence = unique_evidence[:15]  # Top 15 evidence

        # Fetch real publication dates from each page in parallel (best-effort).
        # DDG doesn't provide dates — without this, recency was previously faked.
        dates = await asyncio.gather(
            *[asyncio.to_thread(self._fetch_published_date_sync, ev['source_url']) for ev in unique_evidence],
            return_exceptions=True
        )
        for ev, date in zip(unique_evidence, dates):
            ev['publication_date'] = date if isinstance(date, datetime) else None

        return unique_evidence

    def _fetch_published_date_sync(self, url: str) -> Optional[datetime]:
        """Best-effort extraction of a real publish date from the page's own metadata."""
        try:
            resp = requests.get(
                url, timeout=5,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; ClaimVerificationEngine/1.0)'}
            )
            html = resp.text[:150000]  # cap — we only need the <head>
            patterns = [
                r'property=["\']article:published_time["\'][^>]*content=["\']([^"\']+)["\']',
                r'name=["\']publish(?:ed)?[-_]?date["\'][^>]*content=["\']([^"\']+)["\']',
                r'itemprop=["\']datePublished["\'][^>]*content=["\']([^"\']+)["\']',
                r'name=["\']date["\'][^>]*content=["\']([^"\']+)["\']',
                r'<time[^>]+datetime=["\']([^"\']+)["\']',
            ]
            for pat in patterns:
                m = re.search(pat, html, re.IGNORECASE)
                if m:
                    from dateutil import parser as dateparser
                    try:
                        dt = dateparser.parse(m.group(1))
                        if dt.tzinfo is not None:
                            dt = dt.replace(tzinfo=None)
                        return dt
                    except Exception:
                        continue
        except Exception:
            pass
        return None  # honestly unknown — NOT faked as "today"

    def _build_search_query(self, claim: Dict[str, Any]) -> str:
        """Build optimized search query from claim"""
        parts = []
        if claim.get('subject'):
            parts.append(str(claim['subject']))
        if claim.get('predicate'):
            parts.append(str(claim['predicate']))
        if claim.get('object'):
            parts.append(str(claim['object']))
        if claim.get('location'):
            parts.append(str(claim['location']))
        return " ".join(parts)

    def _search_ddg_sync(self, query: str, max_results: int, region: str) -> List[Dict[str, Any]]:
        from ddgs import DDGS
        evidence_list = []
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, region=region, max_results=max_results):
                    url = r.get('href') or r.get('url')
                    if not url:
                        continue
                    evidence_list.append({
                        'source_url': url,
                        'source_domain': url.split('/')[2] if '//' in url else url,
                        'snippet': (r.get('body') or '')[:500],
                        'supports_claim': None,  # set later by pipeline's stance classifier
                        'credibility_score': 0.7,  # Default, updated by source_credibility.py
                        'entity_overlap': 0.7
                    })
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
        return evidence_list

    async def _search_ddg(self, query: str, max_results: int = 10, region: str = "wt-wt") -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._search_ddg_sync, query, max_results, region)
