"""Tests for the audit orchestrator (audit_engine/orchestrator.py).

Two layers, tested separately (same shape as the rest of the package):

* The gates and the shared normalisers — pure, synchronous, no network —
  exercised with fixtures. Covers the severity-mix hygiene fix, the
  weakest-link-not-average rule, and the two distinct performance cases
  (measured-and-bad -> scored low vs. not-measurable -> excluded/renormalised
  and visible in the breakdown).
* :func:`run_audit` — the async shell — exercised with every submodule injected
  as a fake, so no real network/Chrome is hit. Driven with ``asyncio.run``
  directly (same style as test_security.py / test_tech_stack.py): happy path,
  UNREACHABLE immediate return, detect_tech_stack failure cascading to
  technical/security, total failure -> weighted_score=None, and Gate 2 computed
  even when is_lead=True.
"""

import asyncio
from datetime import datetime, timezone

from backend.app.audit_engine.models import (
    AuditStage,
    CitabilityResult,
    Confidence,
    CwvSource,
    FetchResult,
    KeywordsResult,
    PerformanceResult,
    Reachability,
    SchemaResult,
    ScoreTier,
    SecurityHeaders,
    SecurityResult,
    Severity,
    TechnicalResult,
    TechStackResult,
    Vulnerability,
)
from backend.app.audit_engine.orchestrator import (
    RETRY_AFTER,
    evaluate_lead_viability,
    evaluate_weighted_score,
    performance_score,
    run_audit,
    security_score,
)

# --------------------------------------------------------------------------- #
# Fixture builders
# --------------------------------------------------------------------------- #
FETCHED_AT = datetime(2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc)


def make_fetch(
    *, reachability: Reachability = Reachability.OK, fetched_at: datetime = FETCHED_AT
) -> FetchResult:
    return FetchResult(
        domain="example.com",
        reachability=reachability,
        status_code=200 if reachability == Reachability.OK else None,
        final_url="https://example.com/" if reachability == Reachability.OK else None,
        html="<html></html>" if reachability == Reachability.OK else None,
        fetched_at=fetched_at,
    )


def make_tech_stack() -> TechStackResult:
    return TechStackResult(identified=True, confidence=Confidence.HIGH)


def make_technical(score: float = 100.0) -> TechnicalResult:
    return TechnicalResult(dimensions=[], score=score)


def make_security(
    *, all_headers: bool = True, vulnerabilities: list[Vulnerability] | None = None
) -> SecurityResult:
    headers = SecurityHeaders(
        hsts=all_headers,
        csp=all_headers,
        x_content_type_options=all_headers,
        x_frame_options=all_headers,
        referrer_policy=all_headers,
        permissions_policy=all_headers,
    )
    vulns = vulnerabilities or []
    return SecurityResult(
        version_known=True,
        headers=headers,
        vulnerabilities=vulns,
        has_known_vulns=bool(vulns),
    )


def make_performance(
    *, lcp_ms: float | None = 1500.0, inp_ms: float | None = 100.0, cls: float | None = 0.05
) -> PerformanceResult:
    return PerformanceResult(
        source=CwvSource.LAB,
        lcp_ms=lcp_ms,
        inp_ms=inp_ms,
        cls=cls,
        lcp_source=CwvSource.LAB if lcp_ms is not None else None,
        inp_source=CwvSource.LAB if inp_ms is not None else None,
        cls_source=CwvSource.LAB if cls is not None else None,
        lighthouse_runs=3,
        snapshot_at=FETCHED_AT,
    )


def make_schema(score: float = 100.0) -> SchemaResult:
    return SchemaResult(score=score)


def make_citability(score: float = 80.0) -> CitabilityResult:
    return CitabilityResult(score=score)


def make_vuln(cve: str = "CVE-2024-0001", severity: Severity = Severity.CRITICAL) -> Vulnerability:
    return Vulnerability(
        cve_id=cve,
        severity=severity,
        product="WordPress",
        affected_version="6.4",
        source_url=f"https://nvd.nist.gov/vuln/detail/{cve}",
    )


