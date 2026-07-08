"""Tests for the Lead typed contract (backend/app/models/leads.py).

The model must accept the *current* raw lead dict shape the endpoints
already write (company/domain/status/geo_score/monthly_value/audit_date/notes)
and additionally carry the denormalised audit-summary fields task 8 introduces.
Also covers the pure validation helpers the endpoints delegate to:
``parse_editable_status`` (kanban drag & drop / PUT status) and
``parse_logo_url`` (media-card logo).
"""

from datetime import datetime, timezone

import pytest

from backend.app.audit_engine.models import AuditStage, Reachability
from backend.app.models.leads import (
    EDITABLE_STATUSES,
    AuditSummary,
    Lead,
    LeadStatus,
    ManualFinding,
    parse_editable_status,
    parse_logo_url,
)


def test_lead_validates_current_dict_shape():
    lead = Lead(
        **{
            "company": "Example",
            "domain": "example.com",
            "status": "audit",
            "geo_score": 85,  # int in the legacy dict -> coerced to float
            "monthly_value": 0,
            "audit_date": "2026-07-04",
            "notes": [{"date": "2026-07-04T10:00:00", "text": "Auditoría iniciada"}],
        }
    )

    assert lead.company == "Example"
    assert lead.geo_score == 85.0
    assert lead.notes[0].text == "Auditoría iniciada"
    # New summary fields default to "no audit yet" instead of failing validation.
    assert lead.tier is None
    assert lead.is_lead is None
    assert lead.reachability is None
    assert lead.retry_at is None
    assert lead.last_audit_id is None


def test_lead_coerces_reachability_and_new_fields():
    lead = Lead(
        company="X",
        domain="x.com",
        reachability="unreachable",
        retry_at=datetime(2026, 7, 5, tzinfo=timezone.utc),
        is_lead=False,
        tier="critical",
        last_audit_id="abc123",
    )

    assert lead.reachability is Reachability.UNREACHABLE
    assert lead.is_lead is False
    assert lead.tier == "critical"
    assert lead.last_audit_id == "abc123"


def test_audit_summary_fields_are_a_subset_of_lead():
    # Lead inherits AuditSummary, so the summary written back after an audit
    # is always a valid subset of the lead document.
    assert set(AuditSummary.model_fields) <= set(Lead.model_fields)


def test_lead_carries_progress_and_logo_fields_with_safe_defaults():
    lead = Lead(company="Example", domain="example.com")
    assert lead.current_stage is None
    assert lead.logo_url is None

    lead = Lead(
        company="Example",
        domain="example.com",
        current_stage="technical_analysis",  # raw string from Mongo -> coerced
        logo_url="https://example.com/logo.png",
    )
    assert lead.current_stage is AuditStage.TECHNICAL_ANALYSIS
    assert lead.logo_url == "https://example.com/logo.png"


class TestParseEditableStatus:
    @pytest.mark.parametrize("raw", [status.value for status in EDITABLE_STATUSES])
    def test_accepts_every_editable_status(self, raw):
        assert parse_editable_status(raw) is LeadStatus(raw)

    def test_strips_whitespace(self):
        assert parse_editable_status("  proposal  ") is LeadStatus.PROPOSAL

    @pytest.mark.parametrize("raw", ["nonsense", "", "   "])
    def test_rejects_values_outside_the_vocabulary(self, raw):
        assert parse_editable_status(raw) is None

    @pytest.mark.parametrize("raw", ["unreachable", "failed"])
    def test_rejects_engine_owned_statuses(self, raw):
        # They ARE valid LeadStatus values, but only the engine may set them —
        # a drag & drop / manual PUT must never move a lead there.
        assert LeadStatus(raw) is not None
        assert parse_editable_status(raw) is None


class TestParseLogoUrl:
    def test_accepts_http_and_https_stripped(self):
        assert parse_logo_url(" https://cdn.example.com/logo.png ") == (
            "https://cdn.example.com/logo.png"
        )
        assert parse_logo_url("http://example.com/a.jpg") == "http://example.com/a.jpg"

    def test_blank_clears_the_logo(self):
        assert parse_logo_url("") == ""
        assert parse_logo_url("   ") == ""

    @pytest.mark.parametrize("raw", ["ftp://x/logo.png", "javascript:alert(1)", "logo.png"])
    def test_rejects_non_http_schemes(self, raw):
        assert parse_logo_url(raw) is None


def test_manual_findings_default_empty_and_are_distinct_from_notes():
    lead = Lead(company="Example", domain="example.com")
    assert lead.manual_findings == []
    assert lead.notes == []

    lead = Lead(
        company="Example",
        domain="example.com",
        notes=[{"date": "2026-07-04", "text": "Llamé al cliente, no contestó"}],
        manual_findings=[
            ManualFinding(
                date="2026-07-04", text="Las fotos son de stock, cero señales de confianza"
            )
        ],
    )
    assert lead.notes[0].text == "Llamé al cliente, no contestó"
    assert lead.manual_findings[0].text == "Las fotos son de stock, cero señales de confianza"
