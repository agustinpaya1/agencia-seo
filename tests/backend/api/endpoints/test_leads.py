"""Tests for the CRM lead endpoints (backend/app/api/endpoints/leads.py).

Same harness pattern as test_audit.py: FastAPI's TestClient *without* entering
the lifespan context (no real Mongo connection), the leads collection
dependency-overridden with an in-memory fake. The fake here carries more
surface than the deliberately-minimal fakes of the other test files because
these endpoints need it: ``find().sort().to_list()`` for the list endpoint and
``find_one_and_update`` with ``$push``/``$set`` + ``ReturnDocument.AFTER`` for
note/status. ``services.core.PROPOSALS_DIR`` is monkeypatched to a tmp dir in
every test so ``has_pdf``/the PDF endpoint never touch the real
``~/.geo-prospects``.
"""

from types import SimpleNamespace

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

import backend.app.services.core as core
from backend.app.dependencies import get_leads_collection
from backend.app.main import app


# --------------------------------------------------------------------------- #
# In-memory fake collection with the surface the lead endpoints use
# --------------------------------------------------------------------------- #
class FakeCursor:
    def __init__(self, docs: list[dict]) -> None:
        self._docs = docs

    def sort(self, key: str, direction: int):
        self._docs = sorted(self._docs, key=lambda d: d.get(key), reverse=direction == -1)
        return self

    async def to_list(self, length: int) -> list[dict]:
        return [dict(d) for d in self._docs[:length]]


class FakeLeadsCollection:
    def __init__(self) -> None:
        self.docs: list[dict] = []

    def find(self, query: dict) -> FakeCursor:
        matching = [d for d in self.docs if all(d.get(k) == v for k, v in query.items())]
        return FakeCursor([dict(d) for d in matching])

    async def find_one(self, filt: dict):
        for d in self.docs:
            if all(d.get(k) == v for k, v in filt.items()):
                return dict(d)
        return None

    async def find_one_and_update(self, filt: dict, update: dict, return_document=None):
        for d in self.docs:
            if all(d.get(k) == v for k, v in filt.items()):
                for key, val in update.get("$push", {}).items():
                    d.setdefault(key, []).append(val)
                for key, val in update.get("$set", {}).items():
                    d[key] = val
                return dict(d)  # ReturnDocument.AFTER: the updated doc
        return None


def make_lead(**overrides) -> dict:
    doc = {
        "_id": ObjectId(),
        "company": "Example",
        "domain": "example.com",
        "status": "completed",
        "geo_score": 61.0,
        "monthly_value": 0,
        "audit_date": "2026-07-04",
        "updated_at": "2026-07-04",
        "notes": [],
    }
    doc.update(overrides)
    return doc


@pytest.fixture()
def harness(monkeypatch, tmp_path):
    leads = FakeLeadsCollection()
    app.dependency_overrides[get_leads_collection] = lambda: leads
    monkeypatch.setattr(core, "PROPOSALS_DIR", tmp_path)  # isolate from ~/.geo-prospects

    yield SimpleNamespace(client=TestClient(app), leads=leads, proposals_dir=tmp_path)
    app.dependency_overrides.clear()


# --------------------------------------------------------------------------- #
# GET /api/leads
# --------------------------------------------------------------------------- #
class TestListLeads:
    def test_empty_collection_returns_empty_list_and_zeroed_stats(self, harness):
        resp = harness.client.get("/api/leads")

        assert resp.status_code == 200
        body = resp.json()
        assert body["leads"] == []
        assert body["stats"]["total"] == 0

    def test_exposes_id_string_and_stats_shape(self, harness):
        lead = make_lead()
        harness.leads.docs.append(lead)

        body = harness.client.get("/api/leads").json()

        [item] = body["leads"]
        assert item["id"] == str(lead["_id"])
        assert "_id" not in item
        assert set(body["stats"]) == {"total", "active", "mrr", "pipeline", "avg_score", "avg_tier"}

    def test_filters_by_exact_status(self, harness):
        harness.leads.docs.append(make_lead(domain="a.com", status="active"))
        harness.leads.docs.append(make_lead(domain="b.com", status="lead"))

        body = harness.client.get("/api/leads", params={"status": "active"}).json()

        assert [item["domain"] for item in body["leads"]] == ["a.com"]

    def test_sort_score_is_ascending(self, harness):
        harness.leads.docs.append(make_lead(domain="high.com", geo_score=90.0))
        harness.leads.docs.append(make_lead(domain="low.com", geo_score=10.0))

        body = harness.client.get("/api/leads", params={"sort": "score"}).json()

        assert [item["domain"] for item in body["leads"]] == ["low.com", "high.com"]

    def test_sort_company_is_alphabetical(self, harness):
        harness.leads.docs.append(make_lead(domain="z.com", company="Zeta"))
        harness.leads.docs.append(make_lead(domain="a.com", company="Alfa"))

        body = harness.client.get("/api/leads", params={"sort": "company"}).json()

        assert [item["company"] for item in body["leads"]] == ["Alfa", "Zeta"]

    def test_sort_mrr_is_descending(self, harness):
        harness.leads.docs.append(make_lead(domain="small.com", monthly_value=100))
        harness.leads.docs.append(make_lead(domain="big.com", monthly_value=900))

        body = harness.client.get("/api/leads", params={"sort": "mrr"}).json()

        assert [item["domain"] for item in body["leads"]] == ["big.com", "small.com"]


