"""Tests for the read-only report assembly (backend/app/services/report.py).

Two layers, same split as test_persistence.py:

* pure builders (``assemble_report``, ``report_markdown`` and the ``_jsonable``
  sanitiser) — exercised over documents produced by the *real*
  ``audit_run_documents`` builder, so the assembly is tested against exactly
  the shapes persistence writes, not hand-invented dicts.
* the async shell (``load_audit_report``) — exercised against a minimal fake
  db (find_one by ``_id`` only), driven with ``asyncio.run``.
"""

import asyncio
from datetime import datetime, timezone

from bson import ObjectId

from backend.app.audit_engine.models import (
    AuditResult,
    CitabilityResult,
    Confidence,
    CwvSource,
    FetchResult,
    KeywordsResult,
    KeywordSuggestion,
    LeadViabilityResult,
    PerformanceResult,
    Reachability,
    SchemaResult,
    SecurityHeaders,
    SecurityResult,
    TechnicalResult,
    TechStackResult,
    WeightedDimension,
    WeightedScoreResult,
)
from backend.app.services.persistence import CATEGORY_COLLECTIONS, audit_run_documents
from backend.app.services.report import (
    _jsonable,
    assemble_report,
    load_audit_report,
    report_markdown,
)


# --------------------------------------------------------------------------- #
# Fixtures — a full audit split through the real persistence builder
# --------------------------------------------------------------------------- #
def make_fetch(domain: str = "example.com") -> FetchResult:
    return FetchResult(
        domain=domain,
        reachability=Reachability.OK,
        status_code=200,
        final_url=f"https://{domain}/",
        html="<html>hi</html>",
        fetched_at=datetime.now(timezone.utc),
    )


def make_full_audit(domain: str = "example.com") -> AuditResult:
    now = datetime.now(timezone.utc)
    return AuditResult(
        domain=domain,
        reachability=Reachability.OK,
        fetch=make_fetch(domain),
        tech_stack=TechStackResult(identified=True, cms="WordPress", confidence=Confidence.HIGH),
        technical=TechnicalResult(
            dimensions=[
                WeightedDimension(
                    name="indexabilidad",
                    score=80.0,
                    weight=0.5,
                    points=40.0,
                    findings=["robots.txt permite el rastreo"],
                )
            ],
            score=88.0,
        ),
        security=SecurityResult(version_known=True, headers=SecurityHeaders(hsts=True)),
        performance=PerformanceResult(
            source=CwvSource.LAB,
            lcp_ms=2000.0,
            inp_ms=150.0,
            cls=0.05,
            lighthouse_runs=3,
            snapshot_at=now,
        ),
        schema_org=SchemaResult(score=40.0, format="json-ld", detected_types=["LocalBusiness"]),
        keywords=KeywordsResult(
            signals={"title": "Example"},
            suggestions=[KeywordSuggestion(query="clinica dental valencia", source="title")],
        ),
        citability=CitabilityResult(score=55.0, blocks_analyzed=4),
        lead_viability=LeadViabilityResult(
            is_lead=True,
            reason="Hay margen de mejora",
            checked_dimensions={"technical": 88.0},
        ),
        weighted_score=WeightedScoreResult(
            final_score=72.5,
            tier="fair",
            breakdown=[
                WeightedDimension(
                    name="technical",
                    score=88.0,
                    weight=0.35,
                    points=30.8,
                    findings=["peso base 35/100"],
                )
            ],
        ),
        created_at=now,
    )


def make_lead(**overrides) -> dict:
    doc = {
        "_id": ObjectId(),
        "company": "Example",
        "domain": "example.com",
        "status": "completed",
    }
    doc.update(overrides)
    return doc


def split_audit(result: AuditResult, lead_id: ObjectId):
    """Run the real persistence split so the assembly sees stored shapes."""
    return audit_run_documents(result, lead_id=lead_id)


# --------------------------------------------------------------------------- #
# Fake db — find_one by _id, the only read the shell performs
# --------------------------------------------------------------------------- #
class FakeCollection:
    def __init__(self) -> None:
        self.docs: list[dict] = []

    async def find_one(self, filt: dict):
        for doc in self.docs:
            if all(doc.get(key) == value for key, value in filt.items()):
                return dict(doc)
        return None


class FakeDB:
    def __init__(self) -> None:
        self.collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        return self.collections.setdefault(name, FakeCollection())


def seeded_db(run_doc: dict, category_docs: dict[str, dict]) -> FakeDB:
    db = FakeDB()
    db["audit_runs"].docs.append(run_doc)
    for name, doc in category_docs.items():
        db[CATEGORY_COLLECTIONS[name]].docs.append(doc)
    return db


