"""Tests for the Mongo persistence layer (backend/app/services/persistence.py).

Two layers, mirroring the pure/async split of the audit engine (task 8, point 8):

* pure helpers (``snapshot_query``/``snapshot_document``/``audit_summary``/
  ``prospect_filter``/``audit_document``/``_load_performance``) — exercised
  directly, no Mongo.
* the async shells (``MongoSnapshotStore``, ``save_audit_result``,
  ``ensure_indexes``) — exercised against an in-memory fake collection injected
  in place of a real Mongo collection, driven with ``asyncio.run`` (no
  mongomock/testcontainers dependency, same approach as test_performance.py).

The fake only implements the handful of collection methods the module calls and
the ``$gte`` operator the 48h snapshot query needs — enough to assert control
flow, not a Mongo reimplementation. The real round-trip is verified manually
against the dev database.
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
from backend.app.audit_engine.performance import (
    SNAPSHOT_MAX_AGE,
    LighthouseRun,
    evaluate_performance,
)
from backend.app.services.persistence import (
    AUDITS_COLLECTION,
    SNAPSHOTS_COLLECTION,
    MongoSnapshotStore,
    _load_performance,
    audit_document,
    audit_summary,
    ensure_indexes,
    prospect_filter,
    save_audit_result,
    snapshot_document,
    snapshot_query,
)


# --------------------------------------------------------------------------- #
# In-memory fake collection / db
# --------------------------------------------------------------------------- #
def _matches(doc: dict, filt: dict) -> bool:
    for key, cond in filt.items():
        val = doc.get(key)
        if isinstance(cond, dict):
            for op, operand in cond.items():
                if op == "$gte":
                    if val is None or val < operand:
                        return False
                else:
                    raise NotImplementedError(f"fake collection: unsupported op {op}")
        elif val != cond:
            return False
    return True


class FakeCollection:
    def __init__(self) -> None:
        self.docs: list[dict] = []
        self.indexes: list[tuple] = []

    async def create_index(self, keys, **kwargs):
        self.indexes.append((keys, kwargs))
        return "idx"

    async def insert_one(self, doc):
        stored = dict(doc)
        stored["_id"] = ObjectId()
        self.docs.append(stored)
        return SimpleNamespace(inserted_id=stored["_id"])

    async def find_one(self, filt):
        for d in self.docs:
            if _matches(d, filt):
                return dict(d)
        return None

    async def replace_one(self, filt, replacement, upsert=False):
        for i, d in enumerate(self.docs):
            if _matches(d, filt):
                new = dict(replacement)
                new["_id"] = d["_id"]
                self.docs[i] = new
                return SimpleNamespace(matched_count=1, upserted_id=None)
        if upsert:
            new = dict(replacement)
            new["_id"] = ObjectId()
            self.docs.append(new)
            return SimpleNamespace(matched_count=0, upserted_id=new["_id"])
        return SimpleNamespace(matched_count=0, upserted_id=None)

    async def update_one(self, filt, update):
        for d in self.docs:
            if _matches(d, filt):
                d.update(update["$set"])
                return SimpleNamespace(matched_count=1)
        return SimpleNamespace(matched_count=0)


class FakeDB:
    def __init__(self) -> None:
        self._collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        return self._collections.setdefault(name, FakeCollection())


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
def make_perf(*, now: datetime | None = None):
    return evaluate_performance(
        [LighthouseRun(lcp_ms=2000.0, inp_ms=150.0, cls=0.05)] * 3, None, now=now
    )


def make_fetch(domain: str = "example.com", html: str = "<html>hi</html>") -> FetchResult:
    return FetchResult(
        domain=domain,
        reachability=Reachability.OK,
        status_code=200,
        final_url=f"https://{domain}/",
        html=html,
        fetched_at=datetime.now(timezone.utc),
    )


def make_audit(*, domain: str = "example.com", is_lead: bool = True, reachable: bool = True):
    now = datetime.now(timezone.utc)
    return AuditResult(
        domain=domain,
        reachability=Reachability.OK if reachable else Reachability.UNREACHABLE,
        retry_at=None if reachable else now + timedelta(hours=24),
        fetch=make_fetch(domain),
        weighted_score=(
            WeightedScoreResult(final_score=72.5, tier="moderate", breakdown=[])
            if is_lead
            else None
        ),
        lead_viability=(LeadViabilityResult(is_lead=is_lead, reason="test") if reachable else None),
        created_at=now,
    )


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #
class TestPureHelpers:
    def test_snapshot_query_applies_48h_cut_in_the_query(self):
        now = datetime(2026, 7, 4, 12, tzinfo=timezone.utc)
        q = snapshot_query("example.com", now=now)
        assert q["domain"] == "example.com"
        assert q["snapshot_at"] == {"$gte": now - SNAPSHOT_MAX_AGE}

    def test_snapshot_document_tags_the_domain(self):
        perf = make_perf()
        doc = snapshot_document("example.com", perf)
        assert doc["domain"] == "example.com"
        assert doc["lcp_ms"] == 2000.0

    def test_audit_document_keeps_full_fetch_html(self):
        doc = audit_document(make_audit())
        assert doc["fetch"]["html"] == "<html>hi</html>"  # corte A: append-only, full html

    def test_audit_document_attaches_optional_prospect_id(self):
        pid = ObjectId()
        assert audit_document(make_audit(), prospect_id=pid)["prospect_id"] == pid
        assert "prospect_id" not in audit_document(make_audit())

    def test_audit_summary_lead(self):
        audit = make_audit(is_lead=True)
        s = audit_summary(audit, "abc123")
        assert s.geo_score == 72.5
        assert s.tier == "moderate"
        assert s.is_lead is True
        assert s.reachability is Reachability.OK
        assert s.retry_at is None
        assert s.last_audit_id == "abc123"
        assert s.audit_date == audit.created_at.date().isoformat()

    def test_audit_summary_unreachable_degrades_without_score(self):
        audit = make_audit(is_lead=False, reachable=False)
        s = audit_summary(audit, "x")
        assert s.geo_score == 0.0
        assert s.tier is None
        assert s.is_lead is None
        assert s.reachability is Reachability.UNREACHABLE
        assert s.retry_at is not None  # queryable by the future retry job

    def test_prospect_filter_prefers_id_over_domain(self):
        assert prospect_filter("example.com") == {"domain": "example.com"}
        oid = ObjectId()
        assert prospect_filter("example.com", oid) == {"_id": oid}

    def test_load_performance_normalises_naive_snapshot_to_utc(self):
        # pymongo returns BSON dates naive; _load_performance must re-attach UTC (corte B).
        doc = snapshot_document("example.com", make_perf())
        doc["snapshot_at"] = doc["snapshot_at"].replace(tzinfo=None)
        doc["_id"] = ObjectId()
        loaded = _load_performance(doc)
        assert loaded.snapshot_at.tzinfo is timezone.utc
        assert loaded.lcp_ms == 2000.0


# --------------------------------------------------------------------------- #
# MongoSnapshotStore
# --------------------------------------------------------------------------- #
class TestMongoSnapshotStore:
    def test_save_then_get_returns_fresh_snapshot(self):
        store = MongoSnapshotStore(FakeCollection())
        asyncio.run(store.save("example.com", make_perf()))
        got = asyncio.run(store.get("example.com"))
        assert got is not None
        assert got.lcp_ms == 2000.0
        assert got.from_snapshot is False  # the shell flips this, not the store

    def test_get_ignores_snapshot_older_than_48h(self):
        store = MongoSnapshotStore(FakeCollection())
        stale = make_perf(now=datetime.now(timezone.utc) - timedelta(hours=49))
        asyncio.run(store.save("example.com", stale))
        assert asyncio.run(store.get("example.com")) is None

    def test_get_miss_returns_none(self):
        store = MongoSnapshotStore(FakeCollection())
        assert asyncio.run(store.get("nope.com")) is None

    def test_save_upserts_one_document_per_domain(self):
        collection = FakeCollection()
        store = MongoSnapshotStore(collection)
        asyncio.run(store.save("example.com", make_perf()))
        asyncio.run(store.save("example.com", make_perf()))
        assert len(collection.docs) == 1  # replaced, not appended


# --------------------------------------------------------------------------- #
# save_audit_result
# --------------------------------------------------------------------------- #
class TestSaveAuditResult:
    def test_appends_audit_and_denormalises_prospect_summary(self):
        db = FakeDB()
        audits, prospects = db[AUDITS_COLLECTION], db["prospects"]
        asyncio.run(prospects.insert_one({"domain": "example.com", "company": "Example"}))

        audit_id = asyncio.run(save_audit_result(audits, prospects, make_audit()))

        assert len(audits.docs) == 1
        p = asyncio.run(prospects.find_one({"domain": "example.com"}))
        assert p["geo_score"] == 72.5
        assert p["tier"] == "moderate"
        assert p["is_lead"] is True
        assert p["reachability"] is Reachability.OK
        assert p["last_audit_id"] == str(audit_id)

    def test_audits_collection_is_append_only(self):
        db = FakeDB()
        audits, prospects = db[AUDITS_COLLECTION], db["prospects"]
        asyncio.run(prospects.insert_one({"domain": "example.com", "company": "Example"}))

        asyncio.run(save_audit_result(audits, prospects, make_audit()))
        asyncio.run(save_audit_result(audits, prospects, make_audit()))

        assert len(audits.docs) == 2  # history kept, nothing overwritten

    def test_warns_when_no_prospect_matches_the_domain(self, caplog):
        # Task 7 higiene: a non-matching $set used to be a silent no-op. It still
        # doesn't raise (8b guarantees the prospect exists in practice), but it
        # must leave a trace instead of vanishing.
        db = FakeDB()
        audits, prospects = db[AUDITS_COLLECTION], db["prospects"]

        with caplog.at_level("WARNING"):
            audit_id = asyncio.run(
                save_audit_result(audits, prospects, make_audit(domain="ghost.com"))
            )

        assert len(audits.docs) == 1  # the audit itself is still saved
        assert any("ghost.com" in r.message for r in caplog.records)
        assert any(str(audit_id) in r.message for r in caplog.records)

    def test_matches_prospect_by_id_when_given(self):
        db = FakeDB()
        audits, prospects = db[AUDITS_COLLECTION], db["prospects"]
        inserted = asyncio.run(
            prospects.insert_one({"domain": "example.com", "company": "Example"})
        )
        pid = inserted.inserted_id

        asyncio.run(save_audit_result(audits, prospects, make_audit(), prospect_id=pid))

        assert audits.docs[-1]["prospect_id"] == pid
        p = asyncio.run(prospects.find_one({"_id": pid}))
        assert p["geo_score"] == 72.5


# --------------------------------------------------------------------------- #
# ensure_indexes
# --------------------------------------------------------------------------- #
class TestEnsureIndexes:
    def test_creates_the_minimum_index_set(self):
        db = FakeDB()
        asyncio.run(ensure_indexes(db, prospects_name="prospects"))

        audits = db[AUDITS_COLLECTION].indexes
        assert any(keys == [("domain", 1), ("created_at", -1)] for keys, _ in audits)

        snaps = db[SNAPSHOTS_COLLECTION].indexes
        assert any(keys == "domain" and kw.get("unique") for keys, kw in snaps)
        ttl = next(kw for keys, kw in snaps if keys == "snapshot_at")
        assert ttl["expireAfterSeconds"] == int(SNAPSHOT_MAX_AGE.total_seconds())

        prospects = db["prospects"].indexes
        assert any(keys == "retry_at" and "partialFilterExpression" in kw for keys, kw in prospects)
