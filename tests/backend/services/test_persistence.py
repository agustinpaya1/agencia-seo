"""Tests for the Mongo persistence layer (backend/app/services/persistence.py).

Two layers, mirroring the pure/async split of the audit engine (task 8, point 8):

* pure helpers (``snapshot_query``/``snapshot_document``/``fetch_metadata``/
  ``audit_run_documents``/``audit_summary``/``lead_filter``/
  ``_load_performance``) — exercised directly, no Mongo.
* the async shells (``MongoSnapshotStore``, ``save_audit_result``,
  ``ensure_indexes``) — exercised against an in-memory fake db/collection
  injected in place of real Mongo, driven with ``asyncio.run`` (no
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
    CitabilityResult,
    Confidence,
    CwvSource,
    FetchResult,
    KeywordsResult,
    LeadViabilityResult,
    PerformanceResult,
    Reachability,
    SchemaResult,
    SecurityHeaders,
    SecurityResult,
    TechnicalResult,
    TechStackResult,
    WeightedScoreResult,
)
from backend.app.audit_engine.performance import (
    SNAPSHOT_MAX_AGE,
    LighthouseRun,
    evaluate_performance,
)
from backend.app.models.leads import STATUS_IN_PROGRESS
from backend.app.services.persistence import (
    AUDIT_RUNS_COLLECTION,
    CATEGORY_COLLECTIONS,
    SNAPSHOTS_COLLECTION,
    MongoSnapshotStore,
    _load_performance,
    audit_run_documents,
    audit_summary,
    ensure_indexes,
    fetch_metadata,
    lead_filter,
    leads_collection_name,
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
    def __init__(self, name: str = "", insert_log: list[str] | None = None) -> None:
        self.name = name
        self.docs: list[dict] = []
        self.indexes: list[tuple] = []
        self._insert_log = insert_log

    async def create_index(self, keys, **kwargs):
        self.indexes.append((keys, kwargs))
        return "idx"

    async def insert_one(self, doc):
        stored = dict(doc)
        stored.setdefault("_id", ObjectId())  # respect pre-generated ids (builder)
        self.docs.append(stored)
        if self._insert_log is not None:
            self._insert_log.append(self.name)
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
    """Dict-of-collections fake with a shared insert log (order assertions)."""

    def __init__(self) -> None:
        self._collections: dict[str, FakeCollection] = {}
        self.insert_log: list[str] = []

    def __getitem__(self, name: str) -> FakeCollection:
        return self._collections.setdefault(name, FakeCollection(name, self.insert_log))


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
        headers={"server": "nginx"},
        robots_txt="User-agent: *\nAllow: /",
        sitemap_urls=[f"https://{domain}/sitemap.xml"],
        fetched_at=datetime.now(timezone.utc),
        notes=["ok"],
    )


def make_audit(*, domain: str = "example.com", is_lead: bool = True, reachable: bool = True):
    """Orchestration-only AuditResult: no category ran (all None)."""
    now = datetime.now(timezone.utc)
    return AuditResult(
        domain=domain,
        reachability=Reachability.OK if reachable else Reachability.UNREACHABLE,
        retry_at=None if reachable else now + timedelta(hours=24),
        fetch=make_fetch(domain),
        weighted_score=(
            WeightedScoreResult(final_score=72.5, tier="fair", breakdown=[]) if is_lead else None
        ),
        lead_viability=(LeadViabilityResult(is_lead=is_lead, reason="test") if reachable else None),
        created_at=now,
    )


def make_full_audit(
    *, domain: str = "example.com", performance: PerformanceResult | None = None
) -> AuditResult:
    """AuditResult with every category present (the split-happy-path fixture).

    Expected reports scores: technical 88.0 (own field), security 100.0 (all 6
    headers, no vulns -> orchestrator normaliser), performance 100.0 (all
    metrics good -> normaliser), schema_org 40.0, citability 55.0.
    """
    now = datetime.now(timezone.utc)
    performance = performance or PerformanceResult(
        source=CwvSource.LAB,
        lcp_ms=2000.0,
        inp_ms=150.0,
        cls=0.05,
        lighthouse_runs=3,
        snapshot_at=now,
    )
    return AuditResult(
        domain=domain,
        reachability=Reachability.OK,
        fetch=make_fetch(domain),
        tech_stack=TechStackResult(identified=True, cms="WordPress", confidence=Confidence.HIGH),
        technical=TechnicalResult(dimensions=[], score=88.0),
        security=SecurityResult(
            version_known=True,
            headers=SecurityHeaders(
                hsts=True,
                csp=True,
                x_content_type_options=True,
                x_frame_options=True,
                referrer_policy=True,
                permissions_policy=True,
            ),
        ),
        performance=performance,
        schema_org=SchemaResult(score=40.0),
        keywords=KeywordsResult(signals={"title": "Example"}, suggestions=[]),
        citability=CitabilityResult(score=55.0, blocks_analyzed=4),
        lead_viability=LeadViabilityResult(is_lead=True, reason="test"),
        weighted_score=WeightedScoreResult(final_score=72.5, tier="fair", breakdown=[]),
        created_at=now,
    )


def unmeasurable_performance() -> PerformanceResult:
    """Ran but produced no metric: the one case whose reports score is None."""
    return PerformanceResult(
        source=CwvSource.LAB,
        lcp_ms=None,
        inp_ms=None,
        cls=None,
        lighthouse_runs=3,
        snapshot_at=datetime.now(timezone.utc),
        notes=["lighthouse no devolvió métricas"],
    )


# --------------------------------------------------------------------------- #
# Pure helpers — snapshots
# --------------------------------------------------------------------------- #
class TestSnapshotHelpers:
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

    def test_load_performance_normalises_naive_snapshot_to_utc(self):
        # pymongo returns BSON dates naive; _load_performance must re-attach UTC (corte B).
        doc = snapshot_document("example.com", make_perf())
        doc["snapshot_at"] = doc["snapshot_at"].replace(tzinfo=None)
        doc["_id"] = ObjectId()
        loaded = _load_performance(doc)
        assert loaded.snapshot_at.tzinfo is timezone.utc
        assert loaded.lcp_ms == 2000.0


# --------------------------------------------------------------------------- #
# Pure helpers — fetch projection
# --------------------------------------------------------------------------- #
class TestFetchMetadata:
    def test_persists_only_the_closed_metadata_list(self):
        meta = fetch_metadata(make_fetch())
        assert set(meta) == {"status_code", "final_url", "sitemap_urls", "notes", "fetched_at"}
        assert meta["status_code"] == 200
        assert meta["sitemap_urls"] == ["https://example.com/sitemap.xml"]

    def test_never_persists_html_headers_or_robots(self):
        # The inverse of the old corte-A test (audit_document kept full html).
        meta = fetch_metadata(make_fetch(html="<html>huge page</html>"))
        assert "html" not in meta
        assert "headers" not in meta
        assert "robots_txt" not in meta


# --------------------------------------------------------------------------- #
# Pure helpers — the run/categories split
# --------------------------------------------------------------------------- #
class TestAuditRunDocuments:
    def test_splits_categories_with_cross_references(self):
        audit = make_full_audit()
        run_doc, cat_docs = audit_run_documents(audit)

        assert set(cat_docs) == set(CATEGORY_COLLECTIONS)
        assert set(run_doc["reports"]) == set(CATEGORY_COLLECTIONS)
        for name, doc in cat_docs.items():
            assert run_doc["reports"][name]["id"] == doc["_id"]
            assert doc["audit_id"] == run_doc["_id"]
            assert doc["domain"] == "example.com"
            assert doc["computed_at"] == audit.created_at
        # Category content no longer lives on the run document.
        for name in CATEGORY_COLLECTIONS:
            assert name not in run_doc

    def test_category_payload_is_flat(self):
        _, cat_docs = audit_run_documents(make_full_audit())
        assert cat_docs["technical"]["score"] == 88.0  # not nested under a key
        assert cat_docs["citability"]["blocks_analyzed"] == 4
        assert cat_docs["security"]["version_known"] is True

    def test_reports_scores_come_from_the_right_source(self):
        run_doc, _ = audit_run_documents(make_full_audit())
        reports = run_doc["reports"]
        assert reports["technical"]["score"] == 88.0  # own field
        assert reports["schema_org"]["score"] == 40.0  # own field
        assert reports["citability"]["score"] == 55.0  # own field
        assert reports["security"]["score"] == 100.0  # orchestrator normaliser
        assert reports["performance"]["score"] == 100.0  # orchestrator normaliser

    def test_performance_without_data_keeps_doc_but_null_score(self):
        audit = make_full_audit(performance=unmeasurable_performance())
        run_doc, cat_docs = audit_run_documents(audit)
        assert "performance" in cat_docs  # diagnostic value: the attempt is kept
        assert run_doc["reports"]["performance"]["score"] is None

    def test_missing_category_has_no_doc_and_no_reports_entry(self):
        audit = make_full_audit()
        audit = audit.model_copy(update={"citability": None})
        run_doc, cat_docs = audit_run_documents(audit)
        assert "citability" not in cat_docs
        assert "citability" not in run_doc["reports"]

    def test_unreachable_audit_yields_empty_reports_and_no_docs(self):
        run_doc, cat_docs = audit_run_documents(make_audit(reachable=False))
        assert run_doc["reports"] == {}
        assert cat_docs == {}
        assert run_doc["retry_at"] is not None

    def test_keywords_and_tech_stack_stay_embedded(self):
        run_doc, _ = audit_run_documents(make_full_audit())
        assert run_doc["keywords"]["signals"] == {"title": "Example"}
        assert run_doc["tech_stack"]["cms"] == "WordPress"

    def test_fetch_is_reduced_to_metadata(self):
        run_doc, _ = audit_run_documents(make_full_audit())
        assert "html" not in run_doc["fetch"]
        assert "headers" not in run_doc["fetch"]
        assert "robots_txt" not in run_doc["fetch"]
        assert run_doc["fetch"]["status_code"] == 200

    def test_run_id_and_lead_id_are_optional_and_respected(self):
        run_id, lead_id = ObjectId(), ObjectId()
        run_doc, cat_docs = audit_run_documents(make_full_audit(), lead_id=lead_id, run_id=run_id)
        assert run_doc["_id"] == run_id  # migration preserves legacy ids
        assert run_doc["lead_id"] == lead_id
        assert all(doc["audit_id"] == run_id for doc in cat_docs.values())

        bare, _ = audit_run_documents(make_full_audit())
        assert "lead_id" not in bare
        assert isinstance(bare["_id"], ObjectId)  # pre-generated by the builder


# --------------------------------------------------------------------------- #
# Pure helpers — summary + lead filter
# --------------------------------------------------------------------------- #
class TestAuditSummary:
    def test_audit_summary_lead(self):
        audit = make_audit(is_lead=True)
        s = audit_summary(audit, "abc123")
        assert s.geo_score == 72.5
        assert s.tier == "fair"
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

    def test_lead_filter_prefers_id_over_domain(self):
        assert lead_filter("example.com") == {"domain": "example.com"}
        oid = ObjectId()
        assert lead_filter("example.com", oid) == {"_id": oid}


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
    def test_fans_out_into_run_and_category_collections(self):
        db = FakeDB()
        leads = db[leads_collection_name()]
        asyncio.run(leads.insert_one({"domain": "example.com", "company": "Example"}))

        run_id = asyncio.run(save_audit_result(db, make_full_audit()))

        [run] = db[AUDIT_RUNS_COLLECTION].docs
        assert run["_id"] == run_id
        for name, collection_name in CATEGORY_COLLECTIONS.items():
            [doc] = db[collection_name].docs
            assert doc["audit_id"] == run_id
            assert run["reports"][name]["id"] == doc["_id"]

    def test_inserts_categories_before_the_run(self):
        # A crash in between must leave orphan category docs, never a run whose
        # reports map references documents that don't exist.
        db = FakeDB()
        asyncio.run(save_audit_result(db, make_full_audit()))

        assert db.insert_log[-1] == AUDIT_RUNS_COLLECTION
        assert set(db.insert_log[:-1]) == set(CATEGORY_COLLECTIONS.values())

    def test_denormalises_summary_onto_the_lead(self):
        db = FakeDB()
        leads = db[leads_collection_name()]
        asyncio.run(leads.insert_one({"domain": "example.com", "company": "Example"}))

        run_id = asyncio.run(save_audit_result(db, make_full_audit()))

        lead = asyncio.run(leads.find_one({"domain": "example.com"}))
        assert lead["geo_score"] == 72.5
        assert lead["tier"] == "fair"
        assert lead["is_lead"] is True
        assert lead["reachability"] is Reachability.OK
        assert lead["last_audit_id"] == str(run_id)

    def test_audit_runs_collection_is_append_only(self):
        db = FakeDB()
        leads = db[leads_collection_name()]
        asyncio.run(leads.insert_one({"domain": "example.com", "company": "Example"}))

        asyncio.run(save_audit_result(db, make_full_audit()))
        asyncio.run(save_audit_result(db, make_full_audit()))

        assert len(db[AUDIT_RUNS_COLLECTION].docs) == 2  # history kept
        assert len(db[CATEGORY_COLLECTIONS["technical"]].docs) == 2

    def test_unreachable_audit_saves_run_only(self):
        db = FakeDB()
        asyncio.run(save_audit_result(db, make_audit(reachable=False)))

        [run] = db[AUDIT_RUNS_COLLECTION].docs
        assert run["reports"] == {}
        for collection_name in CATEGORY_COLLECTIONS.values():
            assert db[collection_name].docs == []

    def test_warns_when_no_lead_matches_the_domain(self, caplog):
        # Task 7 higiene: a non-matching $set used to be a silent no-op. It still
        # doesn't raise (8b guarantees the lead exists in practice), but it
        # must leave a trace instead of vanishing.
        db = FakeDB()

        with caplog.at_level("WARNING"):
            run_id = asyncio.run(save_audit_result(db, make_full_audit(domain="ghost.com")))

        assert len(db[AUDIT_RUNS_COLLECTION].docs) == 1  # the run itself is saved
        assert any("ghost.com" in r.message for r in caplog.records)
        assert any(str(run_id) in r.message for r in caplog.records)

    def test_matches_lead_by_id_when_given(self):
        db = FakeDB()
        leads = db[leads_collection_name()]
        inserted = asyncio.run(leads.insert_one({"domain": "example.com", "company": "Example"}))
        lead_id = inserted.inserted_id

        asyncio.run(save_audit_result(db, make_full_audit(), lead_id=lead_id))

        assert db[AUDIT_RUNS_COLLECTION].docs[-1]["lead_id"] == lead_id
        lead = asyncio.run(leads.find_one({"_id": lead_id}))
        assert lead["geo_score"] == 72.5


# --------------------------------------------------------------------------- #
# ensure_indexes
# --------------------------------------------------------------------------- #
class TestEnsureIndexes:
    def test_creates_the_minimum_index_set(self):
        db = FakeDB()
        asyncio.run(ensure_indexes(db, leads_name="leads"))

        runs = db[AUDIT_RUNS_COLLECTION].indexes
        assert any(keys == [("domain", 1), ("created_at", -1)] for keys, _ in runs)

        # Every category collection: domain history compound + audit_id lookup,
        # and no unique on audit_id (uniqueness is by construction).
        for collection_name in CATEGORY_COLLECTIONS.values():
            cat = db[collection_name].indexes
            assert any(keys == [("domain", 1), ("computed_at", -1)] for keys, _ in cat)
            audit_id_kwargs = next(kw for keys, kw in cat if keys == "audit_id")
            assert not audit_id_kwargs.get("unique")

        snaps = db[SNAPSHOTS_COLLECTION].indexes
        assert any(keys == "domain" and kw.get("unique") for keys, kw in snaps)
        ttl = next(kw for keys, kw in snaps if keys == "snapshot_at")
        assert ttl["expireAfterSeconds"] == int(SNAPSHOT_MAX_AGE.total_seconds())

        leads = db["leads"].indexes
        assert any(keys == "retry_at" and "partialFilterExpression" in kw for keys, kw in leads)
        # The 409 concurrency guard: unique domain while an audit is in flight.
        assert any(
            keys == "domain"
            and kw.get("unique")
            and kw.get("partialFilterExpression") == {"status": STATUS_IN_PROGRESS}
            for keys, kw in leads
        )
