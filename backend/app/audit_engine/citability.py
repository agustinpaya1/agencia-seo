"""AI-citability wrapper.

Thin adapter over citability_scorer.py: it reuses the existing 5-weight
formula without rewriting it, and maps the output onto :class:`CitabilityResult`.
This is the 5th category of the final weighted score.
"""

from __future__ import annotations

from .citability_scorer import analyze_html_citability
from .models import CitabilityResult, FetchResult


def score_citability(fetch: FetchResult) -> CitabilityResult:
    """Score the page's AI citability by wrapping the existing scorer.

    Delegates to :func:`citability_scorer.analyze_html_citability` with the
    HTML from ``fetch`` (task 7, parte B: the scorer used to re-fetch the URL
    itself, which risked scoring a different snapshot of the page than the rest
    of the audit engine — now it scores exactly what ``fetch`` already has).
    """
    html = fetch.html or ""
    if not html:
        return CitabilityResult(notes=["Sin HTML disponible: no se pudo evaluar citabilidad."])

    report = analyze_html_citability(html, url=fetch.final_url or fetch.domain)

    return CitabilityResult(
        score=report["average_citability_score"],
        blocks_analyzed=report["total_blocks_analyzed"],
        optimal_length_passages=report["optimal_length_passages"],
        grade_distribution=report["grade_distribution"],
    )