# --------------------------------------------------------------------------- #
# Shared normalisers (pure)
# --------------------------------------------------------------------------- #
class TestSecurityScore:
    def test_all_headers_no_vulns_is_100(self):
        assert security_score(make_security(all_headers=True)) == 100.0

    def test_no_headers_is_zero(self):
        assert security_score(make_security(all_headers=False)) == 0.0

    def test_severity_mix_uses_worst_not_alphabetical(self):
        # Hygiene 1: max() over the enum values would compare "low" > "critical"
        # alphabetically and pick LOW; the explicit ranking must pick CRITICAL.
        mixed = make_security(
            all_headers=True,
            vulnerabilities=[
                make_vuln("CVE-1", Severity.LOW),
                make_vuln("CVE-2", Severity.CRITICAL),
            ],
        )
        assert security_score(mixed) == 0.0  # CRITICAL ceiling, not LOW's 70

        # Order must not matter, and a LOW-only list is NOT zeroed (proves the
        # distinction the buggy alphabetical max() would have erased).
        reversed_order = make_security(
            all_headers=True,
            vulnerabilities=[
                make_vuln("CVE-2", Severity.CRITICAL),
                make_vuln("CVE-1", Severity.LOW),
            ],
        )
        assert security_score(reversed_order) == 0.0
        low_only = make_security(
            all_headers=True, vulnerabilities=[make_vuln("CVE-1", Severity.LOW)]
        )
        assert security_score(low_only) == 70.0

    def test_unknown_severity_capped_cautiously(self):
        # WPScan CVEs carry Severity.UNKNOWN; a real-but-ungraded hole still caps.
        scan = make_security(
            all_headers=True, vulnerabilities=[make_vuln("CVE-9", Severity.UNKNOWN)]
        )
        assert security_score(scan) == 55.0


class TestPerformanceScore:
    def test_all_good_is_100(self):
        assert performance_score(make_performance(lcp_ms=1500, inp_ms=100, cls=0.05)) == 100.0

    def test_measured_and_bad_scores_low_not_excluded(self):
        # Hygiene 2: a real bad measurement scores near 0 on purpose (sales
        # argument), it is NOT treated as missing.
        score = performance_score(make_performance(lcp_ms=6000, inp_ms=800, cls=0.4))
        assert score == 0.0
        assert score is not None

    def test_not_measurable_returns_none(self):
        # Hygiene 2: no data at all is None (excluded), never 0.
        assert performance_score(make_performance(lcp_ms=None, inp_ms=None, cls=None)) is None

    def test_partial_metrics_average_over_present_only(self):
        # Only LCP measured (3100ms -> 80); INP/CLS missing are not counted as 0.
        assert performance_score(make_performance(lcp_ms=3100, inp_ms=None, cls=None)) == 80.0


# --------------------------------------------------------------------------- #
# Gate 1 — lead viability (pure)
# --------------------------------------------------------------------------- #
class TestGateOne:
    def test_all_dimensions_high_is_not_lead(self):
        result = evaluate_lead_viability(
            make_technical(95),
            make_security(all_headers=True),
            make_performance(lcp_ms=1500, inp_ms=100, cls=0.05),
            make_schema(95),
        )
        assert result.is_lead is False
        assert "Ya resuelto" in result.reason
        assert set(result.checked_dimensions) == {
            "technical",
            "security",
            "performance",
            "schema_org",
        }

    def test_weakest_link_rules_not_average(self):
        # Everything perfect except mediocre performance -> is_lead=True, even
        # though the AVERAGE of the four dimensions stays >= 90 (punto 2).
        result = evaluate_lead_viability(
            make_technical(100),
            make_security(all_headers=True),
            make_performance(lcp_ms=3100, inp_ms=350, cls=0.175),  # ~76.7
            make_schema(100),
        )
        assert result.is_lead is True
        assert "performance" in result.reason
        dims = result.checked_dimensions
        assert dims["performance"] < 90  # weakest link below threshold
        assert sum(dims.values()) / len(dims) >= 90  # ...yet the average would not flag it

    def test_critical_cve_makes_security_the_weakest_link(self):
        result = evaluate_lead_viability(
            make_technical(100),
            make_security(
                all_headers=True, vulnerabilities=[make_vuln(severity=Severity.CRITICAL)]
            ),
            make_performance(lcp_ms=1500, inp_ms=100, cls=0.05),
            make_schema(100),
        )
        assert result.is_lead is True
        assert result.checked_dimensions["security"] == 0.0
        assert "security" in result.reason


