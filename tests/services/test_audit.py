"""Tests for the real background audit runner (backend/app/services/audit.py).

The engine is injected as a fake ``audit_runner`` (same DI shape as the rest of
the package) so no network/Chrome runs; persistence goes through the real
``save_audit_result`` against the same in-memory fake db used by
test_persistence.py. Covers the three real outcomes of an audit:

* reachable + is_lead resolved (True or False) -> lead ``completed`` with
  the denormalised summary,
* UNREACHABLE -> lead ``unreachable`` with a pending ``retry_at``,
* the runner (or persistence) crashing -> lead visibly ``failed``, never
  stuck "in progress".
"""

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from bson import ObjectId

from backend.app.audit_engine.models import (
    AuditResult,
    FetchResult,
    LeadViabilityResult,
    Reachability,
    WeightedScoreResult,
)
from backend.app.models.leads import (
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_IN_PROGRESS,
    STATUS_UNREACHABLE,
)
from backend.app.services.audit import run_audit_background
from backend.app.services.persistence import (
    AUDIT_RUNS_COLLECTION,
    SNAPSHOTS_COLLECTION,
    MongoSnapshotStore,
    leads_collection_name,
)


# --------------------------------------------------------------------------- #
# In-memory fakes (same minimal shape as test_persistence.py)
# --------------------------------------------------------------------------- #
class FakeCollection:
    def __init__(self) -> None:
        self.docs: list[dict] = []

    async def insert_one(self, doc):
        stored = dict(doc)
        stored.setdefault("_id", ObjectId())
        self.docs.append(stored)
        return SimpleNamespace(inserted_id=stored["_id"])

    async def find_one(self, filt):
        for d in self.docs:
            if all(d.get(k) == v for k, v in filt.items()):
                return dict(d)
        return None

    async def update_one(self, filt, update):
        for d in self.docs:
            if all(d.get(k) == v for k, v in filt.items()):
                d.update(update["$set"])
                return SimpleNamespace(matched_count=1)
        return SimpleNamespace(matched_count=0)


class ExplodingCollection(FakeCollection):
    async def insert_one(self, doc):
        raise RuntimeError("mongo down")


class FakeDB:
    def __init__(self) -> None:
        self._collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        return self._collections.setdefault(name, FakeCollection())


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
def make_audit(*, domain: str = "example.com", is_lead: bool = True, reachable: bool = True):
    now = datetime.now(timezone.utc)
    return AuditResult(
        domain=domain,
        reachability=Reachability.OK if reachable else Reachability.UNREACHABLE,
        retry_at=None if reachable else now + timedelta(hours=24),
        fetch=FetchResult(
            domain=domain,
            reachability=Reachability.OK if reachable else Reachability.UNREACHABLE,
            fetched_at=now,
        ),
        weighted_score=(
            WeightedScoreResult(final_score=72.5, tier="fair", breakdown=[]) if reachable else None
        ),
        lead_viability=(LeadViabilityResult(is_lead=is_lead, reason="test") if reachable else None),
        created_at=now,
    )


def make_runner(result=None, exc: Exception | None = None):
    """A fake run_audit that records its call and returns/raises on demand."""
    calls: dict = {}

    async def runner(domain, *, snapshot_store=None):
        calls["domain"] = domain
        calls["snapshot_store"] = snapshot_store
        if exc is not None:
            raise exc
        return result

    return runner, calls


def seed_lead(db: FakeDB, domain: str = "example.com"):
    leads = db[leads_collection_name()]
    inserted = asyncio.run(
        leads.insert_one({"domain": domain, "company": "Example", "status": STATUS_IN_PROGRESS})
    )
    return inserted.inserted_id


def run(lead_id, db, runner):
    asyncio.run(run_audit_background(lead_id, "example.com", db, audit_runner=runner))


def find_lead(db: FakeDB, lead_id):
    return asyncio.run(db[leads_collection_name()].find_one({"_id": lead_id}))


# --------------------------------------------------------------------------- #
# The three outcomes
# --------------------------------------------------------------------------- #
class TestCompleted:
    def test_reachable_lead_completes_with_summary(self):
        db = FakeDB()
        lead_id = seed_lead(db)
        runner, calls = make_runner(make_audit(is_lead=True))

        run(lead_id, db, runner)

        assert len(db[AUDIT_RUNS_COLLECTION].docs) == 1  # the run is archived
        lead = find_lead(db, lead_id)
        assert lead["status"] == STATUS_COMPLETED
        assert lead["geo_score"] == 72.5
        assert lead["tier"] == "fair"
        assert lead["is_lead"] is True
        assert lead["last_audit_id"] == str(db[AUDIT_RUNS_COLLECTION].docs[0]["_id"])
        assert calls["domain"] == "example.com"

    def test_reachable_non_lead_is_still_completed(self):
        # is_lead=False is a *resolved* outcome (site already solved), not a failure.
        db = FakeDB()
        lead_id = seed_lead(db)
        runner, _ = make_runner(make_audit(is_lead=False))

        run(lead_id, db, runner)

        lead = find_lead(db, lead_id)
        assert lead["status"] == STATUS_COMPLETED
        assert lead["is_lead"] is False

    def test_injects_mongo_snapshot_store_over_snapshots_collection(self):
        # The whole point of 8b's snapshot wiring: the runner must receive the
        # Mongo-backed store, not fall back to a fresh in-memory no-op.
        db = FakeDB()
        lead_id = seed_lead(db)
        runner, calls = make_runner(make_audit())

        run(lead_id, db, runner)

        store = calls["snapshot_store"]
        assert isinstance(store, MongoSnapshotStore)
        assert store._collection is db[SNAPSHOTS_COLLECTION]


class TestUnreachable:
    def test_unreachable_marks_retry_pending_not_completed(self):
        db = FakeDB()
        lead_id = seed_lead(db)
        runner, _ = make_runner(make_audit(reachable=False))

        run(lead_id, db, runner)

        assert len(db[AUDIT_RUNS_COLLECTION].docs) == 1  # the attempt is history too
        lead = find_lead(db, lead_id)
        assert lead["status"] == STATUS_UNREACHABLE
        assert lead["retry_at"] is not None  # queryable by a future retry job
        assert lead["geo_score"] == 0.0
        assert lead["tier"] is None


class TestFailed:
    def test_runner_crash_marks_lead_failed_not_in_progress(self, caplog):
        db = FakeDB()
        lead_id = seed_lead(db)
        runner, _ = make_runner(exc=RuntimeError("boom"))

        with caplog.at_level("ERROR"):
            run(lead_id, db, runner)

        assert db[AUDIT_RUNS_COLLECTION].docs == []  # nothing to archive
        lead = find_lead(db, lead_id)
        assert lead["status"] == STATUS_FAILED
        assert lead["updated_at"] is not None
        assert any("fallo inesperado" in r.message for r in caplog.records)

    def test_persistence_crash_also_marks_lead_failed(self, caplog):
        # The audit ran fine but Mongo blew up on save: same rule, no limbo.
        db = FakeDB()
        db._collections[AUDIT_RUNS_COLLECTION] = ExplodingCollection()
        lead_id = seed_lead(db)
        runner, _ = make_runner(make_audit())

        with caplog.at_level("ERROR"):
            run(lead_id, db, runner)

        lead = find_lead(db, lead_id)
        assert lead["status"] == STATUS_FAILED
