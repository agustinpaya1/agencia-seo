"""Tests for the citability_scorer.py wrapper (audit_engine/citability.py).

score_citability never fetches anything itself — it hands fetch.html straight
to scripts/citability_scorer.py's analyze_html_citability, so these tests only
need a FetchResult fixture, no network and no mocking of requests.
"""

from datetime import datetime, timezone

from backend.app.audit_engine.citability import score_citability
from backend.app.audit_engine.models import FetchResult, Reachability

# A body-heavy paragraph so at least one content block clears the >=20-word
# minimum citability_scorer.py requires to score a block at all.
_ARTICLE_HTML = """
<html><body>
<h1>What is GEO?</h1>
<p>GEO is a discipline that is defined as the practice of optimizing content so
that AI systems such as ChatGPT and Perplexity can find it, understand it, and
cite it directly in their answers to user questions, according to research from
Anthropic and other AI labs published in 2025.</p>
</body></html>
"""


def make_fetch(html: str | None) -> FetchResult:
    return FetchResult(
        domain="example.com",
        reachability=Reachability.OK,
        status_code=200,
        final_url="https://example.com/",
        html=html,
        fetched_at=datetime.now(timezone.utc),
    )


def test_scores_a_content_rich_page():
    result = score_citability(make_fetch(_ARTICLE_HTML))

    assert result.blocks_analyzed == 1
    assert result.score > 0
    assert sum(result.grade_distribution.values()) == 1


def test_empty_html_yields_zero_score_without_crashing():
    result = score_citability(make_fetch(""))

    assert result.blocks_analyzed == 0
    assert result.score == 0


def test_none_html_is_reported_as_unavailable():
    result = score_citability(make_fetch(None))

    assert result.blocks_analyzed == 0
    assert result.notes == ["Sin HTML disponible: no se pudo evaluar citabilidad."]
