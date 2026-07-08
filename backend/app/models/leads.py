from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from ..audit_engine.models import AuditStage, Reachability


class LeadStatus(str, Enum):
    """Full pipeline-status vocabulary for a lead document.

    The first seven are the CRM funnel and are user-assignable (see
    :data:`EDITABLE_STATUSES`); ``unreachable`` and ``failed`` are set only by
    the audit engine — no existing status distinguished "site down, retry
    pending" or "audit crashed" from a finished audit. Lives here (not
    services/audit.py) so the persistence layer can build the unique partial
    index over it without a circular import.
    """

    LEAD = "lead"
    AUDIT = "audit"
    PROPOSAL = "proposal"
    ACTIVE = "active"
    COMPLETED = "completed"
    CHURNED = "churned"
    LOST = "lost"
    UNREACHABLE = "unreachable"
    FAILED = "failed"


# Statuses owned by the audit flow (task 8b), kept as plain strings because
# they are written raw into Mongo documents and compared against raw docs.
STATUS_IN_PROGRESS = LeadStatus.AUDIT.value
STATUS_COMPLETED = LeadStatus.COMPLETED.value
STATUS_UNREACHABLE = LeadStatus.UNREACHABLE.value
STATUS_FAILED = LeadStatus.FAILED.value

# Statuses a user may assign by hand (PUT /api/leads/{id}/status and the kanban
# drag & drop). unreachable/failed are engine verdicts, not manual moves.
EDITABLE_STATUSES: frozenset[LeadStatus] = frozenset(
    {
        LeadStatus.LEAD,
        LeadStatus.AUDIT,
        LeadStatus.PROPOSAL,
        LeadStatus.ACTIVE,
        LeadStatus.COMPLETED,
        LeadStatus.CHURNED,
        LeadStatus.LOST,
    }
)


def parse_editable_status(raw: str) -> LeadStatus | None:
    """Pure validation of a user-supplied status change.

    Returns the :class:`LeadStatus` when ``raw`` (stripped) is one of the
    user-assignable stages, ``None`` otherwise — including the engine-owned
    ``unreachable``/``failed``, which must never be set by hand.
    """
    try:
        status = LeadStatus(raw.strip())
    except ValueError:
        return None
    return status if status in EDITABLE_STATUSES else None


def parse_logo_url(raw: str) -> str | None:
    """Pure validation of a user-pasted logo URL.

    An ``http(s)://`` URL is accepted as-is (stripped); an empty/blank value
    normalises to ``""`` meaning "clear the logo, fall back to the initials
    placeholder"; anything else is invalid (``None``). There is no upload
    machinery behind this — it is a plain string the UI renders as <img src>.
    """
    value = raw.strip()
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value
    return None


class LeadNoteRequest(BaseModel):
    text: str


class LeadStatusRequest(BaseModel):
    status: str


class LeadLogoRequest(BaseModel):
    logo_url: str = ""


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
    # Last stage the background audit reported (services/audit.py). Kept after
    # the run finishes so a failed audit still shows where it stopped.
    current_stage: AuditStage | None = None
    # Optional pasted image URL for the media card; "" / None -> initials
    # placeholder. Validated by parse_logo_url, no file upload behind it.
    logo_url: str | None = None