# --------------------------------------------------------------------------- #
# Gate 2 — weighted score (pure)
# --------------------------------------------------------------------------- #
def _weights(result) -> dict[str, float]:
    return {d.name: d.weight for d in result.breakdown}


class TestGateTwo:
    def test_all_categories_weights_and_final(self):
        result = evaluate_weighted_score(
            make_technical(80),
            make_security(all_headers=True),  # -> 100
            make_performance(lcp_ms=1500, inp_ms=100, cls=0.05),  # -> 100
            make_schema(60),
            make_citability(40),
        )
        w = _weights(result)
        assert w == {
            "technical": 0.35,
            "citability": 0.25,
            "performance": 0.20,
            "schema": 0.15,
            "security": 0.05,
        }
        assert round(sum(w.values()), 4) == 1.0
        # 80*.35 + 40*.25 + 100*.20 + 60*.15 + 100*.05 = 28 + 10 + 20 + 9 + 5 = 72
        assert result.final_score == 72.0
        assert result.tier == ScoreTier.FAIR

    def test_tier_boundaries(self):
        # 100 across the board -> Excellent; a single dimension check per tier.
        assert (
            evaluate_weighted_score(
                make_technical(100),
                make_security(all_headers=True),
                make_performance(),
                make_schema(100),
                make_citability(100),
            ).tier
            == ScoreTier.EXCELLENT
        )
        assert _tier_via_final(76.0) == ScoreTier.GOOD
        assert _tier_via_final(52.0) == ScoreTier.POOR
        assert _tier_via_final(16.0) == ScoreTier.CRITICAL

    def test_performance_not_measurable_excluded_and_visible(self):
        # Hygiene 2: unmeasurable performance is excluded, weight redistributed,
        # and STILL visible in the breakdown with weight=0 + a finding.
        result = evaluate_weighted_score(
            make_technical(80),
            make_security(all_headers=True),  # -> 100
            make_performance(lcp_ms=None, inp_ms=None, cls=None),
            make_schema(60),
            make_citability(40),
        )
        perf = next(d for d in result.breakdown if d.name == "performance")
        assert perf.weight == 0.0
        assert perf.points == 0.0
        assert any("excluida" in f and "rendimiento" in f for f in perf.findings)

        w = _weights(result)
        assert round(w["technical"], 4) == round(35 / 80, 4)  # 0.4375
        assert round(w["citability"], 4) == round(25 / 80, 4)  # 0.3125
        assert round(w["schema"], 4) == round(15 / 80, 4)  # 0.1875
        assert round(w["security"], 4) == round(5 / 80, 4)  # 0.0625
        assert round(sum(w.values()), 4) == 1.0
        # 80*.4375 + 40*.3125 + 60*.1875 + 100*.0625 = 35 + 12.5 + 11.25 + 6.25 = 65
        assert result.final_score == 65.0

    def test_measured_bad_vs_not_measurable_differ(self):
        # The two performance cases must NOT collapse: measured-bad drags the
        # score down (weight kept), not-measurable is excluded (higher score).
        bad = evaluate_weighted_score(
            make_technical(80),
            make_security(all_headers=True),
            make_performance(lcp_ms=6000, inp_ms=800, cls=0.4),  # -> 0
            make_schema(60),
            make_citability(40),
        )
        perf_bad = next(d for d in bad.breakdown if d.name == "performance")
        assert perf_bad.weight == 0.20  # measured -> still weighted
        assert perf_bad.score == 0.0  # ...and its 0 drags the total
        # 80*.35 + 40*.25 + 0*.20 + 60*.15 + 100*.05 = 28 + 10 + 0 + 9 + 5 = 52
        assert bad.final_score == 52.0
        assert bad.tier == ScoreTier.POOR

        not_measurable = evaluate_weighted_score(
            make_technical(80),
            make_security(all_headers=True),
            make_performance(lcp_ms=None, inp_ms=None, cls=None),
            make_schema(60),
            make_citability(40),
        )
        assert not_measurable.final_score == 65.0
        assert bad.final_score < not_measurable.final_score

    def test_all_categories_missing_returns_none(self):
        assert evaluate_weighted_score(None, None, None, None, None) is None

    def test_some_categories_missing_renormalises_and_flags(self):
        result = evaluate_weighted_score(make_technical(90), None, None, None, make_citability(50))
        w = _weights(result)
        assert round(w["technical"], 4) == round(35 / 60, 4)
        assert round(w["citability"], 4) == round(25 / 60, 4)
        assert w["performance"] == 0.0
        assert w["schema"] == 0.0
        assert w["security"] == 0.0
        sec = next(d for d in result.breakdown if d.name == "security")
        assert any("no disponible" in f for f in sec.findings)
        # 90*(35/60) + 50*(25/60) = 52.5 + 20.83 = 73.33
        assert result.final_score == 73.33


