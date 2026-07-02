"""AI-citability wrapper.

Thin adapter over scripts/citability_scorer.py: it reuses the existing 5-weight
formula without rewriting it, and maps the output onto :class:`CitabilityResult`.
This is the 5th category of the final weighted score.
"""

from .models import CitabilityResult, FetchResult


def score_citability(fetch: FetchResult) -> CitabilityResult:
    """Score the page's AI citability by wrapping the existing scorer.

    Delegates to scripts/citability_scorer.py (unchanged) and adapts its
    page-level metrics into a :class:`CitabilityResult`.
    """
    raise NotImplementedError
