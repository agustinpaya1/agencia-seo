"""Initial site fetch for the audit engine (diagram 3.1, step B).

Single source of the raw material every deterministic submodule reads: HTML,
response headers, robots.txt and the sitemap URL list. Reuses
scripts/fetch_page.py; no LLM involved.
"""

from .models import FetchResult


async def fetch_site(domain: str) -> FetchResult:
    """Fetch HTML + headers + robots.txt + sitemap for ``domain``.

    Wraps scripts/fetch_page.py. On no response / timeout, returns a
    :class:`FetchResult` with ``reachability=Reachability.UNREACHABLE`` and empty
    payload fields so the orchestrator can schedule a 24h retry without blocking.
    """
    raise NotImplementedError
