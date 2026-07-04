"""Security audit: headers + known CVEs (diagram 3.3).

Authoritative security result. When the stack version is not visible it reports
``version_known=False`` ("sin datos suficientes") instead of inventing risk. It
reports CVE id, severity and the official source link only — never exploitation
steps; that restriction lives in the :class:`Vulnerability` model itself.

Two layers, kept apart on purpose (task 6, point 1), same shape as
schema_org.py, technical.py, performance.py and tech_stack.py:

* :func:`evaluate_security` — **pure and synchronous**. Receives the raw
  response headers from the initial fetch, the already-resolved vulnerability
  scan (WPScan or OSV.dev, normalized by the shell) and the grade/score already
  returned by MDN HTTP Observatory, and assembles the final
  :class:`SecurityResult`. No network, trivially unit-testable with fixtures.
* :func:`scan_security` — the **async shell**. Decides the WordPress-vs-OSV
  branch from ``stack.cms`` (task 5), calls Observatory for the headers grade
  in both branches, resolves the visible version (no visible version ->
  ``version_known=False`` and **no** CVE scanner is called at all — there is
  nothing to query with), and delegates the assembly to the pure layer.

WPScan's free API is for non-commercial use and needs a key (design doc,
section 2): when ``WPSCAN_API_KEY`` is not set the WordPress branch degrades
cleanly to "sin datos de CVE", mirroring how performance.py degrades without
``CRUX_API_KEY`` — it never fails the whole audit.

Observatory rate-limits at 1 scan/minute/host and caches on its own side, so
this module keeps no local snapshot store (unlike performance.py, where the
caching problem was ours to solve).
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Awaitable, Callable, Mapping, Sequence
from urllib.parse import urlparse

import requests
from pydantic import BaseModel, Field

from .models import (
    FetchResult,
    Reachability,
    SecurityHeaders,
    SecurityResult,
    Severity,
    TechStackResult,
    Vulnerability,
)

# --------------------------------------------------------------------------- #
# Cuts outside the literal diagram (task 6, point 4 — declared in the closing)
# --------------------------------------------------------------------------- #
_OBSERVATORY_ENDPOINT = "https://observatory-api.mdn.mozilla.net/api/v2/scan"
_OBSERVATORY_TIMEOUT_S = 30  # a cold scan runs server-side and takes a few seconds
_WPSCAN_ENDPOINT = "https://wpscan.com/api/v3/wordpresses/{version}"
_WPSCAN_TIMEOUT_S = 15
_OSV_ENDPOINT = "https://api.osv.dev/v1/query"
_OSV_TIMEOUT_S = 15

_WORDPRESS = "wordpress"

# Categories whose product+version are worth a CVE lookup in the non-WordPress
# branch ("consulta por producto + versión"): the stack-identifying ones, not
# analytics/fonts/tag managers. Every versioned identifying technology is
# queried, not just the CMS — OSV is keyed per product.
_CVE_QUERY_CATEGORIES = {
    "CMS",
    "Ecommerce",
    "Web frameworks",
    "JavaScript frameworks",
    "Static site generator",
    "Programming languages",
    "Web servers",
    "Blogs",
    "Wikis",
}

# wappalyzer names -> OSV package names where they differ. Lookups without an
# ecosystem match any ecosystem by name, so unmapped names fall back to
# lowercase as-is (best effort; a miss degrades to "no data", never to a crash).
_OSV_PACKAGE_ALIASES = {
    "next.js": "next",
    "nuxt.js": "nuxt",
    "vue.js": "vue",
    "angular": "@angular/core",
}

# Official links only (diagram 3.3): NVD detail page for CVEs, the OSV entry
# page for advisories without a CVE alias.
_NVD_DETAIL_URL = "https://nvd.nist.gov/vuln/detail/{cve}"
_OSV_DETAIL_URL = "https://osv.dev/vulnerability/{id}"

# SecurityHeaders field -> (response header, label used in notes). The presence
# check is our own deterministic pass over fetch.headers; Observatory's grade is
# the external validation on top, not a replacement.
_SECURITY_HEADER_FIELDS: dict[str, tuple[str, str]] = {
    "hsts": ("strict-transport-security", "Strict-Transport-Security"),
    "csp": ("content-security-policy", "Content-Security-Policy"),
    "x_content_type_options": ("x-content-type-options", "X-Content-Type-Options"),
    "x_frame_options": ("x-frame-options", "X-Frame-Options"),
    "referrer_policy": ("referrer-policy", "Referrer-Policy"),
    "permissions_policy": ("permissions-policy", "Permissions-Policy"),
}


# --------------------------------------------------------------------------- #
# Raw inputs to the pure layer (the shell produces these from the APIs)
# --------------------------------------------------------------------------- #
class ObservatoryReport(BaseModel):
    """Parsed MDN HTTP Observatory response — one of the pure layer's inputs.

    ``failed=True`` means the call was attempted and produced no grade (timeout,
    network error, malformed body); the audit degrades with a note instead of
    failing.
    """

    grade: str | None = None
    score: int | None = None
    failed: bool = False
    error: str | None = None


class VulnerabilityScan(BaseModel):
    """Outcome of the CVE lookup (WPScan or OSV.dev), normalized by the shell.

    The pure layer receives ``None`` instead of an instance when no scanner was
    invoked at all (version not visible). ``failed=True`` covers both a scanner
    error and a scanner that could not run (WPSCAN_API_KEY not configured) —
    ``error`` says which. ``error`` alongside ``failed=False`` marks a partial
    result (some per-product OSV queries failed, others answered).
    """

    source: str  # "WPScan" | "OSV.dev"
    vulnerabilities: list[Vulnerability] = Field(default_factory=list)
    failed: bool = False
    error: str | None = None


# --------------------------------------------------------------------------- #
# Pure layer
# --------------------------------------------------------------------------- #
def evaluate_security(
    headers: Mapping[str, str] | None,
    scan: VulnerabilityScan | None,
    observatory: ObservatoryReport | None,
    *,
    version_known: bool,
) -> SecurityResult:
    """Assemble the raw header/CVE/Observatory inputs into a SecurityResult.

    Pure and synchronous: no network. ``headers`` are the raw response headers
    from the initial fetch; ``scan`` is the already-resolved CVE lookup (``None``
    when no scanner ran because the version is not visible); ``observatory`` is
    the grade/score already returned by MDN HTTP Observatory (``None`` or
    ``failed=True`` degrade to a note, never to a failed audit).

    ``has_known_vulns`` is True when the scan reports **any** unpatched CVE,
    regardless of severity — diagram 3.3's node H asks "¿CVE conocido sin
    parchear?", not "¿CVE grave?"; severity is reported per CVE, not used as a
    filter. Absence of data (version unknown, scanner failed or unconfigured)
    always resolves to ``has_known_vulns=False`` plus an explicit note: no data
    is never presented as risk.
    """
    notes: list[str] = []

    sec_headers, missing = _check_headers(headers or {})
    if missing:
        notes.append(
            f"Cabeceras de seguridad ausentes ({len(missing)}/{len(_SECURITY_HEADER_FIELDS)}): "
            f"{', '.join(missing)}."
        )
    else:
        notes.append("Las 6 cabeceras de seguridad recomendadas están presentes.")

    grade: str | None = None
    score: int | None = None
    if observatory is None or observatory.failed or observatory.grade is None:
        detail = (observatory.error if observatory else None) or "sin respuesta"
        notes.append(
            f"MDN HTTP Observatory no disponible ({detail}); las cabeceras se evalúan "
            "solo con la comprobación propia."
        )
    else:
        grade, score = observatory.grade, observatory.score
        notes.append(f"MDN HTTP Observatory: nota {grade} (puntuación {score}).")

    vulnerabilities: list[Vulnerability] = []
    has_known_vulns = False
    if not version_known:
        notes.append(
            "Versión del stack no visible en headers/meta/JS: sin datos suficientes "
            "para consultar CVEs. No se inventa riesgo."
        )
    elif scan is None or scan.failed:
        source = scan.source if scan else "CVE"
        detail = (scan.error if scan else None) or "sin respuesta"
        notes.append(
            f"Consulta de CVEs ({source}) sin datos: {detail}. Sin datos no se asume riesgo."
        )
    else:
        if scan.error:
            notes.append(f"Consulta de CVEs incompleta ({scan.source}): {scan.error}.")
        if scan.vulnerabilities:
            vulnerabilities = list(scan.vulnerabilities)
            has_known_vulns = True
            notes.append(
                f"{len(vulnerabilities)} CVE(s) conocidas sin parchear según {scan.source}: "
                "se reporta identificador, severidad y enlace oficial, nunca pasos de "
                "explotación."
            )
        else:
            notes.append(f"Sin vulnerabilidades conocidas a la fecha según {scan.source}.")

    return SecurityResult(
        version_known=version_known,
        headers=sec_headers,
        observatory_grade=grade,
        observatory_score=score,
        vulnerabilities=vulnerabilities,
        has_known_vulns=has_known_vulns,
        notes=notes,
    )


def _check_headers(headers: Mapping[str, str]) -> tuple[SecurityHeaders, list[str]]:
    """Presence of each recommended header (case-insensitive, empty value = absent)."""
    present = {k.strip().lower() for k, v in headers.items() if (v or "").strip()}
    values = {field: header in present for field, (header, _) in _SECURITY_HEADER_FIELDS.items()}
    missing = [label for field, (_, label) in _SECURITY_HEADER_FIELDS.items() if not values[field]]
    return SecurityHeaders(**values), missing


def _merge_scans(scans: Sequence[VulnerabilityScan]) -> VulnerabilityScan:
    """Fold the per-product OSV scans into one: union of CVEs, de-duplicated.

    ``failed`` only when *every* per-product query failed; a partial failure
    keeps the successful subset and carries the failures in ``error`` so the
    pure layer can note the result as incomplete.
    """
    vulns: list[Vulnerability] = []
    seen: set[str] = set()
    errors: list[str] = []
    answered = 0
    for scan in scans:
        if scan.failed:
            errors.append(scan.error or "sin respuesta")
            continue
        answered += 1
        for vuln in scan.vulnerabilities:
            if vuln.cve_id not in seen:
                seen.add(vuln.cve_id)
                vulns.append(vuln)
    if answered == 0:
        return VulnerabilityScan(
            source="OSV.dev", failed=True, error="; ".join(errors) or "sin respuesta"
        )
    return VulnerabilityScan(
        source="OSV.dev", vulnerabilities=vulns, error="; ".join(errors) or None
    )


# --------------------------------------------------------------------------- #
# Async shell: Observatory always; WPScan/OSV only with a visible version
# --------------------------------------------------------------------------- #
async def scan_security(
    fetch: FetchResult,
    stack: TechStackResult,
    *,
    fetch_observatory: Callable[[str], Awaitable[ObservatoryReport]] | None = None,
    run_wpscan: Callable[[str, str], Awaitable[VulnerabilityScan]] | None = None,
    run_osv: Callable[[str, str], Awaitable[VulnerabilityScan]] | None = None,
) -> SecurityResult:
    """Assess security headers and known vulnerabilities (diagram 3.3).

    The branch is decided by ``stack.cms``: WordPress goes to WPScan (core
    version, ``WPSCAN_API_KEY`` required — absent key degrades with a note),
    everything else to OSV.dev per versioned identifying product. Headers are
    graded via MDN HTTP Observatory in both branches. When no visible version
    exists, ``version_known=False`` and **no** CVE scanner is called at all.

    ``fetch_observatory``/``run_wpscan``/``run_osv`` are injectable so this
    shell is testable without hitting any real API (task 6, point 5); they
    default to the real clients. ``run_wpscan`` receives ``(version, api_key)``;
    ``run_osv`` receives ``(product, version)``. Each call degrades
    independently: an Observatory timeout does not cancel the CVE lookup and
    vice versa — each failure becomes its own note.
    """
    if fetch.reachability != Reachability.OK:
        return SecurityResult(
            version_known=False,
            notes=["Sitio no alcanzable: no se pudo auditar la seguridad."],
        )

    fetch_observatory = fetch_observatory or _fetch_observatory
    run_wpscan = run_wpscan or _run_wpscan
    run_osv = run_osv or _run_osv

    observatory = await fetch_observatory(_host(fetch))

    scan: VulnerabilityScan | None
    if (stack.cms or "").strip().lower() == _WORDPRESS:
        version = _wordpress_version(stack)
        version_known = version is not None
        if version is None:
            scan = None
        elif not (api_key := os.getenv("WPSCAN_API_KEY")):
            scan = VulnerabilityScan(
                source="WPScan",
                failed=True,
                error="WPScan no configurado (falta WPSCAN_API_KEY), sin datos de CVE "
                "para WordPress",
            )
        else:
            scan = await run_wpscan(version, api_key)
    else:
        products = _versioned_products(stack)
        version_known = bool(products)
        if not products:
            scan = None
        else:
            scan = _merge_scans([await run_osv(name, version) for name, version in products])

    return evaluate_security(fetch.headers, scan, observatory, version_known=version_known)


def _host(fetch: FetchResult) -> str:
    target = fetch.final_url or fetch.domain or ""
    if "//" in target:
        return urlparse(target).hostname or ""
    return target.split("/", 1)[0]


def _wordpress_version(stack: TechStackResult) -> str | None:
    for tech in stack.technologies:
        if tech.name.strip().lower() == _WORDPRESS and tech.version:
            return tech.version
    return None


def _versioned_products(stack: TechStackResult) -> list[tuple[str, str]]:
    """Identifying technologies with a visible version — what OSV can be asked about."""
    return [
        (t.name, t.version)
        for t in stack.technologies
        if t.version and (set(t.categories) & _CVE_QUERY_CATEGORIES)
    ]


# --------------------------------------------------------------------------- #
# Real MDN HTTP Observatory client (degrades to a failed report, never raises)
# --------------------------------------------------------------------------- #
async def _fetch_observatory(host: str) -> ObservatoryReport:
    if not host:
        return ObservatoryReport(failed=True, error="host vacío")
    try:
        return await asyncio.to_thread(_sync_fetch_observatory, host)
    except Exception as exc:
        return ObservatoryReport(failed=True, error=str(exc)[:200])


def _sync_fetch_observatory(host: str) -> ObservatoryReport:
    # POST triggers a scan; Observatory itself serves a cached recent scan when
    # one exists (1 scan/minute/host limit on their side).
    resp = requests.post(
        _OBSERVATORY_ENDPOINT, params={"host": host}, timeout=_OBSERVATORY_TIMEOUT_S
    )
    resp.raise_for_status()
    body = resp.json()
    if body.get("error"):
        return ObservatoryReport(failed=True, error=str(body["error"]))
    grade = body.get("grade")
    if grade is None:
        return ObservatoryReport(failed=True, error="respuesta sin nota (grade)")
    score = body.get("score")
    return ObservatoryReport(grade=str(grade), score=int(score) if score is not None else None)


# --------------------------------------------------------------------------- #
# Real WPScan client (WordPress core CVEs by version)
# --------------------------------------------------------------------------- #
async def _run_wpscan(version: str, api_key: str) -> VulnerabilityScan:
    try:
        return await asyncio.to_thread(_sync_run_wpscan, version, api_key)
    except Exception as exc:
        return VulnerabilityScan(source="WPScan", failed=True, error=str(exc)[:200])


def _sync_run_wpscan(version: str, api_key: str) -> VulnerabilityScan:
    # WPScan keys core versions without dots: 6.4.1 -> "641".
    resp = requests.get(
        _WPSCAN_ENDPOINT.format(version=version.replace(".", "")),
        headers={"Authorization": f"Token token={api_key}"},
        timeout=_WPSCAN_TIMEOUT_S,
    )
    if resp.status_code == 404:
        return VulnerabilityScan(
            source="WPScan", failed=True, error=f"versión {version} desconocida para WPScan"
        )
    resp.raise_for_status()
    entry = resp.json().get(version) or {}
    vulns: list[Vulnerability] = []
    for raw in entry.get("vulnerabilities") or []:
        cves = (raw.get("references") or {}).get("cve") or []
        if not cves:
            continue  # the model is CVE-centric; advisories without a CVE id are skipped
        cve_id = str(cves[0])
        if not cve_id.upper().startswith("CVE-"):
            cve_id = f"CVE-{cve_id}"
        vulns.append(
            Vulnerability(
                cve_id=cve_id,
                severity=Severity.UNKNOWN,  # WPScan payloads don't carry a CVSS bucket
                product="WordPress",
                affected_version=version,
                source_url=_NVD_DETAIL_URL.format(cve=cve_id),
            )
        )
    return VulnerabilityScan(source="WPScan", vulnerabilities=vulns)


# --------------------------------------------------------------------------- #
# Real OSV.dev client (per product + version, no key needed)
# --------------------------------------------------------------------------- #
async def _run_osv(product: str, version: str) -> VulnerabilityScan:
    try:
        return await asyncio.to_thread(_sync_run_osv, product, version)
    except Exception as exc:
        return VulnerabilityScan(
            source="OSV.dev", failed=True, error=f"{product} {version}: {str(exc)[:200]}"
        )


def _sync_run_osv(product: str, version: str) -> VulnerabilityScan:
    package = _OSV_PACKAGE_ALIASES.get(product.strip().lower(), product.strip().lower())
    resp = requests.post(
        _OSV_ENDPOINT,
        json={"package": {"name": package}, "version": version},
        timeout=_OSV_TIMEOUT_S,
    )
    resp.raise_for_status()
    vulns = []
    for raw in resp.json().get("vulns") or []:
        vuln = _osv_vulnerability(raw, product, version)
        if vuln is not None:
            vulns.append(vuln)
    return VulnerabilityScan(source="OSV.dev", vulnerabilities=vulns)


def _osv_vulnerability(raw: dict, product: str, version: str) -> Vulnerability | None:
    osv_id = str(raw.get("id") or "")
    ids = [osv_id, *(str(a) for a in raw.get("aliases") or [])]
    cve_id = next((i for i in ids if i.upper().startswith("CVE-")), None)
    if cve_id is not None:
        source_url = _NVD_DETAIL_URL.format(cve=cve_id)
    elif osv_id:
        # No CVE alias: report the OSV/GHSA id with its own official entry page.
        cve_id, source_url = osv_id, _OSV_DETAIL_URL.format(id=osv_id)
    else:
        return None
    return Vulnerability(
        cve_id=cve_id,
        severity=_osv_severity(raw),
        product=product,
        affected_version=version,
        source_url=source_url,
    )


def _osv_severity(raw: dict) -> Severity:
    label = str((raw.get("database_specific") or {}).get("severity") or "").strip().upper()
    return {
        "CRITICAL": Severity.CRITICAL,
        "HIGH": Severity.HIGH,
        "MODERATE": Severity.MEDIUM,
        "MEDIUM": Severity.MEDIUM,
        "LOW": Severity.LOW,
    }.get(label, Severity.UNKNOWN)
