"""Initial site fetch for the audit engine (diagram 3.1, step B).

Single source of the raw material every deterministic submodule reads: HTML,
response headers, robots.txt and the sitemap URL list. No LLM involved.

Two layers, kept apart on purpose, same shape as the other submodules:

* :func:`evaluate_fetch` — **pure and synchronous**. Receives the raw outcome
  of the main-page request (:class:`PageFetchOutcome`) plus the raw text of
  robots.txt, the sitemap XML, and any sub-sitemap XML already fetched by the
  shell (``None`` for any of them), and resolves them into a
  :class:`FetchResult`: decides ``reachability`` and classifies/combines the
  sitemap's declared URLs via :func:`_classify_sitemap_document` and
  :func:`_resolve_sitemap_urls`. No network, trivially unit-testable with
  fixtures.
* :func:`fetch_site` — the **async shell**. Fetches the main page, and — only
  when the site is reachable — /robots.txt and /sitemap.xml (falling back to
  /sitemap_index.xml). If that sitemap is a ``<sitemapindex>``, it also fetches
  up to :data:`MAX_SUB_SITEMAPS` child sitemaps, then delegates all the
  interpretation to the pure layer.

Reuse vs. own logic (declared here since it is a judgment call, not spelled
out anywhere else):

* The main-page request is NOT done via ``fetch_page.py:fetch_page``.
  That function already follows redirects, captures headers and handles
  timeouts/connection errors — but it never keeps the raw HTML, only a
  stripped ``text_content`` after decomposing scripts/nav/footer. Every other
  submodule (schema_org.py's JSON-LD extraction, ssr.py's SSR heuristic) needs
  the untouched HTML, so the main-page fetch is a small dedicated
  ``requests.get`` here. It reuses ``fetch_page.DEFAULT_HEADERS`` so the
  User-Agent/Accept headers stay identical to the rest of the codebase.
* robots.txt IS reused as-is via ``fetch_page.py:fetch_robots_txt``:
  it already resolves "exists vs. 404 vs. request error" into one boolean,
  which is exactly what this module needs (see the 404 decision below).
* The sitemap is NOT reused via ``fetch_page.py:crawl_sitemap``: that
  function recurses into every sub-sitemap of a sitemap index with no depth
  limit and returns the fully-crawled page list, which is more crawling than
  step B needs (see the depth decision below).

Declared decisions (judgment calls the prompt asked to make explicit):

* Sitemap depth: **one level of recursion, namespace-aware root detection**.
  The root tag of the fetched sitemap XML decides how its ``<loc>`` values
  are read (real sitemaps almost always declare
  ``xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"``, so root detection
  must not depend on a bare/prefixed tag name):
    - ``<urlset>``: every ``<loc>`` under ``<url>`` is a real page. Read
      directly, same as before.
    - ``<sitemapindex>``: every ``<loc>`` under ``<sitemap>`` is a
      *child-sitemap* URL, not a page. The shell follows up to
      :data:`MAX_SUB_SITEMAPS` of them (see cap below) and reads the real
      pages out of each. If a followed child sitemap turns out to be itself a
      ``<sitemapindex>``, it is **not** followed further — a second level of
      indirection is out of scope, same spirit as the original "zero
      recursion" call but now one level deeper since a bare index with no
      real pages was making ``sitemap_urls`` useless on any indexed site
      (Yoast/WordPress, Shopify, most large sites).
* Sub-sitemap cap: at most :data:`MAX_SUB_SITEMAPS` (20) child sitemaps are
  followed per index — an index can list hundreds, and this module only needs
  enough pages for downstream heuristics, not a full crawl.
* Page cap: at most :data:`MAX_SITEMAP_URLS` (500) page URLs are kept overall
  (single ``<urlset>`` or combined across followed sub-sitemaps), in document
  order, de-duplicated.
* Resilience: an individual sub-sitemap fetch failing (timeout, 404, invalid
  XML) is skipped and the rest are still followed — it never fails the whole
  fetch. Truncation (cap on sub-sitemaps or on pages) and any skipped
  sub-sitemap are recorded in :attr:`FetchResult.notes`, the same field the
  rest of the package uses for this kind of "here's what happened, not an
  error" bookkeeping.
* Timeouts: :data:`PAGE_TIMEOUT_S` (15s) for the main page,
  :data:`ROBOTS_TIMEOUT_S` (10s) for robots.txt, :data:`SITEMAP_TIMEOUT_S`
  (10s) for the sitemap and reused for each sub-sitemap fetch — robots.txt/
  sitemap are small, secondary files that should fail fast rather than hold
  up the whole fetch.
* Reachability: ``UNREACHABLE`` when the main-page request itself fails
  (timeout, DNS, connection refused — no HTTP response at all) or the server
  answers with a 5xx. A 4xx (e.g. 404) is a real HTTP response — the server is
  reachable, the resource just isn't there — so it resolves to
  ``reachability=OK`` with ``status_code`` reflecting the 4xx; downstream
  submodules can act on the status code if they need to. robots.txt/sitemap
  failures are always independent of this decision: they degrade to ``None``
  each on their own and never flip the overall fetch to ``UNREACHABLE``.
* Not done here (declared out of scope): preferring the ``Sitemap:`` directive
  from robots.txt over ``/sitemap.xml``/``/sitemap_index.xml``. robots.txt is
  already fetched before the sitemap, so wiring the discovered URL in is
  plausible, but it changes ``fetch_sitemap_fn``'s contract (base URL + fixed
  candidate paths today) and touches every test double built against that
  shape. Left as a future improvement rather than folded into this fix.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from .fetch_page import DEFAULT_HEADERS, fetch_robots_txt
from .models import FetchResult, Reachability

PAGE_TIMEOUT_S = 15
ROBOTS_TIMEOUT_S = 10
SITEMAP_TIMEOUT_S = 10
MAX_SITEMAP_URLS = 500
LIGHTHOUSE_TIMEOUT_S = 45
MAX_SUB_SITEMAPS = 20  # cap on how many child sitemaps a <sitemapindex> is followed into
_UNREACHABLE_STATUS_FLOOR = 500  # 5xx -> UNREACHABLE; 4xx is a real, reachable response
_SITEMAP_PATHS = ("/sitemap.xml", "/sitemap_index.xml")
_SITEMAP_URLSET = "urlset"
_SITEMAP_INDEX = "sitemapindex"


# --------------------------------------------------------------------------- #
# Raw input to the pure layer (the shell produces this from the main-page request)
# --------------------------------------------------------------------------- #
class PageFetchOutcome(BaseModel):
    """Raw result of requesting the main page, before interpretation.

    ``ok=False`` means the request itself never got an HTTP response (timeout,
    DNS failure, connection refused) — distinct from a completed request that
    came back with an error status code, which is ``ok=True`` with
    ``status_code`` set.
    """

    ok: bool
    status_code: int | None = None
    final_url: str | None = None  # after following redirects
    html: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    error: str | None = None


# --------------------------------------------------------------------------- #
# Pure layer
# --------------------------------------------------------------------------- #
def evaluate_fetch(
    domain: str,
    page: PageFetchOutcome,
    robots_txt: str | None,
    sitemap_xml: str | None,
    lighthouse_raw: dict | None,  # Nuevo parámetro
    *,
    sub_sitemap_xmls: Sequence[str | None] | None = None,
    now: datetime | None = None,
) -> FetchResult:
    """Resolve a raw main-page outcome + robots.txt/sitemap text into a FetchResult.

    Pure and synchronous: no network. ``sub_sitemap_xmls`` is the raw text the
    async shell already fetched for each child sitemap it decided to follow
    (``None`` for one that failed) — this function never fetches anything
    itself, it only classifies and combines text it is handed. See the module
    docstring for the reachability and sitemap-depth decisions. When the site
    is UNREACHABLE, ``robots_txt``/``sitemap_xml`` are ignored and the payload
    fields stay empty so the orchestrator can schedule a retry without
    treating this as a partial result.
    """
    now = now or datetime.now(timezone.utc)
    unreachable = not page.ok or (
        page.status_code is not None and page.status_code >= _UNREACHABLE_STATUS_FLOOR
    )

    if unreachable:
        return FetchResult(
            domain=domain,
            reachability=Reachability.UNREACHABLE,
            status_code=page.status_code,
            final_url=page.final_url,
            fetched_at=now,
        )

    sitemap_urls, notes = _resolve_sitemap_urls(sitemap_xml, sub_sitemap_xmls)

    return FetchResult(
        domain=domain,
        reachability=Reachability.OK,
        status_code=page.status_code,
        final_url=page.final_url,
        html=page.html,
        headers=page.headers,
        robots_txt=robots_txt,
        sitemap_urls=sitemap_urls,
        lighthouse_raw=lighthouse_raw,
        fetched_at=now,
        notes=notes,
    )


def _classify_sitemap_document(xml_text: str) -> tuple[str, list[str]]:
    """Classify one sitemap XML document and extract its ``<loc>`` values.

    Namespace-aware: BeautifulSoup's ``xml`` parser resolves the default
    ``xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"`` sitemaps almost
    always declare, so the root tag's local name is read as plain
    ``"urlset"``/``"sitemapindex"`` regardless of that namespace.

    Returns ``(kind, locs)`` where ``kind`` is ``"urlset"`` (every loc is a
    real page), ``"sitemapindex"`` (every loc is a child-sitemap URL, not a
    page) or ``"invalid"`` (unparseable / unrecognized root tag — treated as
    no data, never raises).
    """
    try:
        soup = BeautifulSoup(xml_text, "xml")
    except Exception:
        return "invalid", []
    root = soup.find(True)
    if root is None or root.name not in (_SITEMAP_URLSET, _SITEMAP_INDEX):
        return "invalid", []

    locs: list[str] = []
    seen: set[str] = set()
    for loc in root.find_all("loc"):
        text = loc.get_text(strip=True)
        if not text or text in seen:
            continue
        seen.add(text)
        locs.append(text)
    return root.name, locs


def _resolve_sitemap_urls(
    sitemap_xml: str | None,
    sub_sitemap_xmls: Sequence[str | None] | None,
) -> tuple[list[str], list[str]]:
    """Combine the main sitemap doc + any already-fetched sub-sitemap docs.

    Pure: everything here is text already in hand, no network. A plain
    ``<urlset>`` is read directly. A ``<sitemapindex>`` is expanded using
    ``sub_sitemap_xmls`` — the shell's fetch results, in the same order as the
    index's ``<loc>`` entries, ``None`` where a sub-fetch failed (skipped, not
    fatal). A sub-sitemap that is itself an index is not followed further —
    one level of recursion only, see the module docstring.
    """
    if not sitemap_xml:
        return [], []

    notes: list[str] = []
    kind, locs = _classify_sitemap_document(sitemap_xml)

    if kind == _SITEMAP_URLSET:
        urls = locs
    elif kind == _SITEMAP_INDEX:
        followed = sub_sitemap_xmls or []
        notes.append(
            f"sitemap is a sitemapindex with {len(locs)} sub-sitemap(s) declared; "
            f"followed {len(followed)}"
        )
        if len(locs) > len(followed):
            notes.append(
                f"reached MAX_SUB_SITEMAPS ({MAX_SUB_SITEMAPS}); "
                f"{len(locs) - len(followed)} sub-sitemap(s) not followed"
            )
        urls = []
        seen: set[str] = set()
        for sub_xml in followed:
            if sub_xml is None:
                notes.append("a sub-sitemap fetch failed and was skipped")
                continue
            sub_kind, sub_locs = _classify_sitemap_document(sub_xml)
            if sub_kind == _SITEMAP_INDEX:
                notes.append("a sub-sitemap is itself a sitemapindex; not following a second level")
                continue
            if sub_kind != _SITEMAP_URLSET:
                continue
            for url in sub_locs:
                if url not in seen:
                    seen.add(url)
                    urls.append(url)
    else:
        urls = []

    if len(urls) > MAX_SITEMAP_URLS:
        notes.append(
            f"reached MAX_SITEMAP_URLS ({MAX_SITEMAP_URLS}); "
            f"{len(urls) - MAX_SITEMAP_URLS} discovered page URL(s) dropped"
        )
    return urls[:MAX_SITEMAP_URLS], notes


# --------------------------------------------------------------------------- #
# Async shell: main page -> (if reachable) robots.txt + sitemap -> pure layer
# --------------------------------------------------------------------------- #
async def fetch_site(
    domain: str,
    *,
    fetch_page_fn: Callable[[str, int], Awaitable[PageFetchOutcome]] | None = None,
    fetch_robots_fn: Callable[[str, int], Awaitable[str | None]] | None = None,
    fetch_sitemap_fn: Callable[[str, int], Awaitable[str | None]] | None = None,
    fetch_sub_sitemap_fn: Callable[[str, int], Awaitable[str | None]] | None = None,
    fetch_lighthouse_fn: Callable[[str, int, str | None], Awaitable[dict | None]] | None = None,
    lighthouse_api_key: str | None = None,
    now: datetime | None = None,
) -> FetchResult:

    fetch_page_fn = fetch_page_fn or _fetch_main_page
    fetch_robots_fn = fetch_robots_fn or _fetch_robots_txt
    fetch_sitemap_fn = fetch_sitemap_fn or _fetch_sitemap_xml
    fetch_sub_sitemap_fn = fetch_sub_sitemap_fn or _fetch_single_sitemap_xml
    fetch_lighthouse_fn = fetch_lighthouse_fn or _fetch_lighthouse_api

    target = _normalize_domain(domain)
    page = await fetch_page_fn(target, PAGE_TIMEOUT_S)

    if not page.ok or (
        page.status_code is not None and page.status_code >= _UNREACHABLE_STATUS_FLOOR
    ):
        return evaluate_fetch(domain, page, None, None, None, now=now)

    base = page.final_url or target

    # EJECUCIÓN CONCURRENTE: Lanzamos los tres procesos lentos a la vez
    robots_task = fetch_robots_fn(base, ROBOTS_TIMEOUT_S)
    sitemap_task = fetch_sitemap_fn(base, SITEMAP_TIMEOUT_S)
    lighthouse_task = fetch_lighthouse_fn(base, LIGHTHOUSE_TIMEOUT_S, lighthouse_api_key)

    robots_txt, sitemap_xml, lighthouse_raw = await asyncio.gather(
        robots_task, sitemap_task, lighthouse_task
    )

    sub_sitemap_xmls: list[str | None] | None = None
    if sitemap_xml:
        kind, locs = _classify_sitemap_document(sitemap_xml)
        if kind == _SITEMAP_INDEX and locs:
            # Tu lógica recursiva de sitemaps se mantiene intacta
            sub_tasks = [
                fetch_sub_sitemap_fn(sub_url, SITEMAP_TIMEOUT_S)
                for sub_url in locs[:MAX_SUB_SITEMAPS]
            ]
            sub_results = await asyncio.gather(*sub_tasks, return_exceptions=True)
            sub_sitemap_xmls = [
                res if not isinstance(res, Exception) else None for res in sub_results
            ]

    return evaluate_fetch(
        domain,
        page,
        robots_txt,
        sitemap_xml,
        lighthouse_raw,  # Pasamos el JSON crudo a la capa pura
        sub_sitemap_xmls=sub_sitemap_xmls,
        now=now,
    )


def _normalize_domain(domain: str) -> str:
    target = domain.strip()
    if target and "//" not in target:
        target = "https://" + target
    return target


# --------------------------------------------------------------------------- #
# Real requests-based runners
# --------------------------------------------------------------------------- #
async def _fetch_main_page(url: str, timeout: int) -> PageFetchOutcome:
    return await asyncio.to_thread(_sync_fetch_main_page, url, timeout)


def _sync_fetch_main_page(url: str, timeout: int) -> PageFetchOutcome:
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True)
    except requests.exceptions.RequestException as exc:
        return PageFetchOutcome(ok=False, error=str(exc))
    return PageFetchOutcome(
        ok=True,
        status_code=response.status_code,
        final_url=response.url,
        html=response.text,
        headers=dict(response.headers),
    )


async def _fetch_robots_txt(base_url: str, timeout: int) -> str | None:
    result = await asyncio.to_thread(fetch_robots_txt, base_url, timeout)
    return result["content"] if result.get("exists") else None


async def _fetch_sitemap_xml(base_url: str, timeout: int) -> str | None:
    return await asyncio.to_thread(_sync_fetch_sitemap_xml, base_url, timeout)


def _sync_fetch_sitemap_xml(base_url: str, timeout: int) -> str | None:
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    for path in _SITEMAP_PATHS:
        try:
            response = requests.get(origin + path, headers=DEFAULT_HEADERS, timeout=timeout)
        except requests.exceptions.RequestException:
            continue
        if response.status_code == 200 and response.text.strip():
            return response.text
    return None


async def _fetch_single_sitemap_xml(url: str, timeout: int) -> str | None:
    return await asyncio.to_thread(_sync_fetch_single_sitemap_xml, url, timeout)


def _sync_fetch_single_sitemap_xml(url: str, timeout: int) -> str | None:
    """Fetch one exact sub-sitemap URL (no candidate-path fallback, unlike the main sitemap)."""
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    except requests.exceptions.RequestException:
        return None
    if response.status_code == 200 and response.text.strip():
        return response.text
    return None


async def _fetch_lighthouse_api(url: str, timeout: int, api_key: str | None = None) -> dict | None:
    return await asyncio.to_thread(_sync_fetch_lighthouse_api, url, timeout, api_key)


def _sync_fetch_lighthouse_api(url: str, timeout: int, api_key: str | None) -> dict | None:
    """Consume la API de PageSpeed filtrando por SEO y Performance."""
    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {"url": url, "category": ["performance", "seo"], "strategy": "mobile"}
    if api_key:
        params["key"] = api_key

    try:
        response = requests.get(endpoint, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception:
        # En el diseño de fetch.py, los fallos de red periféricos degradan a None
        return None
