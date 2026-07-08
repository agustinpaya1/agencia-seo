"""Tests for Core Web Vitals (audit_engine/performance.py).

Two layers, tested separately (task 4, point 6):

* :func:`evaluate_performance` — pure, synchronous, no network — exercised
  directly with representative raw-run fixtures (with field data, without
  field data, a failed run).
* :func:`measure_performance` — the async shell — exercised with fake
  ``run_lighthouse``/``fetch_crux`` callables and an in-memory snapshot store,
  so no real Chrome/API call happens in the test suite. Driven with
  ``asyncio.run`` directly to avoid adding a pytest-asyncio dependency.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from backend.app.audit_engine.models import CwvSource, FetchResult, Reachability
from backend.app.audit_engine.performance import (
    CruxFieldData,
    InMemorySnapshotStore,
    LighthouseRun,
    evaluate_performance,
    measure_performance,
)


def make_fetch(
    *, domain: str = "example.com", final_url: str | None = "https://example.com/"
) -> FetchResult:
    return FetchResult(
        domain=domain,
        reachability=Reachability.OK,
        status_code=200,
        final_url=final_url,
        html="<html></html>",
        fetched_at=datetime.now(timezone.utc),
    )


# --------------------------------------------------------------------------- #
# Pure layer
# --------------------------------------------------------------------------- #
class TestEvaluatePerformancePure:
    def test_with_field_data_uses_crux_and_marks_source_field(self):
        runs = [
            LighthouseRun(lcp_ms=2000.0, inp_ms=150.0, cls=0.05),
            LighthouseRun(lcp_ms=2100.0, inp_ms=160.0, cls=0.06),
            LighthouseRun(lcp_ms=1900.0, inp_ms=140.0, cls=0.04),
        ]
        crux = CruxFieldData(lcp_ms=2200.0, inp_ms=180.0, cls=0.08)

        result = evaluate_performance(runs, crux)

        assert result.source == CwvSource.FIELD
        assert result.crux_available is True
        assert result.lcp_ms == 2200.0
        assert result.inp_ms == 180.0
        assert result.cls == 0.08
        assert result.lcp_source == CwvSource.FIELD
        assert result.inp_source == CwvSource.FIELD
        assert result.cls_source == CwvSource.FIELD
        assert result.lighthouse_runs == 3
        assert any("CrUX" in n for n in result.notes)

    def test_without_field_data_falls_back_to_lab_median(self):
        runs = [
            LighthouseRun(lcp_ms=2000.0, inp_ms=150.0, cls=0.05),
            LighthouseRun(lcp_ms=2400.0, inp_ms=170.0, cls=0.07),
            LighthouseRun(lcp_ms=1800.0, inp_ms=130.0, cls=0.03),
        ]

        result = evaluate_performance(runs, None)

        assert result.source == CwvSource.LAB
        assert result.crux_available is False
        assert result.lcp_ms == 2000.0  # median of 1800/2000/2400
        assert result.inp_ms == 150.0
        assert result.cls == 0.05
        assert result.lcp_source == CwvSource.LAB
        assert result.inp_source == CwvSource.LAB
        assert result.cls_source == CwvSource.LAB
        assert any("sin datos de tráfico real suficientes" in n for n in result.notes)

    def test_failed_run_is_excluded_from_median_and_noted(self):
        runs = [
            LighthouseRun(lcp_ms=2000.0, inp_ms=150.0, cls=0.05),
            LighthouseRun(lcp_ms=2400.0, inp_ms=170.0, cls=0.07),
            LighthouseRun(failed=True, error="timeout"),
        ]

        result = evaluate_performance(runs, None)

        assert result.lighthouse_runs == 3
        assert result.lcp_ms == 2200.0  # median of the 2 successful runs
        assert any("1/3 corrida(s) de Lighthouse fallaron" in n for n in result.notes)

    def test_crux_partial_data_fills_missing_metric_from_lab(self):
        runs = [
            LighthouseRun(lcp_ms=2000.0, inp_ms=150.0, cls=0.05),
            LighthouseRun(lcp_ms=2100.0, inp_ms=160.0, cls=0.06),
            LighthouseRun(lcp_ms=1900.0, inp_ms=140.0, cls=0.04),
        ]
        crux = CruxFieldData(
            lcp_ms=2200.0, inp_ms=None, cls=0.08
        )  # no INP data yet for this origin

        result = evaluate_performance(runs, crux)

        # LCP/CLS are real field data, INP falls back to the lab median: the whole
        # result must NOT claim FIELD — it is MIXED, tracked per metric.
        assert result.source == CwvSource.MIXED
        assert result.lcp_ms == 2200.0
        assert result.inp_ms == 150.0  # lab median fallback
        assert result.cls == 0.08
        assert result.lcp_source == CwvSource.FIELD
        assert result.inp_source == CwvSource.LAB
        assert result.cls_source == CwvSource.FIELD
        assert result.crux_available is True
        assert any("CrUX sin dato de INP" in n for n in result.notes)
        assert any("Fuentes mixtas por métrica" in n for n in result.notes)

    def test_all_runs_failed_and_no_field_data_degrades_without_crashing(self):
        runs = [
            LighthouseRun(failed=True, error="timeout"),
            LighthouseRun(failed=True, error="chrome crashed"),
            LighthouseRun(failed=True, error="timeout"),
        ]

        result = evaluate_performance(runs, None)

        assert result.source == CwvSource.LAB  # nothing measured -> degraded lab, never FIELD
        assert result.lcp_ms is None
        assert result.inp_ms is None
        assert result.cls is None
        assert result.lcp_source is None
        assert result.inp_source is None
        assert result.cls_source is None
        assert any("3/3 corrida(s) de Lighthouse fallaron" in n for n in result.notes)


# --------------------------------------------------------------------------- #
# Async shell — mocked Lighthouse/CrUX/snapshot store
# --------------------------------------------------------------------------- #
class TestMeasurePerformanceShell:
    def test_fresh_snapshot_short_circuits_lighthouse_and_crux(self):
        store = InMemorySnapshotStore()
        fresh = evaluate_performance(
            [LighthouseRun(lcp_ms=2000.0, inp_ms=150.0, cls=0.05)] * 3,
            None,
            now=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        asyncio.run(store.save("example.com", fresh))

        calls = {"lighthouse": 0, "crux": 0}

        async def fake_lighthouse(_url: str) -> LighthouseRun:
            calls["lighthouse"] += 1
            return LighthouseRun(lcp_ms=9999.0, inp_ms=9999.0, cls=0.9)

        async def fake_crux(_domain: str) -> CruxFieldData | None:
            calls["crux"] += 1
            return None

        result = asyncio.run(
            measure_performance(
                "example.com",
                make_fetch(),
                snapshot_store=store,
                run_lighthouse=fake_lighthouse,
                fetch_crux=fake_crux,
            )
        )

        assert result.from_snapshot is True
        assert result.lcp_ms == 2000.0  # untouched: came from the stored snapshot
        assert calls == {"lighthouse": 0, "crux": 0}

    def test_stale_snapshot_triggers_three_sequential_runs_and_saves(self):
        store = InMemorySnapshotStore()
        stale = evaluate_performance(
            [LighthouseRun(lcp_ms=1000.0, inp_ms=100.0, cls=0.01)] * 3,
            None,
            now=datetime.now(timezone.utc) - timedelta(hours=49),
        )
        asyncio.run(store.save("example.com", stale))

        concurrent = 0
        max_concurrent = 0
        call_count = 0

        async def fake_lighthouse(_url: str) -> LighthouseRun:
            nonlocal concurrent, max_concurrent, call_count
            call_count += 1
            concurrent += 1
            max_concurrent = max(max_concurrent, concurrent)
            await asyncio.sleep(0.01)  # would overlap with a second call if run in parallel
            concurrent -= 1
            return LighthouseRun(lcp_ms=2000.0, inp_ms=150.0, cls=0.05)

        async def fake_crux(_domain: str) -> CruxFieldData | None:
            return CruxFieldData(lcp_ms=2500.0, inp_ms=200.0, cls=0.1)

        result = asyncio.run(
            measure_performance(
                "example.com",
                make_fetch(),
                snapshot_store=store,
                run_lighthouse=fake_lighthouse,
                fetch_crux=fake_crux,
            )
        )

        assert call_count == 3
        assert max_concurrent == 1  # sequential, never overlapping (task 4, point 1)
        assert result.from_snapshot is False
        assert result.source == CwvSource.FIELD
        assert result.lcp_ms == 2500.0

        saved = asyncio.run(store.get("example.com"))
        assert saved is not None
        assert saved.lcp_ms == 2500.0

    def test_no_snapshot_store_reuse_means_repeat_calls_remeasure(self):
        # A fresh InMemorySnapshotStore() per call (the default when the caller
        # doesn't pass one) never has a hit, so it behaves like a no-op cache.
        calls = 0

        async def fake_lighthouse(_url: str) -> LighthouseRun:
            nonlocal calls
            calls += 1
            return LighthouseRun(lcp_ms=2000.0, inp_ms=150.0, cls=0.05)

        async def fake_crux(_domain: str) -> CruxFieldData | None:
            return None

        asyncio.run(
            measure_performance(
                "example.com",
                make_fetch(),
                run_lighthouse=fake_lighthouse,
                fetch_crux=fake_crux,
            )
        )
        asyncio.run(
            measure_performance(
                "example.com",
                make_fetch(),
                run_lighthouse=fake_lighthouse,
                fetch_crux=fake_crux,
            )
        )

        assert calls == 6  # 3 runs x 2 calls, no cross-call caching without a shared store
