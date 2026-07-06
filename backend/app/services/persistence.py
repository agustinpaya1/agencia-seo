"""Mongo persistence for the audit engine.

The deterministic engine in ``audit_engine/`` never learns that Mongo exists
(same rule as tasks 4 and 6): all database access lives here, in ``services/``.
``services/audit.py`` calls :func:`save_audit_result` and injects
:class:`MongoSnapshotStore` into ``run_audit``; ``main.py`` runs
:func:`ensure_indexes` at startup.

Two things are persisted:

* **Core Web Vitals snapshots** — :class:`MongoSnapshotStore` implements the
  ``SnapshotStore`` Protocol from ``audit_engine/performance.py``. It is a pure
  <48h *cache*: one document per domain (unique index), the 48h freshness cut
  applied **in the query** (task 4 decision preserved), and a TTL index for
  housekeeping only (the Mongo TTL sweeper is ~60s-granular, so it is never
  relied on for correctness — the explicit ``$gte`` filter is). Every
  ``PerformanceResult`` is *also* archived in its category report below, so the
  snapshot collection losing old entries costs no analytics.

* **Audit runs, split by category** — :func:`save_audit_result` splits one
  :class:`AuditResult` into a light ``audit_runs`` document (orchestration
  fields, the reduced fetch metadata, the small score-less ``tech_stack`` and
  ``keywords`` results, and a ``reports`` map with ``{id, score}`` per scored
  category) plus one document per scorer category in its own
  ``audit_reports_*`` collection (:data:`CATEGORY_COLLECTIONS`), queryable by
  domain history without going through the parent run.

  The raw ``fetch.html`` / ``headers`` / ``robots_txt`` are NOT persisted
  anywhere: the engine only needs them live, nothing ever read them back, and
  dropping them pays off the old "corte A" append-only-full-html debt. What
  survives of the fetch is the closed metadata list in
  :data:`_FETCH_PERSISTED_FIELDS`.

  Insertion order is categories first, run last (see
  :func:`save_audit_result`): a crash in between leaves harmless orphan
  category documents that nothing references — never a run whose ``reports``
  map points at documents that don't exist.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from bson import ObjectId

from ..audit_engine.models import AuditResult, FetchResult, PerformanceResult
from ..audit_engine.orchestrator import performance_score, security_score
from ..audit_engine.performance import SNAPSHOT_MAX_AGE
from ..models.leads import STATUS_IN_PROGRESS, AuditSummary

logger = logging.getLogger(__name__)

AUDIT_RUNS_COLLECTION = "audit_runs"
SNAPSHOTS_COLLECTION = "performance_snapshots"

# One collection per scorer category, keyed by its AuditResult field name (the
# same keys the `reports` map uses). keywords/tech_stack are NOT here on
# purpose: they carry no score and stay embedded in the run document.
CATEGORY_COLLECTIONS: dict[str, str] = {
    "technical": "audit_reports_technical",
    "security": "audit_reports_security",
    "performance": "audit_reports_performance",
    "schema_org": "audit_reports_schema_org",
    "citability": "audit_reports_citability",
}

# The closed list of fetch fields that survive persistence. Everything else in
# FetchResult (html, headers, robots_txt) is live-only input for the scorers.
_FETCH_PERSISTED_FIELDS = {"status_code", "final_url", "sitemap_urls", "notes", "fetched_at"}


def leads_collection_name() -> str:
    """Name of the CRM leads collection (env-overridable, default ``leads``).

    The single source of truth for the name: ``dependencies.get_leads_collection``,
    ``ensure_indexes``, ``services/audit.py`` and the migration script all
    resolve it here instead of each re-reading the env var.
    """
    return os.getenv("MONGODB_LEADS_COLLECTION", "leads")


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


def fetch_metadata(fetch: FetchResult) -> dict:
    """The persisted projection of a fetch: metadata only, never the payloads.

    ``html``, ``headers`` and ``robots_txt`` are what the scorers consume live;
    persisting them was the old corte-A debt. ``FetchResult`` itself is not
    changed — the engine keeps its full in-memory shape.
    """
    return fetch.model_dump(mode="python", include=_FETCH_PERSISTED_FIELDS)


def _category_score(name: str, value) -> float | None:
    """The 0-100 score a category contributes to the run's ``reports`` map.

    technical/schema_org/citability carry their own ``score`` field;
    security/performance have no score of their own, so the orchestrator's
    shared normalisers (the same formulas both gates use — determinism intact)
    are applied here. ``None`` only for performance that ran but measured
    nothing (the one honest "no data" case).
    """
    if name == "security":
        return security_score(value)
    if name == "performance":
        return performance_score(value)
    return value.score


def audit_run_documents(
    result: AuditResult, *, lead_id=None, run_id=None
) -> tuple[dict, dict[str, dict]]:
    """Split one ``AuditResult`` into ``(run_doc, category_docs)``.

    Pure: ObjectIds are pre-generated here (including the run's own ``_id``,
    overridable via ``run_id`` so the migration can preserve legacy ids and
    keep ``leads.last_audit_id`` references intact), and the cross-references
    are already wired — ``run_doc["reports"][cat]["id"] ==
    category_docs[cat]["_id"]`` and ``category_docs[cat]["audit_id"] ==
    run_doc["_id"]``. The shell only inserts.

    ``category_docs`` is keyed by category name (:data:`CATEGORY_COLLECTIONS`
    keys); a category that did not run (``None`` on the result) produces no
    document and no ``reports`` entry, so an UNREACHABLE audit yields
    ``reports == {}`` and zero category docs. ``reports[cat]["score"]`` is
    ``None`` when the category ran but measured nothing (performance).

    ``reports`` ids are stored as native ObjectId (consistent with ``_id`` /
    ``lead_id`` and directly queryable): any future endpoint returning a raw
    run document will need a JSON encoder for them, and any future reader must
    re-attach ``timezone.utc`` to the naive datetimes pymongo returns (see
    ``_load_performance`` for the precedent).
    """
    run_doc = result.model_dump(mode="python")
    run_doc["_id"] = run_id if run_id is not None else ObjectId()
    if lead_id is not None:
        run_doc["lead_id"] = lead_id
    run_doc["fetch"] = fetch_metadata(result.fetch)

    reports: dict[str, dict] = {}
    category_docs: dict[str, dict] = {}
    for name in CATEGORY_COLLECTIONS:
        payload = run_doc.pop(name)
        if payload is None:  # submodule failed or never ran -> no doc, no entry
            continue
        doc = {
            "_id": ObjectId(),
            "audit_id": run_doc["_id"],
            "domain": result.domain,
            "computed_at": result.created_at,
        }
        doc.update(payload)  # flat payload; *Result fields don't collide (checked)
        category_docs[name] = doc
        reports[name] = {"id": doc["_id"], "score": _category_score(name, getattr(result, name))}
    run_doc["reports"] = reports
    return run_doc, category_docs


def audit_summary(result: AuditResult, audit_id) -> AuditSummary:
    """Denormalised summary written back onto the lead after an audit."""
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


def lead_filter(domain: str, lead_id=None) -> dict:
    """Match the lead to update: by ``_id`` when known (8b), else by domain."""
    if lead_id is not None:
        return {"_id": lead_id}
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
# Audit run persistence
# --------------------------------------------------------------------------- #
async def save_audit_result(db, result: AuditResult, *, lead_id=None):
    """Persist one audit: category docs first, then the run, then the lead summary.

    Returns the inserted run's ``_id``. The category-docs-before-run order is
    deliberate (module docstring): orphan category docs are harmless, dangling
    ``reports`` references would not be. The lead update is matched by ``_id``
    when ``lead_id`` is given (task 8b), otherwise by ``domain``; a
    non-matching update logs a warning instead of failing (8b guarantees the
    lead exists in practice).
    """
    run_doc, category_docs = audit_run_documents(result, lead_id=lead_id)
    for name, doc in category_docs.items():
        await db[CATEGORY_COLLECTIONS[name]].insert_one(doc)
    insert = await db[AUDIT_RUNS_COLLECTION].insert_one(run_doc)

    summary = audit_summary(result, insert.inserted_id)
    update = await db[leads_collection_name()].update_one(
        lead_filter(result.domain, lead_id),
        {"$set": summary.model_dump(mode="python")},
    )
    if update.matched_count == 0:
        logger.warning(
            "save_audit_result: no lead matched for domain=%s lead_id=%s; "
            "audit run %s was saved but its summary was not denormalised onto any lead",
            result.domain,
            lead_id,
            insert.inserted_id,
        )
    return insert.inserted_id


# --------------------------------------------------------------------------- #
# Index creation — run by main.py's lifespan before the app takes traffic (8b)
# --------------------------------------------------------------------------- #
async def ensure_indexes(db, *, leads_name: str | None = None) -> None:
    """Create the minimum indexes the persistence layer relies on.

    No ``lead_id`` index on ``audit_runs`` for now: nothing lists runs by lead
    (the denormalised ``leads.last_audit_id`` covers the one lookup that
    exists); add it when a "runs of this lead" query appears.
    """
    leads_name = leads_name or leads_collection_name()
    await db[AUDIT_RUNS_COLLECTION].create_index([("domain", 1), ("created_at", -1)])
    # Category reports: domain history (the compound's prefix also covers plain
    # domain lookups) + assembling one run's reports. No unique on audit_id:
    # one-doc-per-category is guaranteed by construction (audit_run_documents),
    # and a unique index would only add a write-failure mode.
    for collection_name in CATEGORY_COLLECTIONS.values():
        await db[collection_name].create_index([("domain", 1), ("computed_at", -1)])
        await db[collection_name].create_index("audit_id")
    await db[SNAPSHOTS_COLLECTION].create_index("domain", unique=True)
    # TTL: housekeeping only (sweeper is ~60s-granular; the $gte query is the
    # source of truth for freshness).
    await db[SNAPSHOTS_COLLECTION].create_index(
        "snapshot_at", expireAfterSeconds=int(SNAPSHOT_MAX_AGE.total_seconds())
    )
    # Partial index over `$type: date` keeps only leads with a real pending
    # retry (excludes the null retry_at of reachable ones), so a future retry job
    # can query "who is due" without scanning every lead (proposal §5).
    await db[leads_name].create_index(
        "retry_at", partialFilterExpression={"retry_at": {"$type": "date"}}
    )
    # At most one lead per domain may be in "audit" (in progress) at a time.
    # This is the real concurrency guard for POST /api/audit: the endpoint's
    # find_one pre-check is only a fast path (check-then-insert races); losing
    # the race surfaces as DuplicateKeyError on the insert -> 409.
    await db[leads_name].create_index(
        "domain", unique=True, partialFilterExpression={"status": STATUS_IN_PROGRESS}
    )