def _tier_via_final(final: float) -> ScoreTier:
    """Build a WeightedScoreResult whose final lands on ``final`` and read its tier.

    A single citability category (weight renormalises to 1.0) makes final_score
    equal to that category's score, so the tier boundary can be checked directly.
    """
    return evaluate_weighted_score(None, None, None, None, make_citability(final)).tier


# --------------------------------------------------------------------------- #
# run_audit — async shell, every submodule injected
# --------------------------------------------------------------------------- #
def make_fakes(
    fetch_result: FetchResult,
    *,
    tech_stack: TechStackResult | None = None,
    technical: TechnicalResult | None = None,
    security: SecurityResult | None = None,
    performance: PerformanceResult | None = None,
    schema: SchemaResult | None = None,
    keywords: KeywordsResult | None = None,
    citability: CitabilityResult | None = None,
) -> tuple[dict, dict]:
    """Build a full set of passing fake submodules + a call-log dict."""
    calls: dict[str, list] = {}

    def log(name, value):
        calls.setdefault(name, []).append(value)

    async def fake_fetch(domain):
        log("fetch", domain)
        return fetch_result

    async def fake_tech(fetch):
        log("tech", fetch)
        return tech_stack

    def fake_technical(fetch, stack):
        log("technical", (fetch, stack))
        return technical

    async def fake_security(fetch, stack):
        log("security", (fetch, stack))
        return security

    async def fake_performance(domain, fetch):
        log("performance", (domain, fetch))
        return performance

    async def fake_schema(fetch):
        log("schema", fetch)
        return schema

    def fake_keywords(fetch, schema_arg):
        log("keywords", (fetch, schema_arg))
        return keywords

    def fake_citability(fetch):
        log("citability", fetch)
        return citability

    fakes = dict(
        fetch_site=fake_fetch,
        detect_tech_stack=fake_tech,
        score_technical=fake_technical,
        scan_security=fake_security,
        measure_performance=fake_performance,
        validate_schema=fake_schema,
        suggest_keywords=fake_keywords,
        score_citability=fake_citability,
    )
    return fakes, calls


