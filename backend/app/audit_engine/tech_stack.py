"""Technology stack detection (diagram 3.2).

Two layers, kept apart on purpose (task 5, point 1), same shape as schema_org.py,
technical.py and performance.py:

* :func:`evaluate_tech_stack` — **pure and synchronous**. Receives the already
  gathered signals — the normalized wappalyzer-next detections for the static
  scan, optionally the detections found after a browser render, plus the raw
  response headers — and resolves them into a :class:`TechStackResult` with the
  detected technologies, a confidence level, and the CDN/origin verdict. No
  network, no browser, trivially unit-testable with fixtures.
* :func:`detect_tech_stack` — the **async shell**. Runs wappalyzer-next over the
  static fetch (``scan_type="balanced"``, HTTP only, no browser); if the static
  signatures are weak or contradictory it renders the page with a real browser
  (``scan_type="full"`` — wappalyzer-next launches its **own** headless Chromium
  via the extension, not shared with performance.py; that sharing is task 8) and
  re-evaluates with the post-JavaScript detections.

Why the pure layer consumes wappalyzer detections instead of raw meta/cookies:
wappalyzer-next only accepts a URL and does its own fetch + fingerprinting; it
does not expose the individual meta-generator / cookie signals, nor accept
pre-fetched HTML. So the shell runs it (the I/O + browser, like performance.py
runs Lighthouse) and the pure layer consumes its parsed per-technology
detections (name/version/categories/confidence), exactly as
:func:`performance.evaluate_performance` consumes parsed ``LighthouseRun``
objects rather than re-running Lighthouse. The raw ``fetch.headers`` are still
passed to the pure layer for the CDN/origin heuristic (task 5, point 2), since a
CDN edge in front of the origin is a header signal.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence

from pydantic import BaseModel, Field

from .models import Confidence, DetectedTechnology, FetchResult, Reachability, TechStackResult

# --------------------------------------------------------------------------- #
# Cuts outside the literal diagram (task 5, point 4 — declared in the closing)
# --------------------------------------------------------------------------- #
# wappalyzer-next reports a 0-100 confidence per technology. These map it to the
# HIGH/MEDIUM/LOW enum and drive the "clear signature?" decision of diagram 3.2.
_HIGH_CONF = 90  # per-tech wappalyzer confidence >= this -> Confidence.HIGH
_MED_CONF = 50  # ... >= this -> MEDIUM, else LOW

# wappalyzer scan modes: "balanced" is HTTP-only (no browser); "full" launches a
# headless Chromium via the wappalyzer extension = the "render with Playwright"
# node of diagram 3.2. Its `timeout` is the per-page load budget for the render.
_STATIC_SCAN = "balanced"
_RENDER_SCAN = "full"
_RENDER_TIMEOUT_S = 30

# Categories that actually identify the stack (a CMS/framework/language/server),
# as opposed to analytics, tag managers, fonts, CDNs, etc. — used to decide
# `identified` and confidence, not merely "did wappalyzer find *anything*".
_IDENTIFYING_CATEGORIES = {
    "CMS",
    "Ecommerce",
    "Web frameworks",
    "JavaScript frameworks",
    "Static site generator",
    "Programming languages",
    "Web servers",
    "Page builders",
    "Blogs",
    "Wikis",
    "PaaS",
}
_CMS_CATEGORY = "CMS"
_CDN_CATEGORY = "CDN"

# Categories that mean "a standalone frontend/app framework is serving the page".
# A strong CMS signature together with a strong signature from one of these is
# the other contradiction of diagram 3.2's node B — its own casuística: "tema/CMS
# de base pero frontend headless custom encima" (e.g. WordPress + React/Next.js).
# A classic CMS does not deliver its frontend through a separate app framework,
# so seeing both strongly means the static scan alone cannot settle it and the
# render must run. "Web frameworks" (Next.js, but also Django/Express) is
# included on purpose: a full CMS next to any strong standalone framework is
# equally contradictory.
_FRONTEND_FRAMEWORK_CATEGORIES = {
    "JavaScript frameworks",
    "Web frameworks",
    "Static site generator",
}

# Own header heuristic for an edge/proxy in front of the origin (task 5, point 2):
# these response headers are added by a CDN/edge, so the origin server is not
# directly visible. Keyed by header name (lower-case) -> CDN label.
_CDN_HEADER_HINTS: dict[str, str] = {
    "cf-ray": "Cloudflare",
    "cf-cache-status": "Cloudflare",
    "x-amz-cf-id": "Amazon CloudFront",
    "x-amz-cf-pop": "Amazon CloudFront",
    "x-served-by": "Fastly/Varnish",
    "x-fastly-request-id": "Fastly",
    "x-akamai-transformed": "Akamai",
    "x-akamai-request-id": "Akamai",
    "fly-request-id": "Fly.io",
    "x-vercel-id": "Vercel",
    "x-nf-request-id": "Netlify",
    "x-sucuri-id": "Sucuri",
}
# `Server` header tokens that name an edge/CDN rather than the origin software.
_CDN_SERVER_TOKENS = (
    "cloudflare",
    "cloudfront",
    "akamai",
    "fastly",
    "varnish",
    "vercel",
    "netlify",
    "sucuri",
    "incapsula",
    "keycdn",
)


# --------------------------------------------------------------------------- #
# Raw input to the pure layer (the shell produces these from wappalyzer-next)
# --------------------------------------------------------------------------- #
class StackSignal(BaseModel):
    """One normalized wappalyzer-next detection — the pure layer's input unit.

    Analogous to performance.py's ``LighthouseRun``: the parsed output of the
    external tool, produced by the async shell and consumed by the pure function.
    ``confidence`` is wappalyzer's raw 0-100 per-technology score; the pure layer
    maps it to the :class:`Confidence` enum.
    """

    name: str
    version: str | None = None
    categories: list[str] = Field(default_factory=list)
    confidence: int = 100


# --------------------------------------------------------------------------- #
# Pure layer
# --------------------------------------------------------------------------- #
def evaluate_tech_stack(
    static_signals: Sequence[StackSignal],
    headers: Mapping[str, str] | None = None,
    *,
    rendered_signals: Sequence[StackSignal] | None = None,
) -> TechStackResult:
    """Resolve wappalyzer detections + response headers into a TechStackResult.

    Pure and synchronous: no network, no browser. ``static_signals`` are the
    detections from the HTTP-only scan; ``rendered_signals`` are the detections
    after a browser render — pass ``None`` for the pre-render evaluation and a
    (possibly empty) sequence once a render has been done, so the "not even after
    rendering" note can be produced. ``headers`` are the raw response headers
    from the initial fetch, used for the CDN/origin heuristic.

    Confidence follows diagram 3.2's node B: HIGH ("firmas claras") when an
    identifying technology (CMS/framework/language/server) is detected with a
    strong per-tech confidence and there is no contradiction; MEDIUM when the
    identifying signals are weak or contradictory; LOW when nothing identifying is
    found at all ("stack no identificado").
    """
    headers = headers or {}
    rendered_done = rendered_signals is not None
    merged = _merge_signals(static_signals, rendered_signals or [])

    behind_cdn, cdn_label = _detect_cdn(merged, headers)
    technologies = [_to_detected(s) for s in merged]
    identifying = [s for s in merged if _is_identifying(s)]
    cms = _pick_cms(merged)

    notes: list[str] = []
    if rendered_done:
        notes.append(
            "Firmas estáticas débiles o contradictorias: se renderizó la página con "
            "navegador (Chromium propio de wappalyzer-next, scan 'full') y se reevaluó "
            "con el DOM tras ejecutar JavaScript."
        )

    if not identifying:
        identified = False
        confidence = Confidence.LOW
        if rendered_done:
            notes.append(
                "Stack no identificado ni siquiera tras renderizar con navegador "
                "(posible build minificado/ofuscado o SPA sin firmas reconocibles); "
                "confianza baja."
            )
        else:
            notes.append("Stack no identificado a partir de las firmas estáticas; confianza baja.")
    else:
        identified = True
        multi_cms, contra_names = _cms_contradiction(identifying)
        headless, headless_cms, headless_fe = _headless_contradiction(identifying)
        strong = any(s.confidence >= _HIGH_CONF for s in identifying)
        if multi_cms:
            confidence = Confidence.MEDIUM
            notes.append(
                "Firmas contradictorias: se detectó más de un CMS "
                f"({', '.join(contra_names)}); un sitio rara vez usa dos. Se reportan "
                "todos con confianza media."
            )
        elif headless:
            pair = f"CMS ({', '.join(headless_cms)}) y framework de frontend ({', '.join(headless_fe)})"
            if rendered_done and _frontend_confirmed(rendered_signals or []):
                confidence = Confidence.HIGH
                notes.append(
                    f"{pair} con firmas fuertes de ambos, confirmadas tras renderizar: "
                    "compatible con arquitectura headless (el CMS sirve el contenido, "
                    "el framework renderiza el frontend)."
                )
            elif rendered_done:
                confidence = Confidence.MEDIUM
                notes.append(
                    f"Firmas contradictorias: {pair} fuertes a la vez, pero el framework "
                    "no se confirmó en el DOM renderizado; se reporta con confianza media."
                )
            else:
                confidence = Confidence.MEDIUM
                notes.append(
                    f"Firmas contradictorias: {pair} con firmas fuertes a la vez — posible "
                    "frontend headless sobre CMS base; hace falta renderizar para confirmarlo."
                )
        elif strong:
            confidence = Confidence.HIGH
            notes.append("Firmas claras de stack (alta confianza).")
        else:
            confidence = Confidence.MEDIUM
            notes.append("Firmas de stack presentes pero débiles (confianza media).")
        if cms:
            notes.append(f"CMS detectado: {cms}.")

    if behind_cdn:
        notes.append(
            f"Detrás de CDN/proxy ({cdn_label}): el servidor de origen no es visible "
            "directamente, solo el edge."
        )

    return TechStackResult(
        identified=identified,
        technologies=technologies,
        cms=cms,
        behind_cdn=behind_cdn,
        origin_visible=not behind_cdn,
        confidence=confidence,
        notes=notes,
    )


def _merge_signals(
    static: Sequence[StackSignal], rendered: Sequence[StackSignal]
) -> list[StackSignal]:
    """Union static + rendered detections, de-duplicated by name (case-insensitive).

    On a collision: keep the highest wappalyzer confidence, prefer a concrete
    version over an empty one, and union the categories. Static order is
    preserved; technologies that only show up after JS keep their rendered order.
    """
    merged: dict[str, StackSignal] = {}
    for sig in list(static) + list(rendered):
        key = sig.name.strip().lower()
        if not key:
            continue
        existing = merged.get(key)
        if existing is None:
            merged[key] = sig.model_copy()
            continue
        merged[key] = StackSignal(
            name=existing.name,
            version=existing.version or sig.version,
            categories=list(dict.fromkeys(existing.categories + sig.categories)),
            confidence=max(existing.confidence, sig.confidence),
        )
    return list(merged.values())


def _to_detected(sig: StackSignal) -> DetectedTechnology:
    return DetectedTechnology(
        name=sig.name,
        version=(sig.version or None),
        categories=list(sig.categories),
        confidence=_conf_enum(sig.confidence),
    )


def _conf_enum(score: int) -> Confidence:
    if score >= _HIGH_CONF:
        return Confidence.HIGH
    if score >= _MED_CONF:
        return Confidence.MEDIUM
    return Confidence.LOW


def _is_identifying(sig: StackSignal) -> bool:
    return bool(set(sig.categories) & _IDENTIFYING_CATEGORIES)


def _pick_cms(signals: Sequence[StackSignal]) -> str | None:
    """Highest-confidence technology carrying the CMS category, if any."""
    cms = [s for s in signals if _CMS_CATEGORY in s.categories]
    if not cms:
        return None
    return max(cms, key=lambda s: s.confidence).name


def _cms_contradiction(identifying: Sequence[StackSignal]) -> tuple[bool, list[str]]:
    """Two or more distinct CMSs is a contradiction (a site rarely runs two).

    Deliberately scoped to the CMS category only: WordPress + WooCommerce (CMS +
    Ecommerce) is a normal pairing, and multiple Ecommerce-tagged widgets would
    false-positive, so Ecommerce is not treated as a contradiction signal.
    """
    cms_names = sorted({s.name for s in identifying if _CMS_CATEGORY in s.categories})
    if len(cms_names) >= 2:
        return True, cms_names
    return False, []


def _headless_contradiction(
    identifying: Sequence[StackSignal],
) -> tuple[bool, list[str], list[str]]:
    """A strong CMS together with a strong frontend framework is also contradictory.

    Covers diagram 3.2's own casuística of "tema/CMS de base pero frontend
    headless custom encima" (WordPress + React/Next.js with strong signatures of
    both): the static scan alone cannot settle whether the framework is the real
    frontend or an incidental widget, so the render must run. Requiring **both**
    sides at >= _HIGH_CONF is the cut that separates "framework incidental" from
    "headless real": a stray widget with a weak fingerprint does not trip it, and
    when it does fingerprint strongly the only cost is one render, after which
    the combo is either confirmed (headless, HIGH) or downgraded (MEDIUM).
    """
    cms_names = sorted(
        {
            s.name
            for s in identifying
            if _CMS_CATEGORY in s.categories and s.confidence >= _HIGH_CONF
        }
    )
    fe_names = sorted(
        {s.name for s in identifying if _is_frontend_framework(s) and s.confidence >= _HIGH_CONF}
    )
    if cms_names and fe_names:
        return True, cms_names, fe_names
    return False, [], []


def _is_frontend_framework(sig: StackSignal) -> bool:
    return (
        bool(set(sig.categories) & _FRONTEND_FRAMEWORK_CATEGORIES)
        and _CMS_CATEGORY not in sig.categories
    )


def _frontend_confirmed(rendered: Sequence[StackSignal]) -> bool:
    """Did the post-JS scan corroborate a strong frontend framework?

    Confirmation requires the framework to fingerprint strongly among the
    *rendered* detections, not merely survive the merge from the static scan: if
    the render ran and found no framework at runtime, the combo stays
    contradictory (confianza media) instead of being upgraded to headless.
    """
    return any(s.confidence >= _HIGH_CONF and _is_frontend_framework(s) for s in rendered)


def _detect_cdn(signals: Sequence[StackSignal], headers: Mapping[str, str]) -> tuple[bool, str]:
    """Behind a CDN/proxy? -> (behind_cdn, comma-separated labels).

    Combines wappalyzer's own CDN-category detections with a header heuristic
    (task 5, point 2): CDN-added response headers (``cf-ray``, ``x-amz-cf-id``,
    ``x-served-by``, …) and edge tokens in the ``Server`` header.
    """
    labels: list[str] = [s.name for s in signals if _CDN_CATEGORY in s.categories]

    headers_ci = {k.lower(): (v or "") for k, v in headers.items()}
    for header, label in _CDN_HEADER_HINTS.items():
        if header in headers_ci:
            labels.append(label)
    server = headers_ci.get("server", "").lower()
    for token in _CDN_SERVER_TOKENS:
        if token in server:
            labels.append(token.capitalize())

    labels = list(dict.fromkeys(labels))
    return bool(labels), ", ".join(labels)


# --------------------------------------------------------------------------- #
# Async shell: static scan -> render only if weak/contradictory (diagram 3.2)
# --------------------------------------------------------------------------- #
async def detect_tech_stack(
    fetch: FetchResult,
    *,
    run_static: Callable[[str], Awaitable[Sequence[StackSignal]]] | None = None,
    run_rendered: Callable[[str], Awaitable[Sequence[StackSignal]]] | None = None,
) -> TechStackResult:
    """Detect CMS / frameworks / server tech for the fetched site (diagram 3.2).

    Runs wappalyzer-next over the static fetch first (HTTP only, no browser). If
    the resulting confidence is not HIGH — weak or contradictory signatures — it
    renders the page with a real browser and re-evaluates, exactly as diagram 3.2
    prescribes. Flags ``behind_cdn`` / ``origin_visible`` from headers, records a
    confidence level, and returns ``identified=False`` when no stack can be named.

    ``run_static``/``run_rendered`` are injectable so this shell is testable
    without wappalyzer-next or a real browser (task 5, point 5); they default to
    the real wappalyzer-next runners (``balanced`` and ``full`` scans).
    """
    if fetch.reachability != Reachability.OK:
        return TechStackResult(
            identified=False,
            confidence=Confidence.LOW,
            notes=["Sitio no alcanzable: no se pudo detectar el stack tecnológico."],
        )

    run_static = run_static or _run_static_scan
    run_rendered = run_rendered or _run_rendered_scan
    url = _target_url(fetch)
    headers = fetch.headers or {}

    static_signals = list(await run_static(url))
    result = evaluate_tech_stack(static_signals, headers)
    if result.confidence == Confidence.HIGH:
        return result

    rendered_signals = list(await run_rendered(url))
    return evaluate_tech_stack(static_signals, headers, rendered_signals=rendered_signals)


def _target_url(fetch: FetchResult) -> str:
    target = fetch.final_url or fetch.domain or ""
    if target and "//" not in target:
        target = "https://" + target
    return target


# --------------------------------------------------------------------------- #
# Real wappalyzer-next runners (lazy import: absent tool degrades, never crashes)
# --------------------------------------------------------------------------- #
async def _run_static_scan(url: str) -> list[StackSignal]:
    return await asyncio.to_thread(_analyze, url, _STATIC_SCAN)


async def _run_rendered_scan(url: str) -> list[StackSignal]:
    return await asyncio.to_thread(_analyze, url, _RENDER_SCAN)


def _analyze(url: str, scan_type: str) -> list[StackSignal]:
    """Run wappalyzer-next and normalize its output.

    Returns an empty list (which the pure layer degrades to "stack no
    identificado", confidence baja) if the dependency is missing or the scan
    fails — never raises, so a missing browser or a flaky target does not abort
    the whole audit.
    """
    if not url:
        return []
    try:
        from wappalyzer import analyze
    except ImportError:
        return []
    try:
        raw = analyze(url=url, scan_type=scan_type, timeout=_RENDER_TIMEOUT_S)
    except Exception:
        return []
    return _normalize(raw, url)


def _normalize(raw: object, url: str) -> list[StackSignal]:
    """wappalyzer ``{url: {tech: {version, confidence, categories, groups}}}`` -> [StackSignal]."""
    if not isinstance(raw, dict) or not raw:
        return []
    # wappalyzer keys by the URL it actually fetched (post-redirect it can differ
    # from ours); take our entry if present, else the first one.
    per_url = raw.get(url)
    if per_url is None:
        per_url = next(iter(raw.values()), {})
    if not isinstance(per_url, dict):
        return []

    signals: list[StackSignal] = []
    for name, info in per_url.items():
        info = info if isinstance(info, dict) else {}
        version = (str(info.get("version") or "")).strip() or None
        try:
            confidence = int(info.get("confidence", 100))
        except (TypeError, ValueError):
            confidence = 100
        raw_cats = info.get("categories") or []
        categories = [str(c) for c in raw_cats] if isinstance(raw_cats, list) else []
        signals.append(
            StackSignal(
                name=str(name), version=version, categories=categories, confidence=confidence
            )
        )
    return signals
