"""Technology stack detection (diagram 3.2).

Future implementation: wappalyzer-next over the raw fetch, falling back to a
Playwright render when the static fingerprints are weak or contradictory.
"""

from .models import FetchResult, TechStackResult


async def detect_tech_stack(fetch: FetchResult) -> TechStackResult:
    """Detect CMS / frameworks / server tech from the fetched page.

    Async because weak static signatures may require rendering the DOM with
    Playwright (diagram 3.2). Flags ``behind_cdn`` when only the edge is visible
    and records a confidence level; unidentifiable stacks come back with
    ``identified=False``.
    """
    raise NotImplementedError
