"""Audit engine entry point and gate evaluation (diagram 3.1).

:func:`run_audit` is the single public entry point. No LLM is used anywhere in
the pipeline; every number is produced by a deterministic submodule.
"""

from datetime import timedelta

from .models import (
    AuditResult,
    CitabilityResult,
    LeadViabilityResult,
    PerformanceResult,
    SchemaResult,
    SecurityResult,
    TechnicalResult,
    WeightedScoreResult,
)

# Site did not respond -> mark not accessible and retry later, do not block.
RETRY_AFTER = timedelta(hours=24)


async def run_audit(domain: str) -> AuditResult:
    """Run the full deterministic audit for ``domain`` (diagram 3.1).

    Call order:
      1. fetch_site(domain) -> HTML + headers + robots.txt + sitemap.
         If the server does not respond, return an AuditResult with
         reachability=UNREACHABLE and retry_at=now+RETRY_AFTER, run no submodule,
         and do not block the pipeline.
      2. detect_tech_stack(fetch)
      3. score_technical(fetch, stack)      -> pure, fetch+stack only
      4. scan_security(fetch, stack)        -> authoritative headers + CVEs
      5. measure_performance(domain, fetch) -> Core Web Vitals (snapshot/Lighthouse)
      6. validate_schema(fetch)             -> 12 JSON-LD checks
      7. suggest_keywords(fetch, schema)
      8. score_citability(fetch)
      9. evaluate_lead_viability(...) -> Gate 1: if already solved, not a lead.
     10. evaluate_weighted_score(...) -> Gate 2, only when it is a lead.

    Persisting the full report to Mongo happens outside this package (services/,
    task 8).
    """
    raise NotImplementedError


def evaluate_lead_viability(
    technical: TechnicalResult,
    security: SecurityResult,
    performance: PerformanceResult,
    schema_org: SchemaResult,
) -> LeadViabilityResult:
    """Gate 1: decide whether the site has enough margin to be a lead.

    A site already scoring high across the board is not a lead.
    """
    raise NotImplementedError


def evaluate_weighted_score(
    technical: TechnicalResult,
    security: SecurityResult,
    performance: PerformanceResult,
    schema_org: SchemaResult,
    citability: CitabilityResult,
) -> WeightedScoreResult:
    """Gate 2: final weighted score across the 5 categories.

    The exact per-category weights are defined in a later task. Mapping of which
    submodule feeds each category, so no estimate is silently double-counted
    against its authoritative result:

      - Technical:   TechnicalResult.score. technical.py includes the
                     ``security_headers_estimate`` and ``cwv_static_estimate``
                     dimensions — these are ESTIMATES from the raw fetch only.
      - Security:    SecurityResult (authoritative headers + CVEs). This is the
                     real security signal; do NOT also add
                     technical.security_headers_estimate on top of it.
      - Performance: PerformanceResult (authoritative Core Web Vitals). This is
                     the real CWV signal; do NOT also add
                     technical.cwv_static_estimate on top of it.
      - Schema:      SchemaResult.score.
      - Citability:  CitabilityResult.score (5th category; exact weight TBD).
    """
    raise NotImplementedError