class TestRunAuditShell:
    def test_happy_path_runs_every_submodule_once(self):
        fakes, calls = make_fakes(
            make_fetch(),
            tech_stack=make_tech_stack(),
            technical=make_technical(80),
            security=make_security(all_headers=True),
            performance=make_performance(),
            schema=make_schema(70),
            keywords=KeywordsResult(),
            citability=make_citability(60),
        )
        result = asyncio.run(run_audit("example.com", **fakes))

        assert result.reachability == Reachability.OK
        assert result.retry_at is None
        assert result.tech_stack is not None
        assert result.technical.score == 80
        assert result.security is not None
        assert result.performance is not None
        assert result.schema_org is not None
        assert result.keywords is not None
        assert result.citability is not None
        assert result.lead_viability is not None
        assert result.weighted_score is not None
        assert result.errors == []
        # every submodule called exactly once
        assert {k: len(v) for k, v in calls.items()} == {
            "fetch": 1,
            "tech": 1,
            "technical": 1,
            "security": 1,
            "performance": 1,
            "schema": 1,
            "keywords": 1,
            "citability": 1,
        }

    def test_unreachable_returns_immediately(self):
        fetched_at = datetime(2026, 7, 5, 9, 30, 0, tzinfo=timezone.utc)
        fakes, calls = make_fakes(
            make_fetch(reachability=Reachability.UNREACHABLE, fetched_at=fetched_at),
            tech_stack=make_tech_stack(),
            performance=make_performance(),
        )
        result = asyncio.run(run_audit("down.example", **fakes))

        assert result.reachability == Reachability.UNREACHABLE
        # retry_at derives from the fetch timestamp, not a fresh now() (punto 7).
        assert result.retry_at == fetched_at + RETRY_AFTER
        assert result.tech_stack is None
        assert result.lead_viability is None
        assert result.weighted_score is None
        # no submodule beyond the fetch itself ran
        assert list(calls.keys()) == ["fetch"]

    def test_tech_stack_failure_cascades_to_technical_and_security(self):
        fakes, calls = make_fakes(
            make_fetch(),
            performance=make_performance(),
            schema=make_schema(70),
            citability=make_citability(60),
        )

        async def boom_tech(fetch):
            calls.setdefault("tech", []).append(fetch)
            raise RuntimeError("wappalyzer down")

        fakes["detect_tech_stack"] = boom_tech
        result = asyncio.run(run_audit("example.com", **fakes))

        assert result.tech_stack is None
        assert result.technical is None  # cascade: never scored
        assert result.security is None  # cascade: never scanned
        assert "technical" not in calls  # score_technical not called
        assert "security" not in calls  # scan_security not called
        # independent submodules still ran in parallel
        assert result.performance is not None
        assert result.schema_org is not None
        assert any("detect_tech_stack" in e for e in result.errors)
        assert any("score_technical" in e and "tech_stack" in e for e in result.errors)
        assert any("scan_security" in e and "tech_stack" in e for e in result.errors)
        # Gate 2 still computed over the available categories; Gate 1 -> lead.
        assert result.weighted_score is not None
        assert result.lead_viability.is_lead is True
        assert "no disponible" in result.lead_viability.reason

    def test_total_failure_yields_no_weighted_score(self):
        fetch = make_fetch()

        async def ok_fetch(domain):
            return fetch

        async def boom_async(*args):
            raise RuntimeError("x")

        def boom_sync(*args):
            raise RuntimeError("x")

        fakes = dict(
            fetch_site=ok_fetch,
            detect_tech_stack=boom_async,
            score_technical=boom_sync,
            scan_security=boom_async,
            measure_performance=boom_async,
            validate_schema=boom_async,
            suggest_keywords=boom_sync,
            score_citability=boom_sync,
        )
        result = asyncio.run(run_audit("example.com", **fakes))

        assert result.tech_stack is None
        assert result.technical is None
        assert result.security is None
        assert result.performance is None
        assert result.schema_org is None
        assert result.keywords is None
        assert result.citability is None
        assert result.weighted_score is None  # every category missing (punto 5)
        assert result.lead_viability.is_lead is True
        assert len(result.errors) >= 5

    def test_gate2_computed_even_when_is_lead(self):
        # A clearly-a-lead site (low scores everywhere) still gets a Gate 2 score
        # (punto 6 — this is the intentional change from the task-1 design).
        fakes, _ = make_fakes(
            make_fetch(),
            tech_stack=make_tech_stack(),
            technical=make_technical(30),
            security=make_security(all_headers=False),  # -> 0
            performance=make_performance(lcp_ms=6000, inp_ms=800, cls=0.4),  # -> 0
            schema=make_schema(20),
            keywords=KeywordsResult(),
            citability=make_citability(10),
        )
        result = asyncio.run(run_audit("example.com", **fakes))

        assert result.lead_viability.is_lead is True  # obviously a lead
        assert result.weighted_score is not None  # ...yet Gate 2 still ran
        # 30*.35 + 10*.25 + 0*.20 + 20*.15 + 0*.05 = 10.5 + 2.5 + 0 + 3 + 0 = 16
        assert result.weighted_score.final_score == 16.0
        assert result.weighted_score.tier == ScoreTier.CRITICAL


