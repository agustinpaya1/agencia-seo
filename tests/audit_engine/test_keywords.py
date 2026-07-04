"""Tests for the pure keyword suggester (audit_engine/keywords.py).

suggest_keywords is 100% pure and synchronous, so every case is built from a
FetchResult + SchemaResult fixture — no network. Covers: full on-page signal set
with a LocalBusiness combining service+location, a plain page with only
title/meta/H1 (no schema business type), and an empty page (no signals at all).
"""

from datetime import datetime, timezone

from backend.app.audit_engine.keywords import suggest_keywords
from backend.app.audit_engine.models import FetchResult, Reachability, SchemaResult


def make_fetch(html: str) -> FetchResult:
    return FetchResult(
        domain="example.com",
        reachability=Reachability.OK,
        status_code=200,
        final_url="https://example.com/",
        html=html,
        fetched_at=datetime.now(timezone.utc),
    )


def make_schema(detected_types: list[str] | None = None) -> SchemaResult:
    return SchemaResult(detected_types=detected_types or [])


LOCAL_BUSINESS_HTML = """
<html><head>
<title>Reparación de calderas | Fontanería Pérez</title>
<meta name="description" content="Reparamos calderas y averías urgentes. Servicio 24h en toda la zona.">
</head><body>
<h1>Fontaneros urgentes en Madrid</h1>
<address>Calle Mayor 12, Madrid</address>
</body></html>
"""

PLAIN_HTML = """
<html><head>
<title>About Us | Acme Corp</title>
<meta name="description" content="Acme Corp builds tools for developers everywhere.">
</head><body>
<h1>We build developer tools</h1>
</body></html>
"""


def test_local_business_combines_schema_type_and_location():
    result = suggest_keywords(make_fetch(LOCAL_BUSINESS_HTML), make_schema(["LocalBusiness"]))

    assert result.signals["title"] == "Reparación de calderas | Fontanería Pérez"
    assert result.signals["h1"] == "Fontaneros urgentes en Madrid"
    assert result.signals["schema_type"] == "negocio local"
    assert result.signals["location"] == "Calle Mayor 12, Madrid"

    sources = [s.source for s in result.suggestions]
    assert sources[0] == "location"
    combined = result.suggestions[0]
    assert combined.query == "negocio local en Calle Mayor 12, Madrid"

    # schema_type is folded into the combined "location" suggestion, not repeated
    # standalone, since both signals were available together.
    assert "schema_type" not in sources


def test_plain_page_without_local_business_type_has_no_location_signal():
    result = suggest_keywords(make_fetch(PLAIN_HTML), make_schema([]))

    assert result.signals["location"] is None
    assert result.signals["schema_type"] is None

    sources = {s.source for s in result.suggestions}
    assert sources == {"title", "h1", "meta"}
    titles = {s.query for s in result.suggestions if s.source == "title"}
    assert titles == {"About Us"}


def test_empty_page_yields_no_signals_and_no_suggestions():
    result = suggest_keywords(make_fetch(""), make_schema([]))

    assert all(v is None for v in result.signals.values())
    assert result.suggestions == []


def test_suggestions_are_deduplicated_and_capped():
    html = """
    <html><head><title>Tienda</title>
    <meta name="description" content="Tienda."></head>
    <body><h1>Tienda</h1></body></html>
    """
    result = suggest_keywords(make_fetch(html), make_schema(["Store"]))

    queries = [s.query.lower() for s in result.suggestions]
    assert len(queries) == len(set(queries))
    assert len(result.suggestions) <= 8
