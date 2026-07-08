"""Real background audit execution (task 8b — replaces ``mock_audit_background``).

Runs the deterministic engine (:func:`run_audit`) for one lead and persists
the outcome. This is the only place where the engine meets Mongo: the engine
itself never learns the database exists (same boundary as
``services/persistence.py``), it just receives the Mongo-backed snapshot store
through ``run_audit``'s ``snapshot_store`` parameter.

Lead ``status`` after an audit (the endpoint inserts the lead as
``audit`` = in progress):

* ``completed``   — reachable site, audit ran, ``is_lead`` resolved (True or
  False); the denormalised summary (geo_score/tier/is_lead) is on the lead.
* ``unreachable`` — the site did not respond; ``retry_at`` on the lead says
  when it is worth trying again. Not "completed": there is no score to show.
* ``failed``      — ``run_audit`` itself (or persisting its result) blew up
  unexpectedly; made visible instead of leaving the lead "in progress"
  forever.

While the audit runs, every :class:`AuditStage` the orchestrator reports is
written onto the lead as ``current_stage`` (plus PERSISTENCE, reported here
before saving) so the UI can render a live pipeline timeline. Progress writes
are best-effort: a failing write is logged, never fatal to the audit.

KNOWN DEBT (task 8b closing): this runs in-process via FastAPI BackgroundTasks.
If the process restarts mid-audit (Lighthouse can take minutes), that audit is
lost and its lead stays in ``audit`` until relaunched manually — there is no
queue or automatic retry beyond the UNREACHABLE ``retry_at``. Acceptable at the
current volume of new leads; an external queue (Celery/RQ) is a deliberate
later step, not something to slip in silently.
"""

import logging
from datetime import datetime

from ..audit_engine.models import AuditStage, Reachability
from ..audit_engine.orchestrator import run_audit
from ..models.leads import STATUS_COMPLETED, STATUS_FAILED, STATUS_UNREACHABLE
from .persistence import (
    SNAPSHOTS_COLLECTION,
    MongoSnapshotStore,
    leads_collection_name,
    save_audit_result,
)

logger = logging.getLogger(__name__)


async def run_audit_background(
    lead_id,
    domain: str,
    db,
    *,
    audit_runner=None,
    api_key: str | None = None,
) -> None:
    """Run the real audit for ``domain`` and leave the lead in a final status.

    Receives the whole ``db`` handle (persistence owns the collection names —
    it fans out into ``audit_runs`` + the ``audit_reports_*`` category
    collections). ``audit_runner`` is injectable for tests (defaults to the
    engine's :func:`run_audit`); it receives the Mongo-backed snapshot store so
    the <48h Core Web Vitals cache works across audits instead of being a
    per-call no-op.
    """
    audit_runner = audit_runner or run_audit
    leads = db[leads_collection_name()]

    async def on_stage(stage: AuditStage) -> None:
        # Best-effort progress marker for the UI timeline. Guarded here (in
        # addition to the orchestrator's own guard) so the direct PERSISTENCE
        # call below can never fail an otherwise healthy audit either.
        try:
            await leads.update_one({"_id": lead_id}, {"$set": {"current_stage": stage.value}})
        except Exception:
            logger.exception(
                "run_audit_background: no se pudo escribir current_stage=%s para lead=%s",
                stage.value,
                lead_id,
            )

    try:
        result = await audit_runner(
            domain,
            snapshot_store=MongoSnapshotStore(db[SNAPSHOTS_COLLECTION]),
            on_stage=on_stage,
            api_key=api_key,
        )
        await on_stage(AuditStage.PERSISTENCE)
        await save_audit_result(db, result, lead_id=lead_id)
        status = STATUS_COMPLETED if result.reachability == Reachability.OK else STATUS_UNREACHABLE
        await leads.update_one({"_id": lead_id}, {"$set": {"status": status}})
    except Exception:
        # run_audit guards every submodule internally, so this is a genuinely
        # unexpected crash (or Mongo failing on save). Whatever it was, the
        # lead must not stay "in progress" forever.
        logger.exception(
            "run_audit_background: fallo inesperado auditando domain=%s lead=%s",
            domain,
            lead_id,
        )
        try:
            await leads.update_one(
                {"_id": lead_id},
                {
                    "$set": {
                        "status": STATUS_FAILED,
                        "updated_at": datetime.now().strftime("%Y-%m-%d"),
                    }
                },
            )
        except Exception:
            logger.exception(
                "run_audit_background: no se pudo marcar el lead %s como failed",
                lead_id,
            )
