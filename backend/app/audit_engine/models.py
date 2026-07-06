"""Pydantic models for the deterministic audit engine.

One ``*Result`` model per submodule plus an aggregating :class:`AuditResult`.
The engine never calls an LLM at any point, so nothing here depends on an
Anthropic/OpenAI/Gemini client. The shapes follow the flow described in
diagram 3.1 of docs/motor-auditoria-determinista.md.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Shared enums
# --------------------------------------------------------------------------- #
class Reachability(str, Enum):
    """Whether the initial fetch reached the origin server (diagram 3.1)."""

    OK = "ok"
    UNREACHABLE = "unreachable"  # no response / timeout -> retry in 24h


class Confidence(str, Enum):
    """Confidence level for signals that can be weak or contradictory."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Severity(str, Enum):
    """CVE severity, mirrored from the official source (diagram 3.3)."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class CwvSource(str, Enum):
    """Origin of the Core Web Vitals numbers (diagram 3.4).

    Provenance is tracked per metric (LCP/INP/CLS can come from different
    sources): CrUX may report a real field LCP while INP/CLS fall back to the lab
    median. ``MIXED`` is the overall summary label for that case; the per-metric
    ``*_source`` fields on :class:`PerformanceResult` carry the exact origin.
    """

    FIELD = "field"  # CrUX real-user data ("dato real de Google")
    LAB = "lab"  # Lighthouse lab run ("sin trafico real registrado")
    MIXED = "mixed"  # overall summary: some metrics FIELD, others LAB


# --------------------------------------------------------------------------- #
# Scoring primitive
# --------------------------------------------------------------------------- #
class WeightedDimension(BaseModel):
    """A single weighted category inside a composite score."""

    name: str
    score: float  # 0-100, normalised for this dimension
    weight: float  # 0-1 share of the composite total
    points: float  # score * weight, contribution to total
    findings: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Shared input: initial fetch (diagram 3.1, step B) -> produced by fetch.py
# --------------------------------------------------------------------------- #
class FetchResult(BaseModel):
    """Raw material every deterministic submodule reads from.

    Produced by :func:`audit_engine.fetch.fetch_site`. When the server does not
    respond, ``reachability`` is ``UNREACHABLE`` and the HTML/headers fields stay
    empty; the orchestrator then schedules a retry instead of running submodules.
    """

    domain: str
    reachability: Reachability
    status_code: int | None = None
    final_url: str | None = None  # after following redirects
    html: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    robots_txt: str | None = None
    sitemap_urls: list[str] = Field(default_factory=list)
    fetched_at: datetime
    notes: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# tech_stack.py
# --------------------------------------------------------------------------- #
class DetectedTechnology(BaseModel):
    """A single technology fingerprint found on the site."""

    name: str
    version: str | None = None
    categories: list[str] = Field(default_factory=list)
    confidence: Confidence


class TechStackResult(BaseModel):
    """Technology detection output (diagram 3.2)."""

    identified: bool  # False -> "stack no identificado"
    technologies: list[DetectedTechnology] = Field(default_factory=list)
    cms: str | None = None
    behind_cdn: bool = False  # origin server not visible, edge only
    origin_visible: bool = True
    confidence: Confidence = Confidence.LOW
    notes: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# technical.py
# --------------------------------------------------------------------------- #
class TechnicalResult(BaseModel):
    """Deterministic technical SEO score (technical.py, pure over fetch+stack)."""

    dimensions: list[WeightedDimension] = Field(default_factory=list)
    score: float = 0.0  # 0-100 weighted


# --------------------------------------------------------------------------- #
# security.py
# --------------------------------------------------------------------------- #
class SecurityHeaders(BaseModel):
    """Presence of each recommended security response header."""

    hsts: bool = False
    csp: bool = False
    x_content_type_options: bool = False
    x_frame_options: bool = False
    referrer_policy: bool = False
    permissions_policy: bool = False


class Vulnerability(BaseModel):
    """A known, unpatched CVE.

    Only carries the identifier, severity and official link. It never contains
    exploitation steps (see diagram 3.3).
    """

    cve_id: str
    severity: Severity
    product: str
    affected_version: str | None = None
    source_url: str


class SecurityResult(BaseModel):
    """Authoritative security result (security.py, diagram 3.3)."""

    version_known: bool  # False -> "sin datos suficientes"
    headers: SecurityHeaders = Field(default_factory=SecurityHeaders)
    observatory_grade: str | None = None  # MDN HTTP Observatory
    observatory_score: int | None = None
    vulnerabilities: list[Vulnerability] = Field(default_factory=list)
    has_known_vulns: bool = False
    notes: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# performance.py
# --------------------------------------------------------------------------- #
class PerformanceResult(BaseModel):
    """Core Web Vitals result (performance.py, diagram 3.4).

    performance.py owns its <48h snapshot: when a fresh snapshot exists it is
    returned as-is with ``from_snapshot=True`` and its original ``snapshot_at``.
    """

    source: CwvSource  # overall summary (FIELD/LAB/MIXED)
    lcp_ms: float | None = None
    inp_ms: float | None = None
    cls: float | None = None
    lcp_source: CwvSource | None = None  # per-metric provenance; None when the metric is None
    inp_source: CwvSource | None = None
    cls_source: CwvSource | None = None
    lighthouse_runs: int = 0  # 3 runs, median is taken
    crux_available: bool = False
    from_snapshot: bool = False  # served from a <48h snapshot
    snapshot_at: datetime
    notes: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# schema_org.py
# --------------------------------------------------------------------------- #
class SchemaCheck(BaseModel):
    """One of the 12 structured-data validations from geo-schema."""

    id: str
    label: str
    points: float
    max_points: float
    notes: list[str] = Field(default_factory=list)


class SchemaResult(BaseModel):
    """Structured-data validation result (schema_org.py)."""

    detected_types: list[str] = Field(default_factory=list)
    format: str = "none"  # json-ld | microdata | rdfa | mixed | none
    json_ld_valid: bool = False
    server_rendered: bool = False
    checks: list[SchemaCheck] = Field(default_factory=list)  # the 12 validations
    score: float = 0.0  # 0-100


# --------------------------------------------------------------------------- #
# keywords.py
# --------------------------------------------------------------------------- #
class KeywordSuggestion(BaseModel):
    """A single suggested search query with the on-page signal it came from."""

    query: str
    source: str  # title | meta | h1 | schema_type | location
    notes: list[str] = Field(default_factory=list)


class KeywordsResult(BaseModel):
    """Deterministic search-suggestion result (keywords.py)."""

    signals: dict[str, str | None] = Field(default_factory=dict)
    suggestions: list[KeywordSuggestion] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# citability.py
# --------------------------------------------------------------------------- #
class CitabilityResult(BaseModel):
    """AI-citability result (citability.py).

    Thin wrapper over citability_scorer.py; the existing formula is not
    rewritten. Feeds the 5th category of the final weighted score.
    """

    score: float = 0.0  # 0-100, page-level average
    blocks_analyzed: int = 0
    optimal_length_passages: int = 0
    grade_distribution: dict[str, int] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# orchestrator.py — gates + aggregated result (diagram 3.1)
# --------------------------------------------------------------------------- #
class ScoreTier(str, Enum):
    """Gate 2 final-score band, 5 tramos (replaces the free-form tier string).

    Boundaries are inclusive on the lower end: EXCELLENT 90-100, GOOD 75-89,
    FAIR 60-74, POOR 40-59, CRITICAL 0-39.
    """

    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"  # 75-89
    FAIR = "fair"  # 60-74
    POOR = "poor"  # 40-59
    CRITICAL = "critical"  # 0-39


class LeadViabilityResult(BaseModel):
    """Gate 1: is there enough margin to make this a lead? (diagram 3.1)."""

    is_lead: bool  # False -> already solved, not a lead
    reason: str
    checked_dimensions: dict[str, float] = Field(default_factory=dict)


class WeightedScoreResult(BaseModel):
    """Gate 2: final weighted score across the 5 categories (diagram 3.1).

    ``breakdown`` carries every category, including the ones excluded from the
    weighting (a failed submodule, or performance measured but with no data):
    those appear with ``weight=0``/``points=0`` and a finding explaining the
    exclusion, so a redistributed weight is visible instead of vanishing.
    """

    final_score: float  # 0-100, weighted over the available categories
    tier: ScoreTier
    breakdown: list[WeightedDimension] = Field(default_factory=list)


class AuditResult(BaseModel):
    """Aggregated audit output, the return type of :func:`run_audit`."""

    domain: str
    reachability: Reachability
    retry_at: datetime | None = None  # set when UNREACHABLE (now + 24h)
    fetch: FetchResult
    tech_stack: TechStackResult | None = None
    technical: TechnicalResult | None = None
    security: SecurityResult | None = None
    performance: PerformanceResult | None = None
    schema_org: SchemaResult | None = None
    keywords: KeywordsResult | None = None
    citability: CitabilityResult | None = None
    lead_viability: LeadViabilityResult | None = None
    # Gate 2 is computed whenever at least one category is available, regardless
    # of is_lead (task 8, punto 6); None only when every category is missing.
    weighted_score: WeightedScoreResult | None = None
    # Per-submodule failures / skips: a failed submodule leaves its field None and
    # appends a line here; the rest of the audit still runs (task 8, punto 5).
    errors: list[str] = Field(default_factory=list)
    created_at: datetime
