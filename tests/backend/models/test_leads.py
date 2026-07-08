"""Tests for the Lead typed contract (backend/app/models/leads.py).

The model must accept the *current* raw lead dict shape the endpoints
already write (company/domain/status/geo_score/monthly_value/audit_date/notes)
and additionally carry the denormalised audit-summary fields task 8 introduces.
"""

from datetime import datetime, timezone

from backend.app.audit_engine.models import Reachability
from backend.app.models.leads import AuditSummary, Lead, ManualFinding


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
