from datetime import datetime

from pydantic import BaseModel, Field

from ..audit_engine.models import Reachability

# Lead status vocabulary owned by the audit flow (task 8b). "audit" and
# "completed" predate it (see valid_statuses in api/endpoints/leads.py and
# the frontend Pipeline chips); "unreachable" and "failed" were added because no
# existing status distinguishes "site down, retry pending" or "audit crashed"
# from a finished audit. Lives here (not services/audit.py) so the persistence
# layer can build the unique partial index over it without a circular import.
STATUS_IN_PROGRESS = "audit"
STATUS_COMPLETED = "completed"
STATUS_UNREACHABLE = "unreachable"
STATUS_FAILED = "failed"


class LeadNoteRequest(BaseModel):
    text: str


class LeadStatusRequest(BaseModel):
    status: str


class LeadNote(BaseModel):
    """One dated CRM note, matching the dict the endpoints already push."""

    date: str
    text: str


class ManualFinding(BaseModel):
    """One dated consultant judgment call about the audited site itself.

    Distinct from :class:`LeadNote` (a CRM follow-up log, e.g. "called the
    client, no answer"): a manual finding is qualitative judgment about the
    site under audit (e.g. "photos are stock, zero trust signals") — exactly
    the kind of call the deterministic engine is designed not to make on its
    own (AGENTS.md, principio 0: no LLM in the scoring path).
    """

    date: str
    text: str


class AuditSummary(BaseModel):
    """Denormalised snapshot of the latest audit kept on the Lead document.

    These are exactly the fields ``save_audit_result`` (services/persistence.py,
    task 8) writes back onto the lead after an audit, so the leads
    list/sort endpoint never has to read the ``audit_runs`` collection. It is
    the subset of :class:`Lead` fields an audit run owns.
    """

    geo_score: float = 0.0
    tier: str | None = None
    is_lead: bool | None = None
    reachability: Reachability | None = None
    retry_at: datetime | None = None
    last_audit_id: str | None = None
    audit_date: str | None = None
    updated_at: str | None = None


class Lead(AuditSummary):
    """Typed contract for a CRM lead document (the ``leads`` collection).

    "lead" carries three distinct meanings in this codebase — keep them apart:

    1. **The entity** (this model / the ``leads`` collection): every audited
       company in the CRM, whatever pipeline stage it is in.
    2. **The CRM stage** ``status="lead"``: one value of the pipeline whitelist
       (lead/audit/proposal/active/churned/lost/completed), the default for a
       fresh record. Unrelated to the engine.
    3. **The Gate 1 verdict** ``is_lead`` (inherited from
       :class:`AuditSummary`): the deterministic engine's judgment that the
       audited site has enough margin of improvement to be worth pursuing.

    Mirrors the raw dict the existing endpoints already read/write (company,
    domain, status, monthly_value, notes) plus the denormalised audit-summary
    fields (inherited from :class:`AuditSummary`). The endpoints keep reading
    the raw dict for now; migrating them to this model is a future task.
    """

    company: str
    domain: str
    status: str = "lead"
    monthly_value: float = 0.0
    notes: list[LeadNote] = Field(default_factory=list)
    manual_findings: list[ManualFinding] = Field(default_factory=list)