# --------------------------------------------------------------------------- #
# Pure assembly
# --------------------------------------------------------------------------- #
class TestAssembleReport:
    def test_everything_is_plain_json(self):
        lead = make_lead()
        run_doc, category_docs = split_audit(make_full_audit(), lead["_id"])

        report = assemble_report(lead, run_doc, category_docs)

        def assert_plain(value, path="report"):
            assert not isinstance(value, (ObjectId, datetime)), path
            if isinstance(value, dict):
                for key, child in value.items():
                    assert_plain(child, f"{path}.{key}")
            elif isinstance(value, list):
                for i, child in enumerate(value):
                    assert_plain(child, f"{path}[{i}]")

        assert_plain(report)

    def test_ids_scores_and_categories_are_wired(self):
        lead = make_lead()
        run_doc, category_docs = split_audit(make_full_audit(), lead["_id"])

        report = assemble_report(lead, run_doc, category_docs)

        assert report["lead"]["id"] == str(lead["_id"])
        assert report["audit"]["id"] == str(run_doc["_id"])
        assert report["score"]["final_score"] == 72.5
        assert report["score"]["tier"] == "fair"
        assert report["viability"]["is_lead"] is True
        assert set(report["categories"]) == set(CATEGORY_COLLECTIONS)
        # Category scores come from the run's reports map, detail from the doc.
        assert report["categories"]["technical"]["score"] == 88.0
        assert report["categories"]["schema_org"]["detail"]["format"] == "json-ld"
        # Storage-only keys never leak into the rendered detail.
        for category in report["categories"].values():
            assert category["detail"] is not None
            for key in ("_id", "audit_id", "domain", "computed_at"):
                assert key not in category["detail"]

    def test_missing_category_doc_degrades_to_null_detail(self):
        lead = make_lead()
        run_doc, category_docs = split_audit(make_full_audit(), lead["_id"])
        category_docs.pop("citability")  # orphan lost / never written

        report = assemble_report(lead, run_doc, category_docs)

        assert report["categories"]["citability"]["score"] == 55.0
        assert report["categories"]["citability"]["detail"] is None

    def test_jsonable_handles_nested_bson(self):
        oid = ObjectId()
        now = datetime(2026, 7, 7, 12, 0, 0)
        assert _jsonable({"a": [{"b": oid}], "c": now}) == {
            "a": [{"b": str(oid)}],
            "c": "2026-07-07T12:00:00",
        }


# --------------------------------------------------------------------------- #
# Markdown rendering
# --------------------------------------------------------------------------- #
class TestReportMarkdown:
    def _report(self) -> dict:
        lead = make_lead()
        run_doc, category_docs = split_audit(make_full_audit(), lead["_id"])
        return assemble_report(lead, run_doc, category_docs)

    def test_renders_score_tier_and_breakdown(self):
        markdown = report_markdown(self._report())
        assert "# Informe de auditoría GEO — Example" in markdown
        assert "**72.5 / 100**" in markdown
        assert "Aceptable (60-74)" in markdown
        assert "| SEO técnico | 88.0 | 35.0% | 30.8 |" in markdown

    def test_renders_gate1_categories_and_keywords(self):
        markdown = report_markdown(self._report())
        assert "## Viabilidad como lead (Gate 1)" in markdown
        assert "**Sí, es lead**" in markdown
        assert "### Datos estructurados (Schema.org) — 40.0/100" in markdown
        assert "clinica dental valencia" in markdown

    def test_tolerates_a_minimal_unreachable_report(self):
        # An UNREACHABLE run has no score, no viability, no categories.
        lead = make_lead()
        run_doc = {
            "_id": ObjectId(),
            "domain": "example.com",
            "reachability": "unreachable",
            "reports": {},
            "errors": ["fetch_site: timeout"],
            "created_at": datetime.now(timezone.utc),
        }
        report = assemble_report(lead, run_doc, {})
        markdown = report_markdown(report)
        assert "Informe de auditoría GEO" in markdown
        assert "fetch_site: timeout" in markdown
        assert "## Puntuación global" not in markdown


# --------------------------------------------------------------------------- #
# Async shell
# --------------------------------------------------------------------------- #
class TestLoadAuditReport:
    def test_full_round_trip(self):
        lead = make_lead()
        run_doc, category_docs = split_audit(make_full_audit(), lead["_id"])
        lead["last_audit_id"] = str(run_doc["_id"])
        db = seeded_db(run_doc, category_docs)

        report = asyncio.run(load_audit_report(db, lead))

        assert report is not None
        assert report["audit"]["id"] == str(run_doc["_id"])
        assert set(report["categories"]) == set(CATEGORY_COLLECTIONS)

    def test_lead_without_audit_returns_none(self):
        assert asyncio.run(load_audit_report(FakeDB(), make_lead())) is None

    def test_dangling_last_audit_id_returns_none(self):
        lead = make_lead(last_audit_id=str(ObjectId()))
        assert asyncio.run(load_audit_report(FakeDB(), lead)) is None

    def test_malformed_last_audit_id_returns_none(self):
        lead = make_lead(last_audit_id="not-an-objectid")
        assert asyncio.run(load_audit_report(FakeDB(), lead)) is None