# --------------------------------------------------------------------------- #
# on_stage progress reporting (UI timeline)
# --------------------------------------------------------------------------- #
def full_fakes():
    """A complete passing fake set (happy path) for the stage tests."""
    fakes, _ = make_fakes(
        make_fetch(),
        tech_stack=make_tech_stack(),
        technical=make_technical(80),
        security=make_security(all_headers=True),
        performance=make_performance(),
        schema=make_schema(70),
        keywords=KeywordsResult(),
        citability=make_citability(60),
    )
    return fakes


class TestOnStageReporting:
    def test_happy_path_reports_engine_stages_in_pipeline_order(self):
        stages: list[AuditStage] = []

        async def on_stage(stage):
            stages.append(stage)

        result = asyncio.run(run_audit("example.com", on_stage=on_stage, **full_fakes()))

        # PERSISTENCE is deliberately absent: it belongs to the caller
        # (services/audit.py), the engine never persists.
        assert stages == [
            AuditStage.FETCH,
            AuditStage.TECH_STACK,
            AuditStage.TECHNICAL_ANALYSIS,
            AuditStage.CONTENT_ANALYSIS,
            AuditStage.GATE_1,
            AuditStage.GATE_2,
        ]
        assert result.errors == []

    def test_unreachable_reports_only_fetch(self):
        stages: list[AuditStage] = []

        async def on_stage(stage):
            stages.append(stage)

        fakes, _ = make_fakes(make_fetch(reachability=Reachability.UNREACHABLE))
        result = asyncio.run(run_audit("down.example", on_stage=on_stage, **fakes))

        assert stages == [AuditStage.FETCH]
        assert result.reachability == Reachability.UNREACHABLE

    def test_broken_reporter_never_aborts_the_audit(self):
        async def exploding(stage):
            raise RuntimeError("mongo down")

        result = asyncio.run(run_audit("example.com", on_stage=exploding, **full_fakes()))

        # The audit itself is intact; every reporter failure is an errors line.
        assert result.weighted_score is not None
        assert result.lead_viability is not None
        assert sum("on_stage" in e for e in result.errors) == 6

    def test_no_reporter_is_the_default_noop(self):
        result = asyncio.run(run_audit("example.com", **full_fakes()))
        assert result.errors == []


# --------------------------------------------------------------------------- #
# snapshot_store wiring (task 8b)
# --------------------------------------------------------------------------- #
class TestSnapshotStoreWiring:
    def test_default_measure_performance_receives_injected_store(self, monkeypatch):
        # The injected store must reach the *default* measure_performance path —
        # otherwise the Mongo-backed 48h cache of task 8b would be a silent
        # no-op (every real audit building its own empty InMemorySnapshotStore).
        received = {}

        async def fake_measure(domain, fetch, *, snapshot_store=None, **_):
            received["snapshot_store"] = snapshot_store
            return make_performance()

        monkeypatch.setattr(
            "backend.app.audit_engine.orchestrator._measure_performance", fake_measure
        )

        fakes, _ = make_fakes(
            make_fetch(),
            tech_stack=make_tech_stack(),
            technical=make_technical(80),
            security=make_security(),
            schema=make_schema(70),
            keywords=KeywordsResult(),
            citability=make_citability(60),
        )
        fakes.pop("measure_performance")  # exercise the default path
        store = object()  # SnapshotStore is a Protocol; identity is all that matters
        result = asyncio.run(run_audit("example.com", snapshot_store=store, **fakes))

        assert received["snapshot_store"] is store
        assert result.performance is not None
