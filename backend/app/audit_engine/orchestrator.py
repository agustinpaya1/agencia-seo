"""Audit engine entry point and gate evaluation (diagram 3.1).

:func:`run_audit` is the single public entry point. No LLM is used anywhere in
the pipeline; every number is produced by a deterministic submodule.

The two shared normalisers live here because both gates read them (and the
persistence layer reuses them to fill the per-category ``reports`` map, since
SecurityResult/PerformanceResult carry no ``score`` field of their own):

* :func:`security_score` turns a :class:`SecurityResult` into a 0-100 number.
  The worst unpatched CVE caps the score, and "worst" is picked by an explicit
  :data:`_SEVERITY_RANK` — a plain ``max()`` over the enum would compare the
  string *values* alphabetically ("low" > "critical"), i.e. exactly backwards.
* :func:`performance_score` turns a :class:`PerformanceResult` into a 0-100
  number, or ``None`` when nothing was measurable. The distinction matters
  (task 8, higiene 2): a *measured* bad LCP (e.g. 6000 ms) scores near 0 on
  purpose — that low number is a real sales argument — while performance with
  no data at all (LCP/INP/CLS all ``None``) returns ``None`` and is treated as a
  missing category (excluded from Gate 2 and renormalised, not scored 0).
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from functools import partial

from .citability import score_citability as _score_citability
from .fetch import fetch_site as _fetch_site
from .keywords import suggest_keywords as _suggest_keywords
from .models import (
    AuditResult,
    AuditStage,
    CitabilityResult,
    FetchResult,
    KeywordsResult,
    LeadViabilityResult,
    PerformanceResult,
    Reachability,
    SchemaResult,
    ScoreTier,
    SecurityResult,
    Severity,
    TechnicalResult,
    TechStackResult,
    WeightedDimension,
    WeightedScoreResult,
)
from .performance import SnapshotStore, process_lighthouse_payload
from .performance import measure_performance as _measure_performance
from .schema_org import validate_schema as _validate_schema
from .security import scan_security as _scan_security
from .tech_stack import detect_tech_stack as _detect_tech_stack
from .technical import score_technical as _score_technical

# Site did not respond -> mark not accessible and retry later, do not block.
RETRY_AFTER = timedelta(hours=24)

# Progress callback: awaited with the stage that is *starting*. The engine only
# reports; whoever injects it decides what to do (services/audit.py persists it
# onto the lead as `current_stage`).
StageReporter = Callable[[AuditStage], Awaitable[None]]

# Gate 1: every required dimension must reach this to count as "already solved".
LEAD_THRESHOLD = 90.0

# --------------------------------------------------------------------------- #
# Security normalisation (shared by both gates)
# --------------------------------------------------------------------------- #
# Explicit gravity order: `max()` over the Severity enum would compare its string
# *values* alphabetically ("low" > "high" > "critical"), which is backwards. This
# ranking is what picks the worst CVE in a mixed list (task 8, higiene 1).
_SEVERITY_RANK: dict[Severity, int] = {
    Severity.CRITICAL: 4,
    Severity.HIGH: 3,
    Severity.MEDIUM: 2,
    Severity.LOW: 1,
    Severity.UNKNOWN: 0,
}

# A known unpatched CVE caps the security score at a level set by its severity —
# you cannot be "90+ secure" with a critical hole open. UNKNOWN (WPScan gives no
# CVSS bucket) is a real-but-ungraded finding: capped cautiously below LOW rather
# than dismissed, since we genuinely can't rule out that it is severe.
_VULN_CEILING: dict[Severity, float] = {
    Severity.CRITICAL: 0.0,
    Severity.HIGH: 25.0,
    Severity.MEDIUM: 50.0,
    Severity.LOW: 70.0,
    Severity.UNKNOWN: 55.0,
}

_SECURITY_HEADER_ATTRS = (
    "hsts",
    "csp",
    "x_content_type_options",
    "x_frame_options",
    "referrer_policy",
    "permissions_policy",
)


def security_score(security: SecurityResult) -> float:
    """Normalise a SecurityResult to 0-100 (shared by Gate 1 and Gate 2).

    Base score = share of the 6 recommended security headers present (our own
    deterministic pass; Observatory's grade is reported in SecurityResult but is
    not re-scored here, mirroring security.py's own "grade is validation on top,
    not a replacement"). Any known unpatched CVE then caps the score by its worst
    severity (:data:`_SEVERITY_RANK` picks the worst). ``version_known=False``
    means no scanner ran, so there are no vulnerabilities and no cap — absence of
    data never becomes risk.
    """
    headers = security.headers
    present = sum(bool(getattr(headers, attr)) for attr in _SECURITY_HEADER_ATTRS)
    score = present / len(_SECURITY_HEADER_ATTRS) * 100.0

    if security.vulnerabilities:
        worst = max(security.vulnerabilities, key=lambda v: _SEVERITY_RANK[v.severity]).severity
        score = min(score, _VULN_CEILING[worst])
    return round(score, 2)


# --------------------------------------------------------------------------- #
# Performance normalisation (shared by both gates)
# --------------------------------------------------------------------------- #
# Google's good/poor thresholds per Core Web Vital. Each metric maps to 0-100:
# <= good -> 100, == poor -> 50, then declining to 0 one good->poor span past
# `poor`. A genuinely bad metric lands near 0 on purpose (task 8, higiene 2).
_LCP_GOOD, _LCP_POOR = 2500.0, 4000.0  # ms
_INP_GOOD, _INP_POOR = 200.0, 500.0  # ms
_CLS_GOOD, _CLS_POOR = 0.1, 0.25  # unitless


def _metric_score(value: float, good: float, poor: float) -> float:
    """0-100 score for one Core Web Vital from its good/poor thresholds."""
    if value <= good:
        return 100.0
    span = poor - good
    if value <= poor:
        return 100.0 - (value - good) / span * 50.0
    return max(0.0, 50.0 - (value - poor) / span * 50.0)


def performance_score(performance: PerformanceResult) -> float | None:
    """Normalise a PerformanceResult to 0-100, or ``None`` when unmeasurable.

    The average of the metrics that *were* measured. ``None`` only when all three
    (LCP/INP/CLS) are missing — that is "no data to judge", handled as a missing
    category (excluded + renormalised), NOT scored 0. A measured-but-bad metric
    still scores, and scores low; that low number is intentional (task 8, higiene
    2), so the two cases must not collapse into one.
    """
    scores: list[float] = []
    if performance.lcp_ms is not None:
        scores.append(_metric_score(performance.lcp_ms, _LCP_GOOD, _LCP_POOR))
    if performance.inp_ms is not None:
        scores.append(_metric_score(performance.inp_ms, _INP_GOOD, _INP_POOR))
    if performance.cls is not None:
        scores.append(_metric_score(performance.cls, _CLS_GOOD, _CLS_POOR))
    if not scores:
        return None
    return round(sum(scores) / len(scores), 2)


# --------------------------------------------------------------------------- #
# Gate 1 — lead viability (weakest link, not average)
# --------------------------------------------------------------------------- #
def evaluate_lead_viability(
    technical: TechnicalResult,
    security: SecurityResult,
    performance: PerformanceResult,
    schema_org: SchemaResult,
) -> LeadViabilityResult:
    """Gate 1: decide whether the site has enough margin to be a lead.

    A site is *not* a lead only when **every** one of the four required
    dimensions — technical, normalised security, normalised performance,
    schema_org — reaches :data:`LEAD_THRESHOLD` (90). The weakest link rules, not
    the average: one dimension below 90 makes it a lead even if the other three
    are perfect. Citability does not enter Gate 1 (task 8, punto 2).

    Precondition (enforced by the orchestrator, see :func:`_gate_one`): all four
    results are present and performance is measurable. The non-measurable guard
    below only keeps this pure function total if it is ever called directly.
    """
    perf = performance_score(performance)
    if perf is None:
        return LeadViabilityResult(
            is_lead=True,
            reason="dimensión no disponible: no se puede confirmar que esté resuelto",
            checked_dimensions={
                "technical": technical.score,
                "security": security_score(security),
                "schema_org": schema_org.score,
            },
        )

    dims: dict[str, float] = {
        "technical": technical.score,
        "security": security_score(security),
        "performance": perf,
        "schema_org": schema_org.score,
    }
    weakest_name = min(dims, key=lambda k: dims[k])
    weakest = dims[weakest_name]
    is_lead = weakest < LEAD_THRESHOLD

    if is_lead:
        reason = (
            f"Hay margen de mejora: la dimensión más débil ('{weakest_name}'={weakest:.1f}) "
            f"está por debajo de {LEAD_THRESHOLD:.0f}; manda el eslabón más débil, no el promedio."
        )
    else:
        reason = (
            f"Ya resuelto: las 4 dimensiones (technical, security, performance, schema_org) "
            f"puntúan >= {LEAD_THRESHOLD:.0f}; no hay margen de mejora que ofrecer."
        )
    return LeadViabilityResult(is_lead=is_lead, reason=reason, checked_dimensions=dims)


# --------------------------------------------------------------------------- #
# Gate 2 — final weighted score
# --------------------------------------------------------------------------- #
# Weights sum to 100 (task 8, punto 1). Renormalised over available categories.
_GATE2_WEIGHTS: dict[str, float] = {
    "technical": 35.0,
    "citability": 25.0,
    "performance": 20.0,
    "schema": 15.0,
    "security": 5.0,
}
_GATE2_ORDER = ("technical", "citability", "performance", "schema", "security")


def _tier_for(score: float) -> ScoreTier:
    if score >= 90:
        return ScoreTier.EXCELLENT
    if score >= 75:
        return ScoreTier.GOOD
    if score >= 60:
        return ScoreTier.FAIR
    if score >= 40:
        return ScoreTier.POOR
    return ScoreTier.CRITICAL


def _exclusion_finding(name: str, performance: PerformanceResult | None) -> str:
    """Why a category was dropped from the weighting — kept visible in breakdown."""
    if name == "performance" and performance is not None:
        # The submodule ran but produced no metric: excluded, not scored 0.
        return "excluida: sin datos de rendimiento disponibles (fallo de medición)."
    return f"excluida: categoría '{name}' no disponible (submódulo no ejecutado o fallido)."


def evaluate_weighted_score(
    technical: TechnicalResult | None,
    security: SecurityResult | None,
    performance: PerformanceResult | None,
    schema_org: SchemaResult | None,
    citability: CitabilityResult | None,
) -> WeightedScoreResult | None:
    """Gate 2: final weighted score across the 5 categories.

    Weights (task 8, punto 1): Technical 35 / Citability 25 / Performance 20 /
    Schema 15 / Security 5. Any category that is unavailable — a failed submodule
    (``None``) or performance measured with no data (``performance_score`` ->
    ``None``) — is excluded and its weight redistributed proportionally over the
    ones that remain (the single renormalisation mechanism, task 8, higiene 2).
    Every category still appears in ``breakdown``: excluded ones with
    ``weight=0``/``points=0`` and a finding, so the gap is visible. Returns
    ``None`` only when *every* category is missing (task 8, punto 5).

    Which submodule feeds each category (no estimate double-counted against its
    authoritative result): Technical <- TechnicalResult.score (includes the
    header/CWV *estimate* dimensions from the raw fetch); Security <- the
    authoritative SecurityResult; Performance <- the authoritative
    PerformanceResult; Schema <- SchemaResult.score; Citability <-
    CitabilityResult.score.
    """
    raw: dict[str, float | None] = {
        "technical": technical.score if technical is not None else None,
        "citability": citability.score if citability is not None else None,
        "performance": performance_score(performance) if performance is not None else None,
        "schema": schema_org.score if schema_org is not None else None,
        "security": security_score(security) if security is not None else None,
    }

    total_weight = sum(_GATE2_WEIGHTS[name] for name, value in raw.items() if value is not None)
    if total_weight == 0.0:
        return None  # every category missing -> no honest score to give

    breakdown: list[WeightedDimension] = []
    final = 0.0
    for name in _GATE2_ORDER:
        score = raw[name]
        base_weight = _GATE2_WEIGHTS[name]
        if score is None:
            breakdown.append(
                WeightedDimension(
                    name=name,
                    score=0.0,
                    weight=0.0,
                    points=0.0,
                    findings=[_exclusion_finding(name, performance)],
                )
            )
            continue
        share = base_weight / total_weight
        points = round(score * share, 2)
        final += points
        breakdown.append(
            WeightedDimension(
                name=name,
                score=round(score, 2),
                weight=round(share, 4),
                points=points,
                findings=[
                    f"peso base {base_weight:.0f}/100, renormalizado a {share:.1%} "
                    "sobre las categorías disponibles."
                ],
            )
        )

    final = round(final, 2)
    return WeightedScoreResult(final_score=final, tier=_tier_for(final), breakdown=breakdown)


# --------------------------------------------------------------------------- #
# Orchestrator entry point
# --------------------------------------------------------------------------- #
async def run_audit(
    domain: str,
    *,
    fetch_site: Callable[[str], Awaitable[FetchResult]] | None = None,
    detect_tech_stack: Callable[[FetchResult], Awaitable[TechStackResult]] | None = None,
    score_technical: Callable[[FetchResult, TechStackResult], TechnicalResult] | None = None,
    scan_security: Callable[[FetchResult, TechStackResult], Awaitable[SecurityResult]]
    | None = None,
    measure_performance: Callable[[str, FetchResult], Awaitable[PerformanceResult]] | None = None,
    validate_schema: Callable[[FetchResult], Awaitable[SchemaResult]] | None = None,
    suggest_keywords: Callable[[FetchResult, SchemaResult], KeywordsResult] | None = None,
    score_citability: Callable[[FetchResult], CitabilityResult] | None = None,
    snapshot_store: SnapshotStore | None = None,
    on_stage: StageReporter | None = None,
    api_key: str | None = None,
) -> AuditResult:
    """Run the full deterministic audit for ``domain`` (diagram 3.1).

    Order (task 8, punto 4): fetch (sequential) -> detect_tech_stack (the one
    mandatory sequential step, finished *before* performance so wappalyzer's
    fallback render and Lighthouse never contend for Chromium) -> score_technical
    (sync, inline) -> scan_security + measure_performance + validate_schema in
    parallel -> suggest_keywords + score_citability (sync, after the gather) ->
    Gate 1 + Gate 2.

    Failure handling (task 8, punto 5): each submodule runs in its own
    try/except; an unexpected failure leaves that field ``None`` and appends a
    line to ``AuditResult.errors`` without aborting the rest. Cascades:
    score_technical and scan_security are skipped when detect_tech_stack fails
    (they depend on the stack); suggest_keywords is skipped when validate_schema
    fails. An UNREACHABLE site returns immediately with ``retry_at`` derived from
    the fetch timestamp and no submodule or gate run (task 8, punto 7).

    Every submodule is injectable (same DI shape as the rest of the package) so
    the whole pipeline is testable without network/Chrome; each defaults to the
    real implementation. Persisting to Mongo happens outside this package (8b).

    ``snapshot_store`` is where the *default* ``measure_performance`` keeps its
    <48h Core Web Vitals snapshots — task 8b injects the Mongo-backed store here
    so the cache is real across audits instead of a fresh in-memory no-op per
    call. It only applies to the default path: an injected ``measure_performance``
    manages its own store.

    ``on_stage`` is awaited with each :class:`AuditStage` as it *starts*
    (FETCH .. GATE_2; PERSISTENCE belongs to the caller). A failing reporter
    must never abort the audit: the exception becomes an ``errors`` line and
    the pipeline continues.
    """
    fetch_site = fetch_site or partial(_fetch_site, lighthouse_api_key=api_key)
    detect_tech_stack = detect_tech_stack or _detect_tech_stack
    score_technical = score_technical or _score_technical
    scan_security = scan_security or _scan_security
    measure_performance = measure_performance or partial(
        _measure_performance, snapshot_store=snapshot_store
    )
    validate_schema = validate_schema or _validate_schema
    suggest_keywords = suggest_keywords or _suggest_keywords
    score_citability = score_citability or _score_citability

    created_at = datetime.now(timezone.utc)
    errors: list[str] = []

    async def report(stage: AuditStage) -> None:
        # Progress is best-effort: a broken reporter is recorded, never fatal.
        if on_stage is None:
            return
        try:
            await on_stage(stage)
        except Exception as exc:
            errors.append(f"on_stage({stage.value}): fallo inesperado ({exc!r}).")

    # 1. Initial fetch — the one mandatory sequential step; everything reads it.
    await report(AuditStage.FETCH)
    try:
        fetch = await fetch_site(domain)
    except Exception as exc:  # fetch_site is built not to raise; guard a real bug anyway
        errors.append(f"fetch_site: fallo inesperado ({exc!r}).")
        fetch = FetchResult(
            domain=domain,
            reachability=Reachability.UNREACHABLE,
            fetched_at=created_at,
            notes=["fetch_site falló inesperadamente."],
        )

    # Punto 7: UNREACHABLE -> immediate return, no submodule, no gate. retry_at is
    # fetched_at + RETRY_AFTER (the fetch timestamp), not a second now().
    if fetch.reachability != Reachability.OK:
        return AuditResult(
            domain=domain,
            reachability=fetch.reachability,
            retry_at=fetch.fetched_at + RETRY_AFTER,
            fetch=fetch,
            errors=errors,
            created_at=created_at,
        )

    performance_runtime = None
    seo_runtime = None
    if fetch.lighthouse_raw:
        extracted = process_lighthouse_payload(fetch.lighthouse_raw)
        performance_runtime = extracted.get("performance_runtime")
        seo_runtime = extracted.get("seo_runtime")

    # 2. Tech stack — sequential, fully finished before performance starts.
    await report(AuditStage.TECH_STACK)
    tech_stack: TechStackResult | None = None
    try:
        tech_stack = await detect_tech_stack(fetch)
    except Exception as exc:
        errors.append(
            f"detect_tech_stack: fallo inesperado ({exc!r}); technical y security no se "
            "ejecutan (dependen de tech_stack)."
        )

    # 3-6. One reported stage for the whole technical block: the inline
    # technical score plus the parallel gather below. It stays "current" until
    # CONTENT_ANALYSIS is reported, i.e. until all four submodules finished.
    await report(AuditStage.TECHNICAL_ANALYSIS)

    # 3. Technical score — pure/sync, inline. Cascade: skipped if tech_stack failed.
    technical: TechnicalResult | None = None
    if tech_stack is not None:
        try:
            technical = score_technical(fetch, tech_stack)
        except Exception as exc:
            errors.append(f"score_technical: fallo inesperado ({exc!r}).")
    else:
        errors.append("score_technical: no ejecutado (depende de tech_stack).")

    # 4-6. Security + performance + schema in parallel. Security cascades off
    # tech_stack; performance/schema depend only on the fetch.
    async def _run_security() -> SecurityResult:
        return await scan_security(fetch, tech_stack)

    async def _run_performance() -> PerformanceResult:
        return await measure_performance(domain, fetch)

    async def _run_schema() -> SchemaResult:
        return await validate_schema(fetch)

    parallel: dict[str, Awaitable] = {
        "performance": _run_performance(),
        "schema": _run_schema(),
    }
    if tech_stack is not None:
        parallel["security"] = _run_security()
    else:
        errors.append("scan_security: no ejecutado (depende de tech_stack).")

    gathered = await asyncio.gather(*parallel.values(), return_exceptions=True)
    by_name = dict(zip(parallel.keys(), gathered))

    performance = _unwrap(by_name["performance"], "measure_performance", errors)
    schema_org = _unwrap(by_name["schema"], "validate_schema", errors)
    security = (
        _unwrap(by_name["security"], "scan_security", errors) if "security" in by_name else None
    )

    # 7-8. Keywords + citability, one reported stage.
    await report(AuditStage.CONTENT_ANALYSIS)

    # 7. Keywords — pure/sync, after the gather. Cascade: skipped if schema failed.
    keywords: KeywordsResult | None = None
    if schema_org is not None:
        try:
            keywords = suggest_keywords(fetch, schema_org)
        except Exception as exc:
            errors.append(f"suggest_keywords: fallo inesperado ({exc!r}).")
    else:
        errors.append("suggest_keywords: no ejecutado (depende de schema_org).")

    # 8. Citability — pure/sync, after the gather. Depends only on the fetch.
    citability: CitabilityResult | None = None
    try:
        citability = score_citability(fetch)
    except Exception as exc:
        errors.append(f"score_citability: fallo inesperado ({exc!r}).")

    # Gate 1 — lead viability (all 4 required dimensions must be present & measurable).
    await report(AuditStage.GATE_1)
    lead_viability = _gate_one(technical, security, performance, schema_org)

    # Gate 2 — weighted score, computed regardless of is_lead (punto 6). None only
    # when every category is missing.
    await report(AuditStage.GATE_2)
    weighted_score = evaluate_weighted_score(
        technical, security, performance, schema_org, citability
    )

    return AuditResult(
        domain=domain,
        reachability=fetch.reachability,
        fetch=fetch,
        tech_stack=tech_stack,
        technical=technical,
        security=security,
        performance=performance,
        schema_org=schema_org,
        keywords=keywords,
        citability=citability,
        lead_viability=lead_viability,
        weighted_score=weighted_score,
        errors=errors,
        created_at=created_at,
        performance_runtime=performance_runtime,
        seo_runtime=seo_runtime,
    )


def _unwrap(result: object, label: str, errors: list[str]):
    """A gather() slot: an Exception becomes ``None`` + an errors line."""
    if isinstance(result, Exception):
        errors.append(f"{label}: fallo inesperado ({result!r}).")
        return None
    return result


def _gate_one(
    technical: TechnicalResult | None,
    security: SecurityResult | None,
    performance: PerformanceResult | None,
    schema_org: SchemaResult | None,
) -> LeadViabilityResult:
    """Guard Gate 1: only call :func:`evaluate_lead_viability` when all four
    required dimensions are present and performance is measurable.

    A missing submodule (``None``) or non-measurable performance means we cannot
    confirm the site "already solved" it, so it is a lead by default (task 8,
    punto 5) — built directly here rather than routed through the pure function
    (which cannot be handed a ``None`` result).
    """
    perf_score = performance_score(performance) if performance is not None else None
    if technical is None or security is None or schema_org is None or perf_score is None:
        checked: dict[str, float] = {}
        if technical is not None:
            checked["technical"] = technical.score
        if security is not None:
            checked["security"] = security_score(security)
        if perf_score is not None:
            checked["performance"] = perf_score
        if schema_org is not None:
            checked["schema_org"] = schema_org.score
        return LeadViabilityResult(
            is_lead=True,
            reason="dimensión no disponible: no se puede confirmar que esté resuelto",
            checked_dimensions=checked,
        )
    return evaluate_lead_viability(technical, security, performance, schema_org)
