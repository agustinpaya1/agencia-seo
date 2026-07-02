"""Tests for the pure geo-schema checklist (audit_engine/schema_org.py).

These exercise :func:`evaluate_schema_blocks` — the pure, synchronous layer — on
real JSON-LD strings, with no network involved. The goal (task 2, point 4) is to
show the 12-check rubric works on actual data, not just that the signature is
wired up: one valid-and-complete page, one with a required field missing, and one
with malformed JSON-LD.
"""

import json

from backend.app.audit_engine.schema_org import evaluate_schema_blocks


def _check(result, cid):
    """Fetch a single SchemaCheck by its stable id."""
    for c in result.checks:
        if c.id == cid:
            return c
    raise AssertionError(f"check id not found: {cid} (have {[c.id for c in result.checks]})")


# --------------------------------------------------------------------------- #
# Fixtures — representative JSON-LD blocks
# --------------------------------------------------------------------------- #
COMPLETE_JSONLD = json.dumps({
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "Organization",
            "@id": "https://example.com/#org",
            "name": "Example Corp",
            "url": "https://example.com",
            "logo": {"@type": "ImageObject", "url": "https://example.com/logo.png"},
            "description": "We build example things.",
            "foundingDate": "2015-04-01",
            "sameAs": [
                "https://en.wikipedia.org/wiki/Example",
                "https://www.linkedin.com/company/example",
                "https://twitter.com/example",
                "https://github.com/example",
                "https://www.youtube.com/@example",
            ],
            "knowsAbout": ["SEO", "GEO", "Structured Data"],
        },
        {
            "@type": "WebSite",
            "url": "https://example.com",
            "name": "Example",
            "potentialAction": {
                "@type": "SearchAction",
                "target": "https://example.com/search?q={q}",
                "query-input": "required name=q",
            },
        },
        {
            "@type": "Article",
            "headline": "How GEO works",
            "datePublished": "2026-01-01",
            "dateModified": "2026-02-01",
            "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".summary"]},
            "author": {
                "@type": "Person",
                "name": "Jane Doe",
                "url": "https://example.com/authors/jane",
                "sameAs": "https://www.linkedin.com/in/janedoe",
                "jobTitle": "Head of SEO",
            },
        },
    ],
})

# Organization present but missing a required property (`logo`) and short on
# recommended props -> "basic", not "complete".
MISSING_REQUIRED_JSONLD = json.dumps({
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Bare Corp",
    "url": "https://bare.example",
})

# Syntactically broken JSON-LD (trailing comma, so json.loads raises).
MALFORMED_JSONLD = '{"@context": "https://schema.org", "@type": "Organization", "name": "Oops",}'


# --------------------------------------------------------------------------- #
# Case 1 — valid and complete
# --------------------------------------------------------------------------- #
class TestCompleteSchema:
    def test_shape_is_twelve_checks(self):
        result = evaluate_schema_blocks([COMPLETE_JSONLD], is_homepage=True)
        assert len(result.checks) == 12
        assert 0.0 <= result.score <= 100.0

    def test_valid_json_and_types_full(self):
        result = evaluate_schema_blocks([COMPLETE_JSONLD], is_homepage=True)
        assert result.json_ld_valid is True
        assert result.format == "json-ld"
        assert _check(result, "valid-json-and-types").points == 10.0

    def test_key_signals_present(self):
        result = evaluate_schema_blocks([COMPLETE_JSONLD], is_homepage=True)
        # Organization complete, 5 sameAs (unverified -> counted), full author,
        # WebSite+SearchAction, speakable, knowsAbout with 3 topics.
        assert _check(result, "organization-or-person-present").points == 15.0
        assert _check(result, "sameas-links").points == 15.0
        assert _check(result, "article-author-details").points == 10.0
        assert _check(result, "website-searchaction").points == 5.0
        assert _check(result, "speakable-property").points == 5.0
        assert _check(result, "knowsabout-topics").points == 5.0
        # Homepage -> breadcrumb is N/A and awarded full.
        assert _check(result, "breadcrumblist").points == 5.0
        assert result.score >= 85.0

    def test_sameas_resolution_penalizes_dead_links(self):
        # When the shell reports a dead sameAs, its 3 points drop off.
        url_status = {
            "https://en.wikipedia.org/wiki/Example": True,
            "https://www.linkedin.com/company/example": True,
            "https://twitter.com/example": True,
            "https://github.com/example": True,
            "https://www.youtube.com/@example": False,  # 404
        }
        result = evaluate_schema_blocks([COMPLETE_JSONLD], is_homepage=True, url_status=url_status)
        assert _check(result, "sameas-links").points == 12.0


# --------------------------------------------------------------------------- #
# Case 2 — a required field is absent
# --------------------------------------------------------------------------- #
class TestMissingRequiredField:
    def test_organization_is_basic_not_complete(self):
        result = evaluate_schema_blocks([MISSING_REQUIRED_JSONLD], is_homepage=True)
        org = _check(result, "organization-or-person-present")
        assert org.points == 10.0  # basic, because `logo` (required) is absent
        assert any("logo" in n for n in org.notes)

    def test_json_still_valid_but_score_lower(self):
        result = evaluate_schema_blocks([MISSING_REQUIRED_JSONLD], is_homepage=True)
        complete = evaluate_schema_blocks([COMPLETE_JSONLD], is_homepage=True)
        assert result.json_ld_valid is True
        assert _check(result, "sameas-links").points == 0.0
        assert _check(result, "knowsabout-topics").points == 0.0
        # The missing required field + absent sameAs/knowsAbout cost real points:
        # a bare Organization scores well below the complete page.
        assert result.score < complete.score
        assert result.score < 50.0


# --------------------------------------------------------------------------- #
# Case 3 — malformed JSON-LD
# --------------------------------------------------------------------------- #
class TestMalformedSchema:
    def test_valid_json_check_is_zero(self):
        result = evaluate_schema_blocks([MALFORMED_JSONLD], is_homepage=True)
        assert result.json_ld_valid is False
        assert _check(result, "valid-json-and-types").points == 0.0

    def test_format_still_json_ld_but_entities_unreadable(self):
        # A JSON-LD block *was* present (it just doesn't parse), so the format
        # check still credits JSON-LD, but no entity-level signal survives.
        result = evaluate_schema_blocks([MALFORMED_JSONLD], is_homepage=True)
        assert result.format == "json-ld"
        assert result.detected_types == []
        assert _check(result, "organization-or-person-present").points == 0.0


# --------------------------------------------------------------------------- #
# Empty page — no structured data at all
# --------------------------------------------------------------------------- #
def test_no_structured_data_floor():
    result = evaluate_schema_blocks([], is_homepage=True)
    assert result.format == "none"
    assert result.json_ld_valid is False
    # A no-schema homepage floors at 10: the breadcrumb is N/A on the homepage
    # (5) and "no deprecated schemas present" is vacuously clean (5). Everything
    # else is 0. This is the faithful rubric result, not a bug.
    assert result.score == 10.0
    assert _check(result, "breadcrumblist").points == 5.0
    assert _check(result, "no-deprecated-schemas").points == 5.0
    scored = [c for c in result.checks if c.points > 0]
    assert {c.id for c in scored} == {"breadcrumblist", "no-deprecated-schemas"}
