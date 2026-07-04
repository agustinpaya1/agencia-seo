"""Mongo persistence for the audit engine (task 8, persistence layer only).

The deterministic engine in ``audit_engine/`` never learns that Mongo exists
(same rule as tasks 4 and 6): all database access lives here, in ``services/``.
This module is *not* wired into FastAPI yet and does not replace
``mock_audit_background`` — that is task 8b. It only provides the persistence
primitives underneath.

Two things are persisted:

* **Core Web Vitals snapshots** — :class:`MongoSnapshotStore` implements the
  ``SnapshotStore`` Protocol from ``audit_engine/performance.py``. It is a pure
  <48h *cache*: one document per domain (unique index), the 48h freshness cut
  applied **in the query** (task 4 decision preserved), and a TTL index for
  housekeeping only (the Mongo TTL sweeper is ~60s-granular, so it is never
  relied on for correctness — the explicit ``$gte`` filter is). Every
  ``PerformanceResult`` is *also* archived inside its ``AuditResult`` below, so
  the snapshot collection losing old entries costs no analytics.

* **Full audit reports** — :func:`save_audit_result` appends the whole
  :class:`AuditResult` to the ``audits`` collection and denormalises a summary
  onto the prospect.

  KNOWN DEBT (conscious decision, task 8): ``audits`` is append-only with no
  retention policy, and each document embeds the full ``fetch.html`` of the
  page (corte A of the task-8 proposal — fidelity over size for now).
  Historical ``fetch.html`` growth is technical debt to revisit when there is
  real volume, *not* an oversight — truncating/dropping it is a future task.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from ..audit_engine.models import AuditResult, PerformanceResult
from ..audit_engine.performance import SNAPSHOT_MAX_AGE
from ..models.prospects import AuditSummary

logger = logging.getLogger(__name__)

AUDITS_COLLECTION = "audits"
SNAPSHOTS_COLLECTION = "performance_snapshots"


# --------------------------------------------------------------------------- #
# Pure helpers — query/document builders, unit-testable without Mongo
# --------------------------------------------------------------------------- #
def snapshot_query(domain: str, *, now: datetime | None = None) -> dict:
    """Filter for a fresh (<48h) snapshot of ``domain``.

    The 48h cut lives here, in the query, so the store filters by ``snapshot_at``
    directly instead of re-checking in the shell (SnapshotStore Protocol
    contract, task 4).
    """
    now = now or datetime.now(timezone.utc)
    return {"domain": domain, "snapshot_at": {"$gte": now - SNAPSHOT_MAX_AGE}}


def snapshot_document(domain: str, result: PerformanceResult) -> dict:
    """The document stored for a domain's snapshot (upserted, one per domain)."""
    doc = result.model_dump(mode="python")  # keeps datetimes as BSON dates
    doc["domain"] = domain
    return doc


def audit_document(result: AuditResult, *, prospect_id=None) -> dict:
    """The document appended to ``audits`` for one audit run.

    Stores the whole ``AuditResult`` including ``fetch.html`` (corte A: fidelity
    over size; append-only, see the module known-debt note).
    """
    doc = result.model_dump(mode="python")
    if prospect_id is not None:
        doc["prospect_id"] = prospect_id
    return doc


def audit_summary(result: AuditResult, audit_id) -> AuditSummary:
    """Denormalised summary written back onto the prospect after an audit."""
    ws = result.weighted_score
    lv = result.lead_viability
    day = result.created_at.date().isoformat()
    return AuditSummary(
        geo_score=ws.final_score if ws else 0.0,
        tier=ws.tier if ws else None,
        is_lead=lv.is_lead if lv else None,
        reachability=result.reachability,
        retry_at=result.retry_at,
        last_audit_id=str(audit_id),
        audit_date=day,
        updated_at=day,
    )


def prospect_filter(domain: str, prospect_id=None) -> dict:
    """Match the prospect to update: by ``_id`` when known (8b), else by domain."""
    if prospect_id is not None:
        return {"_id": prospect_id}
    return {"domain": domain}


