"""Core Web Vitals with real reproducibility via snapshots (diagram 3.4).

Owns its own <48h snapshot: the goal is reproducibility of the *report*, not of
the physical measurement — nobody, not even Google, gets the same Lighthouse
number twice in a row (CrUX itself is a p75 over 28 days of real traffic, not a
single sample). CrUX field data is preferred when the domain has enough
real-user traffic; otherwise a Lighthouse lab estimate is stored, always tagged
with its source and timestamp so it is never presented as the real signal.

Two layers, kept apart on purpose (task 4, point 1), same shape as schema_org.py
and technical.py:

* :func:`evaluate_performance` — **pure and synchronous**. Receives the raw
  per-run Lighthouse measurements (LCP/INP/CLS, or a failed run) plus optional
  CrUX field data, and returns the resolved :class:`PerformanceResult`. The
  median of the successful runs is the lab estimate; provenance is tracked **per
  metric** (``lcp_source``/``inp_source``/``cls_source``) because CrUX can report
  a real field LCP while INP/CLS fall back to the lab median — the top-level
  ``source`` is then ``MIXED`` rather than overclaiming ``FIELD``. No Chrome, no
  network, trivially unit-testable.
* :func:`measure_performance` — the **async shell**. Checks the injected
  :class:`SnapshotStore` for a snapshot younger than 48h; if none exists it runs
  Lighthouse 3 times **sequentially** (not concurrently — parallel runs in the
  same process would contend for CPU/network and bias the measurement), queries
  CrUX, persists the fresh snapshot, and delegates the math to the pure layer.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import socket
import statistics
from collections.abc import Awaitable, Callable, Iterable, Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Protocol

import requests
from pydantic import BaseModel

from .models import CwvSource, FetchResult, PerformanceResult

SNAPSHOT_MAX_AGE = timedelta(hours=48)
_LIGHTHOUSE_RUN_COUNT = 3
_LIGHTHOUSE_TIMEOUT_S = 90  # per run; not in the design doc, our own cut (see task closing)
_CRUX_ENDPOINT = "https://chromeuiexperience.googleapis.com/v1/records:queryRecord"
_CRUX_TIMEOUT_S = 10


# --------------------------------------------------------------------------- #
# Raw inputs to the pure layer
# --------------------------------------------------------------------------- #
class LighthouseRun(BaseModel):
    """One raw Lighthouse measurement, or a failed run.

    ``inp_ms`` here is Total Blocking Time, used as the lab proxy for
    responsiveness: a default Lighthouse navigation run does not simulate real
    user interaction, so it cannot produce a genuine INP value (own cut, see
    task closing notes).
    """

    lcp_ms: float | None = None
    inp_ms: float | None = None
    cls: float | None = None
    failed: bool = False
    error: str | None = None


class CruxFieldData(BaseModel):
    """CrUX p75 field metrics for a domain/origin, when the API has enough traffic."""

    lcp_ms: float | None = None
    inp_ms: float | None = None
    cls: float | None = None


# --------------------------------------------------------------------------- #
# Pure layer
# --------------------------------------------------------------------------- #
def evaluate_performance(
    lighthouse_runs: Sequence[LighthouseRun],
    crux: CruxFieldData | None,
    *,
    now: datetime | None = None,
) -> PerformanceResult:
    """Resolve raw Lighthouse runs + optional CrUX field data into a PerformanceResult.

    Pure and synchronous: no Chrome, no network. ``lighthouse_runs`` are the raw
    per-run measurements (task 4, point 1) — the median of the *successful* ones
    becomes the lab estimate; failed runs are excluded from the median and
    reported in a note instead of raising. ``crux`` is ``None`` when the domain
    doesn't have enough real-user traffic for CrUX to report on, or the CrUX API
    key isn't configured — both degrade to ``source=LAB``, never to a failed
    audit (task 4, point 2).
    """
    now = now or datetime.now(timezone.utc)
    notes: list[str] = []

    ok_runs = [r for r in lighthouse_runs if not r.failed]
    failed_count = len(lighthouse_runs) - len(ok_runs)
    if failed_count:
        notes.append(
            f"{failed_count}/{len(lighthouse_runs)} corrida(s) de Lighthouse fallaron; "
            f"mediana calculada sobre las {len(ok_runs)} restantes."
        )

    lab_lcp = _median(r.lcp_ms for r in ok_runs)
    lab_inp = _median(r.inp_ms for r in ok_runs)
    lab_cls = _median(r.cls for r in ok_runs)
    if ok_runs:
        notes.append(
            "INP de laboratorio aproximado con Total Blocking Time: Lighthouse no "
            "simula interacción real de usuario, así que no puede medir INP de verdad."
        )

    # Provenance is resolved per metric, not once for the whole result: CrUX can
    # have a real field LCP while INP/CLS have no field data and fall back to the
    # lab median — marking the whole PerformanceResult as FIELD in that case would
    # overclaim (hygiene, task 5). Each metric carries its own *_source; the
    # top-level ``source`` is only a summary (FIELD/LAB/MIXED).
    has_field = crux is not None and crux.lcp_ms is not None
    if has_field:
        notes.append(
            "Datos de campo reales de CrUX (percentil 75 sobre tráfico real de "
            "usuarios en Chrome, ventana de 28 días) — la señal que usa Google."
        )
        lcp, lcp_source = crux.lcp_ms, CwvSource.FIELD
        inp, inp_source = _resolve_field_metric(crux.inp_ms, lab_inp)
        cls_, cls_source = _resolve_field_metric(crux.cls, lab_cls)
        if crux.inp_ms is None and lab_inp is not None:
            notes.append(
                "CrUX sin dato de INP para este origen; se completa con la mediana de laboratorio (TBT)."
            )
        if crux.cls is None and lab_cls is not None:
            notes.append(
                "CrUX sin dato de CLS para este origen; se completa con la mediana de laboratorio."
            )
    else:
        notes.append(
            "Estimación de laboratorio, sin datos de tráfico real suficientes: no es "
            "la señal real que usa Google, es una aproximación."
        )
        lcp, lcp_source = lab_lcp, _lab_source(lab_lcp)
        inp, inp_source = lab_inp, _lab_source(lab_inp)
        cls_, cls_source = lab_cls, _lab_source(lab_cls)

    source = _overall_source(lcp_source, inp_source, cls_source)
    if source == CwvSource.MIXED:
        notes.append(_mixed_note(lcp_source, inp_source, cls_source))

    return PerformanceResult(
        source=source,
        lcp_ms=lcp,
        inp_ms=inp,
        cls=cls_,
        lcp_source=lcp_source,
        inp_source=inp_source,
        cls_source=cls_source,
        lighthouse_runs=len(lighthouse_runs),
        crux_available=has_field,
        from_snapshot=False,
        snapshot_at=now,
        notes=notes,
    )


def _median(values: Iterable[float | None]) -> float | None:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return round(statistics.median(vals), 2)


def _resolve_field_metric(
    field_value: float | None, lab_value: float | None
) -> tuple[float | None, CwvSource | None]:
    """One metric under a FIELD result: use CrUX when present, else the lab median.

    Returns ``(value, source)``. ``source`` is FIELD when CrUX had the metric,
    LAB when it was filled from the Lighthouse median, and ``None`` when neither
    is available.
    """
    if field_value is not None:
        return field_value, CwvSource.FIELD
    if lab_value is not None:
        return lab_value, CwvSource.LAB
    return None, None


def _lab_source(value: float | None) -> CwvSource | None:
    """LAB when the metric was measured, ``None`` when it is missing entirely."""
    return CwvSource.LAB if value is not None else None


def _overall_source(*sources: CwvSource | None) -> CwvSource:
    """Summarise the per-metric provenance into one label.

    FIELD/LAB when every present metric shares that source, MIXED when they
    differ. Falls back to LAB when nothing was measured at all (a fully degraded
    result, never FIELD).
    """
    present = [s for s in sources if s is not None]
    if not present:
        return CwvSource.LAB
    if all(s == CwvSource.FIELD for s in present):
        return CwvSource.FIELD
    if all(s == CwvSource.LAB for s in present):
        return CwvSource.LAB
    return CwvSource.MIXED


def _mixed_note(lcp: CwvSource | None, inp: CwvSource | None, cls: CwvSource | None) -> str:
    labels = {CwvSource.FIELD: "campo (CrUX)", CwvSource.LAB: "laboratorio (Lighthouse/TBT)"}
    parts = [
        f"{name}={labels[src]}"
        for name, src in (("LCP", lcp), ("INP", inp), ("CLS", cls))
        if src is not None
    ]
    return "Fuentes mixtas por métrica: " + ", ".join(parts) + "."


# --------------------------------------------------------------------------- #
# Snapshot store — minimal interface, no Mongo import in audit_engine
# --------------------------------------------------------------------------- #
class SnapshotStore(Protocol):
    """Where <48h Core Web Vitals snapshots are kept (diagram 3.4).

    ``get`` must itself enforce the freshness window: it returns a result only
    when a snapshot younger than :data:`SNAPSHOT_MAX_AGE` exists for ``domain``,
    ``None`` otherwise. Pushing the freshness check into the store (rather than
    re-checking in the shell) lets a real implementation filter by
    ``snapshot_at`` directly in its query. The Mongo-backed implementation is
    wired in task 8; this module only depends on this Protocol.
    """

    async def get(self, domain: str) -> PerformanceResult | None: ...

    async def save(self, domain: str, result: PerformanceResult) -> None: ...


class InMemorySnapshotStore:
    """Process-local, no-Mongo default: a plain dict keyed by domain.

    Not persisted across process restarts, so a *fresh instance* (the default
    when the shell isn't given one) behaves like a no-op — every call
    remeasures. Reusing one instance across calls (tests, a long-lived process)
    does exercise real <48h caching.
    """

    def __init__(self) -> None:
        self._snapshots: dict[str, PerformanceResult] = {}

    async def get(self, domain: str) -> PerformanceResult | None:
        result = self._snapshots.get(domain)
        if result is None:
            return None
        if datetime.now(timezone.utc) - result.snapshot_at >= SNAPSHOT_MAX_AGE:
            return None
        return result

    async def save(self, domain: str, result: PerformanceResult) -> None:
        self._snapshots[domain] = result


# --------------------------------------------------------------------------- #
# Async shell: snapshot check -> Lighthouse (sequential) + CrUX -> pure layer
# --------------------------------------------------------------------------- #
async def measure_performance(
    domain: str,
    fetch: FetchResult,
    *,
    snapshot_store: SnapshotStore | None = None,
    run_lighthouse: Callable[[str], Awaitable[LighthouseRun]] | None = None,
    fetch_crux: Callable[[str], Awaitable[CruxFieldData | None]] | None = None,
) -> PerformanceResult:
    """Return Core Web Vitals for ``domain``.

    If a snapshot younger than 48h exists it is returned as-is, only with
    ``from_snapshot`` flipped to ``True`` (same metrics, same original
    ``snapshot_at``). Otherwise runs Lighthouse locally 3 times **sequentially**
    (task 4, point 1 — parallel runs would contend for CPU/network in the same
    process and bias the result), queries CrUX field data, persists a fresh
    snapshot, and delegates the math to :func:`evaluate_performance`.

    ``run_lighthouse``/``fetch_crux``/``snapshot_store`` are injectable so this
    shell is testable without spawning Chrome or calling any real API (task 4,
    point 6); they default to the real Playwright+Lighthouse-CLI runner, the
    real CrUX API client, and a fresh :class:`InMemorySnapshotStore`.
    """
    store = snapshot_store if snapshot_store is not None else InMemorySnapshotStore()
    run_lighthouse = run_lighthouse or _run_lighthouse_once
    fetch_crux = fetch_crux or _fetch_crux_field_data

    cached = await store.get(domain)
    if cached is not None:
        return cached.model_copy(update={"from_snapshot": True})

    target = _target_url(fetch, domain)

    runs: list[LighthouseRun] = []
    for _ in range(_LIGHTHOUSE_RUN_COUNT):
        runs.append(await run_lighthouse(target))

    crux = await fetch_crux(domain)

    result = evaluate_performance(runs, crux)
    await store.save(domain, result)
    return result


def _target_url(fetch: FetchResult, domain: str) -> str:
    target = fetch.final_url or fetch.domain or domain
    if "//" not in target:
        target = "https://" + target
    return target


# --------------------------------------------------------------------------- #
# Real Lighthouse runner: Playwright launches Chrome, the lighthouse CLI audits it
# --------------------------------------------------------------------------- #
def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _lighthouse_binary() -> str | None:
    """Locate the `lighthouse` CLI: project-local install first, then $PATH."""
    repo_root = Path(__file__).resolve().parents[3]
    local_bin = repo_root / "node_modules" / ".bin" / "lighthouse"
    if local_bin.exists():
        return str(local_bin)
    return shutil.which("lighthouse")


async def _run_lighthouse_once(url: str) -> LighthouseRun:
    """Launch Chromium via Playwright, point the lighthouse CLI at it, parse the report."""
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        return LighthouseRun(failed=True, error=f"playwright no disponible: {exc}")

    port = _free_port()
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=[f"--remote-debugging-port={port}"],
            )
            try:
                return await _run_lighthouse_cli(url, port)
            finally:
                await browser.close()
    except Exception as exc:  # Chrome failed to launch, port conflict, etc.
        return LighthouseRun(failed=True, error=str(exc))


async def _run_lighthouse_cli(url: str, port: int) -> LighthouseRun:
    binary = _lighthouse_binary()
    if binary is None:
        return LighthouseRun(
            failed=True, error="lighthouse CLI no encontrado; ejecuta `make install`."
        )

    cmd = [
        binary,
        url,
        f"--port={port}",
        "--output=json",
        "--output-path=stdout",
        "--only-categories=performance",
        "--chrome-flags=--headless",
        "--quiet",
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=_LIGHTHOUSE_TIMEOUT_S)
    except (asyncio.TimeoutError, OSError) as exc:
        return LighthouseRun(failed=True, error=str(exc))

    if proc.returncode != 0:
        return LighthouseRun(failed=True, error=stderr.decode(errors="replace")[:500])

    try:
        report = json.loads(stdout)
        audits = report["audits"]
        lcp = audits["largest-contentful-paint"]["numericValue"]
        cls_ = audits["cumulative-layout-shift"]["numericValue"]
        tbt = audits["total-blocking-time"]["numericValue"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        return LighthouseRun(failed=True, error=f"reporte de Lighthouse ilegible: {exc}")

    return LighthouseRun(lcp_ms=lcp, inp_ms=tbt, cls=cls_)


# --------------------------------------------------------------------------- #
# Real CrUX client
# --------------------------------------------------------------------------- #
async def _fetch_crux_field_data(domain: str) -> CruxFieldData | None:
    """None when the API key isn't configured, the origin has no traffic, or the call fails."""
    api_key = os.getenv("CRUX_API_KEY")
    if not api_key:
        return None
    try:
        return await asyncio.to_thread(_sync_fetch_crux, domain, api_key)
    except Exception:
        return None


def _sync_fetch_crux(domain: str, api_key: str) -> CruxFieldData | None:
    origin = domain if "//" in domain else f"https://{domain}"
    resp = requests.post(
        _CRUX_ENDPOINT,
        params={"key": api_key},
        json={"origin": origin},
        timeout=_CRUX_TIMEOUT_S,
    )
    if resp.status_code == 404:
        return None  # NOT_FOUND: insufficient real-user traffic for this origin
    resp.raise_for_status()
    metrics = resp.json().get("record", {}).get("metrics", {})
    return CruxFieldData(
        lcp_ms=_crux_p75(metrics, "largest_contentful_paint"),
        inp_ms=_crux_p75(metrics, "interaction_to_next_paint"),
        cls=_crux_p75(metrics, "cumulative_layout_shift"),
    )


def _crux_p75(metrics: dict, key: str) -> float | None:
    value = metrics.get(key, {}).get("percentiles", {}).get("p75")
    if value is None:
        return None
    return float(value)


# --------------------------------------------------------------------------- #
# Raw payload extraction
# --------------------------------------------------------------------------- #
def process_lighthouse_payload(raw_data: dict[str, Any]) -> dict[str, Any]:
    """Extract strictly required performance and SEO nodes from Lighthouse payload.

    Extracts:
    * Core Web Vitals in Runtime (LCP, TBT, CLS, FCP)
    * Opportunities and Financial Impact (uses-responsive-images, modern-image-formats)
    * Critical SEO audits (document-image-alt)
    """
    if not raw_data:
        return {"performance_runtime": {}, "seo_runtime": {}}

    audits = raw_data.get("lighthouseResult", {}).get("audits", {})

    def _numeric(key: str) -> float | None:
        val = audits.get(key, {}).get("numericValue")
        return float(val) if val is not None else None

    def _savings(key: str) -> float | None:
        val = audits.get(key, {}).get("details", {}).get("overallSavingsBytes")
        return float(val) if val is not None else None

    def _score(key: str) -> int | None:
        val = audits.get(key, {}).get("score")
        return int(val) if val is not None else None

    lcp = _numeric("largest-contentful-paint")
    fcp = _numeric("first-contentful-paint")

    perf = {
        "largest-contentful-paint": lcp / 1000.0 if lcp is not None else None,
        "total-blocking-time": _numeric("total-blocking-time"),
        "cumulative-layout-shift": _numeric("cumulative-layout-shift"),
        "first-contentful-paint": fcp / 1000.0 if fcp is not None else None,
        "uses-responsive-images": _savings("uses-responsive-images"),
        "modern-image-formats": _savings("modern-image-formats"),
    }

    seo = {
        "document-image-alt": _score("document-image-alt"),
    }

    return {
        "performance_runtime": perf,
        "seo_runtime": seo,
    }