# --------------------------------------------------------------------------- #
# GET /api/leads/{lead_id}
# --------------------------------------------------------------------------- #
class TestLeadDetail:
    def test_invalid_object_id_is_400(self, harness):
        assert harness.client.get("/api/leads/not-an-oid").status_code == 400

    def test_unknown_lead_is_404(self, harness):
        assert harness.client.get(f"/api/leads/{ObjectId()}").status_code == 404

    def test_returns_raw_doc_with_id_and_has_pdf(self, harness):
        lead = make_lead()
        harness.leads.docs.append(lead)

        resp = harness.client.get(f"/api/leads/{lead['_id']}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == str(lead["_id"])
        assert body["company"] == "Example"
        assert body["has_pdf"] is False  # tmp proposals dir is empty


# --------------------------------------------------------------------------- #
# POST /api/leads/{lead_id}/note
# --------------------------------------------------------------------------- #
class TestAddLeadNote:
    def test_pushes_dated_note_and_returns_updated_doc(self, harness):
        lead = make_lead()
        harness.leads.docs.append(lead)

        resp = harness.client.post(f"/api/leads/{lead['_id']}/note", json={"text": "Llamado"})

        assert resp.status_code == 200
        body = resp.json()
        assert body["notes"][-1]["text"] == "Llamado"
        assert body["notes"][-1]["date"]  # server-generated timestamp
        # The fake's stored doc was mutated too (real $push semantics).
        assert harness.leads.docs[0]["notes"][-1]["text"] == "Llamado"

    def test_blank_text_is_400(self, harness):
        lead = make_lead()
        harness.leads.docs.append(lead)

        resp = harness.client.post(f"/api/leads/{lead['_id']}/note", json={"text": "   "})

        assert resp.status_code == 400
        assert harness.leads.docs[0]["notes"] == []

    def test_unknown_lead_is_404(self, harness):
        resp = harness.client.post(f"/api/leads/{ObjectId()}/note", json={"text": "hola"})
        assert resp.status_code == 404


# --------------------------------------------------------------------------- #
# PUT /api/leads/{lead_id}/status
# --------------------------------------------------------------------------- #
class TestUpdateLeadStatus:
    def test_whitelisted_status_is_applied(self, harness):
        lead = make_lead(status="lead")
        harness.leads.docs.append(lead)

        resp = harness.client.put(f"/api/leads/{lead['_id']}/status", json={"status": "proposal"})

        assert resp.status_code == 200
        assert resp.json()["status"] == "proposal"
        assert harness.leads.docs[0]["status"] == "proposal"

    def test_status_outside_whitelist_is_400(self, harness):
        lead = make_lead()
        harness.leads.docs.append(lead)

        resp = harness.client.put(f"/api/leads/{lead['_id']}/status", json={"status": "nonsense"})

        assert resp.status_code == 400
        assert harness.leads.docs[0]["status"] == "completed"  # untouched

    def test_unknown_lead_is_404(self, harness):
        resp = harness.client.put(f"/api/leads/{ObjectId()}/status", json={"status": "lead"})
        assert resp.status_code == 404


# --------------------------------------------------------------------------- #
# GET /api/leads/{lead_id}/pdf
# --------------------------------------------------------------------------- #
class TestDownloadLeadPdf:
    def test_unknown_lead_is_404(self, harness):
        assert harness.client.get(f"/api/leads/{ObjectId()}/pdf").status_code == 404

    def test_lead_without_pdf_is_404(self, harness):
        lead = make_lead()
        harness.leads.docs.append(lead)

        assert harness.client.get(f"/api/leads/{lead['_id']}/pdf").status_code == 404

    def test_serves_pregenerated_pdf_from_filesystem(self, harness):
        lead = make_lead()
        harness.leads.docs.append(lead)
        pdf = harness.proposals_dir / "example.com-propuesta.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        resp = harness.client.get(f"/api/leads/{lead['_id']}/pdf")

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content == b"%PDF-1.4 fake"