def _load_performance(doc: dict) -> PerformanceResult:
    """Rebuild a PerformanceResult from a stored snapshot document.

    Drops Mongo-only keys and normalises ``snapshot_at`` back to tz-aware UTC:
    pymongo returns BSON dates as *naive* datetimes, but the rest of the engine
    works in ``timezone.utc`` (corte B).
    """
    data = {k: v for k, v in doc.items() if k not in ("_id", "domain")}
    snap = data.get("snapshot_at")
    if isinstance(snap, datetime) and snap.tzinfo is None:
        data["snapshot_at"] = snap.replace(tzinfo=timezone.utc)
    return PerformanceResult(**data)


# --------------------------------------------------------------------------- #
# Snapshot store — Mongo-backed SnapshotStore (performance.py Protocol)
# --------------------------------------------------------------------------- #
class MongoSnapshotStore:
    """<48h Core Web Vitals cache backed by the ``performance_snapshots`` collection.

    Structural implementation of ``audit_engine.performance.SnapshotStore``:
    ``get`` enforces the 48h window in the query, ``save`` upserts one document
    per domain. Injected into ``measure_performance`` by task 8b; this module
    only depends on the Protocol, never the other way around.
    """

    def __init__(self, collection) -> None:
        self._collection = collection

    async def get(self, domain: str) -> PerformanceResult | None:
        doc = await self._collection.find_one(snapshot_query(domain))
        if doc is None:
            return None
        return _load_performance(doc)

    async def save(self, domain: str, result: PerformanceResult) -> None:
        await self._collection.replace_one(
            {"domain": domain}, snapshot_document(domain, result), upsert=True
        )


# --------------------------------------------------------------------------- #
# Full audit report persistence
# --------------------------------------------------------------------------- #
async def save_audit_result(audits, prospects, result: AuditResult, *, prospect_id=None):
    """Append the full audit to ``audits`` and denormalise a summary onto the prospect.

    Returns the inserted audit's ``_id``. The prospect update is matched by
    ``_id`` when ``prospect_id`` is given (task 8b), otherwise by ``domain``; a
    non-matching update is a silent no-op (8b guarantees the prospect exists).
    """
    insert = await audits.insert_one(audit_document(result, prospect_id=prospect_id))
    summary = audit_summary(result, insert.inserted_id)
    update = await prospects.update_one(
        prospect_filter(result.domain, prospect_id),
        {"$set": summary.model_dump(mode="python")},
    )
    if update.matched_count == 0:
        logger.warning(
            "save_audit_result: no prospect matched for domain=%s prospect_id=%s; "
            "audit %s was saved but its summary was not denormalised onto any prospect",
            result.domain,
            prospect_id,
            insert.inserted_id,
        )
    return insert.inserted_id


# --------------------------------------------------------------------------- #
# Index creation — called at startup by task 8b, not wired here
# --------------------------------------------------------------------------- #
async def ensure_indexes(db, *, prospects_name: str | None = None) -> None:
    """Create the minimum indexes the persistence layer relies on.

    Not called anywhere yet (task 8b runs it at app startup).
    """
    prospects_name = prospects_name or os.getenv("MONGODB_COLLECTION", "prospects")
    await db[AUDITS_COLLECTION].create_index([("domain", 1), ("created_at", -1)])
    await db[SNAPSHOTS_COLLECTION].create_index("domain", unique=True)
    # TTL: housekeeping only (sweeper is ~60s-granular; the $gte query is the
    # source of truth for freshness).
    await db[SNAPSHOTS_COLLECTION].create_index(
        "snapshot_at", expireAfterSeconds=int(SNAPSHOT_MAX_AGE.total_seconds())
    )
    # Partial index over `$type: date` keeps only prospects with a real pending
    # retry (excludes the null retry_at of reachable ones), so a future retry job
    # can query "who is due" without scanning every prospect (proposal §5).
    await db[prospects_name].create_index(
        "retry_at", partialFilterExpression={"retry_at": {"$type": "date"}}
    )
