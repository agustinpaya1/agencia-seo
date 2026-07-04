from datetime import datetime

from pydantic import BaseModel, Field

from ..audit_engine.models import Reachability


class NoteRequest(BaseModel):
    text: str


class StatusRequest(BaseModel):
    status: str


class ProspectNote(BaseModel):
    """One dated CRM note, matching the dict the endpoints already push."""

    date: str
    text: str


class ManualFinding(BaseModel):
    """One dated consultant judgment call about the audited site itself.

    Distinct from :class:`ProspectNote` (a CRM follow-up log, e.g. "called the
    client, no answer"): a manual finding is qualitative judgment about the
    site under audit (e.g. "photos are stock, zero trust signals") — exactly
    the kind of call the deterministic engine is designed not to make on its
    own (AGENTS.md, principio 0: no LLM in the scoring path).
    """

    date: str
    text: str


class AuditSummary(BaseModel):
    """Denormalised snapshot of the latest audit kept on the Prospect document.

    These are exactly the fields ``save_audit_result`` (services/persistence.py,
    task 8) writes back onto the prospect after an audit, so the leads
    list/sort endpoint never has to read the full ``audits`` collection. It is
    the subset of :class:`Prospect` fields an audit run owns.
    """

    geo_score: float = 0.0
    tier: str | None = None
    is_lead: bool | None = None
    reachability: Reachability | None = None
    retry_at: datetime | None = None
    last_audit_id: str | None = None
    audit_date: str | None = None
    updated_at: str | None = None


class Prospect(AuditSummary):
    """Typed contract for a CRM prospect document.

    Mirrors the raw dict the existing endpoints already read/write (company,
    domain, status, monthly_value, notes) plus the denormalised audit-summary
    fields this task introduces (inherited from :class:`AuditSummary`). The
    legacy endpoints keep reading the raw dict for now; migrating them to this
    model is task 8b.
    """

    company: str
    domain: str
    status: str = "lead"
    monthly_value: float = 0.0
    notes: list[ProspectNote] = Field(default_factory=list)
    manual_findings: list[ManualFinding] = Field(default_factory=list)
