"""Tests for the audit endpoint (backend/app/api/endpoints/audit.py).

First endpoint test in the repo, so it sets the pattern: FastAPI's TestClient
*without* entering the lifespan context (no real Mongo connection is opened),
the db handle and the leads collection dependency-overridden with in-memory
fakes, and the engine monkeypatched at ``backend.app.services.audit.run_audit``
— the endpoint itself is exercised for real, background task included
(TestClient runs BackgroundTasks inline before returning the response, so the
final lead state is assertable right after the POST).
"""

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from bson import ObjectId
from fastapi import BackgroundTasks, HTTPException
from fastapi.testclient import TestClient
from pymongo.errors import DuplicateKeyError

import backend.app.services.audit as audit_service
from backend.app.api.endpoints.audit import start_audit
from backend.app.audit_engine.models import (
    AuditResult,
    FetchResult,
    LeadViabilityResult,
    Reachability,
    WeightedScoreResult,
)
from backend.app.dependencies import get_db, get_leads_collection
from backend.app.main import app
from backend.app.models.audit import AuditRequest
from backend.app.models.leads import (
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    STATUS_UNREACHABLE,
)
from backend.app.services.persistence import AUDIT_RUNS_COLLECTION, leads_collection_name


# --------------------------------------------------------------------------- #
# In-memory fakes (same minimal shape as tests/services/test_audit.py)
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


class FakeDB:
    def __init__(self) -> None:
        self._collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        return self._collections.setdefault(name, FakeCollection())


def make_audit(domain: str, *, reachable: bool = True) -> AuditResult:
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
            WeightedScoreResult(final_score=61.0, tier="fair", breakdown=[]) if reachable else None
        ),
        lead_viability=(LeadViabilityResult(is_lead=True, reason="test") if reachable else None),
        created_at=now,
    )


@pytest.fixture()
def harness(monkeypatch):
    """TestClient + fake db/leads + run_audit stubbed at the service module."""
    db = FakeDB()
    leads = db[leads_collection_name()]
    app.dependency_overrides[get_leads_collection] = lambda: leads
    app.dependency_overrides[get_db] = lambda: db

    state = {"reachable": True}

    async def fake_run_audit(domain, *, snapshot_store=None, on_stage=None, api_key=None):
        return make_audit(domain, reachable=state["reachable"])

    monkeypatch.setattr(audit_service, "run_audit", fake_run_audit)

    yield SimpleNamespace(
        client=TestClient(app),
        db=db,
        leads=leads,
        runs=db[AUDIT_RUNS_COLLECTION],
        state=state,
    )
    app.dependency_overrides.clear()


# --------------------------------------------------------------------------- #
# POST /api/audit
# --------------------------------------------------------------------------- #
class TestStartAudit:
    def test_runs_real_audit_and_completes_lead(self, harness):
        resp = harness.client.post("/api/audit", json={"url": "https://example.com/pricing"})

        assert resp.status_code == 202
        body = resp.json()
        assert body["lead"]["domain"] == "example.com"

        # Background task already ran (TestClient executes it inline): the
        # lead went audit -> completed with the denormalised summary.
        assert len(harness.runs.docs) == 1
        [lead] = harness.leads.docs
        assert str(lead["_id"]) == body["lead"]["id"]
        assert lead["status"] == STATUS_COMPLETED
        assert lead["geo_score"] == 61.0
        assert lead["is_lead"] is True

    def test_unreachable_site_leaves_retry_pending(self, harness):
        harness.state["reachable"] = False

        resp = harness.client.post("/api/audit", json={"url": "https://example.com"})

        assert resp.status_code == 202
        [lead] = harness.leads.docs
        assert lead["status"] == STATUS_UNREACHABLE
        assert lead["retry_at"] is not None

    def test_second_request_while_in_flight_is_409(self, harness):
        harness.leads.docs.append(
            {"_id": ObjectId(), "domain": "example.com", "status": STATUS_IN_PROGRESS}
        )

        resp = harness.client.post("/api/audit", json={"url": "https://example.com"})

        assert resp.status_code == 409
        assert len(harness.leads.docs) == 1  # no duplicate lead
        assert harness.runs.docs == []  # no second audit launched

    def test_completed_lead_can_be_audited_again(self, harness):
        # The guard only blocks in-flight audits, not finished ones.
        harness.leads.docs.append(
            {"_id": ObjectId(), "domain": "example.com", "status": STATUS_COMPLETED}
        )

        resp = harness.client.post("/api/audit", json={"url": "https://example.com"})

        assert resp.status_code == 202
        assert len(harness.leads.docs) == 2

    def test_blank_url_is_400(self, harness):
        resp = harness.client.post("/api/audit", json={"url": "   "})
        assert resp.status_code == 400
        assert harness.leads.docs == []


# --------------------------------------------------------------------------- #
# Concurrency guard — the real race, not the sequential fast path
# --------------------------------------------------------------------------- #
class RacingCollection(FakeCollection):
    """Fake leads collection that (a) enforces the unique partial index on
    (domain, status="audit") like real Mongo, and (b) holds every find_one at a
    barrier so two requests both pass the pre-check before either inserts —
    the exact interleaving the fast-path guard alone cannot stop.
    """

    def __init__(self, barrier: asyncio.Barrier) -> None:
        super().__init__()
        self._barrier = barrier

    async def find_one(self, filt):
        result = await super().find_one(filt)
        await self._barrier.wait()  # both requests past the pre-check, none inserted yet
        return result

    async def insert_one(self, doc):
        if doc.get("status") == STATUS_IN_PROGRESS and any(
            d.get("domain") == doc.get("domain") and d.get("status") == STATUS_IN_PROGRESS
            for d in self.docs
        ):
            raise DuplicateKeyError("E11000 duplicate key error (unique partial index)")
        return await super().insert_one(doc)


class TestConcurrencyRace:
    def test_simultaneous_requests_one_wins_one_409(self):
        # start_audit is driven directly (TestClient serialises requests, so it
        # can't interleave them); the barrier guarantees both coroutines pass
        # find_one before either inserts. Only DuplicateKeyError -> 409 saves us.
        async def race():
            leads = RacingCollection(asyncio.Barrier(2))
            db = FakeDB()

            async def request():
                return await start_audit(
                    AuditRequest(url="https://example.com"),
                    BackgroundTasks(),
                    leads=leads,
                    db=db,
                )

            results = await asyncio.gather(request(), request(), return_exceptions=True)
            return leads, results

        leads, results = asyncio.run(race())

        accepted = [r for r in results if isinstance(r, dict)]
        conflicts = [r for r in results if isinstance(r, HTTPException)]
        assert len(accepted) == 1
        assert len(conflicts) == 1
        assert conflicts[0].status_code == 409
        assert len(leads.docs) == 1  # exactly one in-flight lead survived
