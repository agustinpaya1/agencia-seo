"""Tests for the security audit (audit_engine/security.py).

Two layers, tested separately (task 6, point 5):

* :func:`evaluate_security` — pure, synchronous, no network — exercised with
  fixtures (complete headers, absent headers, critical CVE, version not
  visible, failed/unconfigured scans).
* :func:`scan_security` — the async shell — exercised with fake
  Observatory/WPScan/OSV callables, so no real API is hit in the suite. Driven
  with ``asyncio.run`` directly (same style as test_tech_stack.py). Includes
  the explicit "sin WPSCAN_API_KEY" case and the "version_known=False -> no CVE
  scanner is called" case.
"""

import asyncio
from datetime import datetime, timezone

from backend.app.audit_engine.models import (
    Confidence,
    DetectedTechnology,
    FetchResult,
    Reachability,
    Severity,
    TechStackResult,
    Vulnerability,
)
from backend.app.audit_engine.security import (
    ObservatoryReport,
    VulnerabilityScan,
    evaluate_security,
    scan_security,
)

FULL_HEADERS = {
    "Strict-Transport-Security": "max-age=63072000",
    "Content-Security-Policy": "default-src 'self'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=()",
}


def make_fetch(
    *,
    reachability: Reachability = Reachability.OK,
    headers: dict[str, str] | None = None,
) -> FetchResult:
    return FetchResult(
        domain="example.com",
        reachability=reachability,
        status_code=200,
        final_url="https://example.com/",
        html="<html></html>",
        headers=headers or {},
        fetched_at=datetime.now(timezone.utc),
    )


def make_stack(
    *, cms: str | None = None, technologies: list[DetectedTechnology] | None = None
) -> TechStackResult:
    return TechStackResult(
        identified=bool(technologies),
        technologies=technologies or [],
        cms=cms,
        confidence=Confidence.HIGH,
    )


def tech(name: str, version: str | None = None, categories: list[str] | None = None):
    return DetectedTechnology(
        name=name, version=version, categories=categories or [], confidence=Confidence.HIGH
    )


def make_vuln(cve: str = "CVE-2024-0001", severity: Severity = Severity.CRITICAL):
    return Vulnerability(
        cve_id=cve,
        severity=severity,
        product="WordPress",
        affected_version="6.4",
        source_url=f"https://nvd.nist.gov/vuln/detail/{cve}",
    )


# --------------------------------------------------------------------------- #
# Pure layer
# --------------------------------------------------------------------------- #
class TestEvaluateSecurityPure:
    def test_complete_headers_all_present(self):
        result = evaluate_security(
            FULL_HEADERS,
            VulnerabilityScan(source="OSV.dev"),
            ObservatoryReport(grade="A+", score=105),
            version_known=True,
        )

        h = result.headers
        assert all(
            [
                h.hsts,
                h.csp,
                h.x_content_type_options,
                h.x_frame_options,
                h.referrer_policy,
                h.permissions_policy,
            ]
        )
        assert result.observatory_grade == "A+"
        assert result.observatory_score == 105
        assert any("presentes" in n for n in result.notes)

    def test_absent_headers_all_false_and_listed(self):
        result = evaluate_security(
            {"Content-Type": "text/html"},
            VulnerabilityScan(source="OSV.dev"),
            ObservatoryReport(grade="F", score=0),
            version_known=True,
        )

        h = result.headers
        assert not any(
            [
                h.hsts,
                h.csp,
                h.x_content_type_options,
                h.x_frame_options,
                h.referrer_policy,
                h.permissions_policy,
            ]
        )
        assert any("ausentes" in n and "Strict-Transport-Security" in n for n in result.notes)

    def test_critical_cve_sets_has_known_vulns(self):
        scan = VulnerabilityScan(source="WPScan", vulnerabilities=[make_vuln()])

        result = evaluate_security(
            FULL_HEADERS, scan, ObservatoryReport(grade="B", score=65), version_known=True
        )

        assert result.has_known_vulns is True
        assert result.vulnerabilities[0].cve_id == "CVE-2024-0001"
        assert result.vulnerabilities[0].severity == Severity.CRITICAL
        # Only id + severity + official link, never exploitation steps.
        assert any("nunca pasos de" in n for n in result.notes)

    def test_clean_scan_notes_no_known_vulns_to_date(self):
        result = evaluate_security(
            FULL_HEADERS,
            VulnerabilityScan(source="OSV.dev"),
            ObservatoryReport(grade="B", score=65),
            version_known=True,
        )

        assert result.has_known_vulns is False
        assert result.vulnerabilities == []
        assert any("Sin vulnerabilidades conocidas a la fecha" in n for n in result.notes)

    def test_version_not_visible_does_not_invent_risk(self):
        result = evaluate_security(
            FULL_HEADERS, None, ObservatoryReport(grade="B", score=65), version_known=False
        )

        assert result.version_known is False
        assert result.vulnerabilities == []
        assert result.has_known_vulns is False
        assert any("sin datos suficientes" in n for n in result.notes)

    def test_failed_scan_degrades_with_note(self):
        scan = VulnerabilityScan(
            source="WPScan",
            failed=True,
            error="WPScan no configurado (falta WPSCAN_API_KEY), sin datos de CVE para WordPress",
        )

        result = evaluate_security(
            FULL_HEADERS, scan, ObservatoryReport(grade="B", score=65), version_known=True
        )

        assert result.version_known is True  # the version WAS visible; the scanner wasn't
        assert result.has_known_vulns is False
        assert any("WPSCAN_API_KEY" in n for n in result.notes)

    def test_observatory_failure_degrades_with_note(self):
        result = evaluate_security(
            FULL_HEADERS,
            VulnerabilityScan(source="OSV.dev"),
            ObservatoryReport(failed=True, error="timeout"),
            version_known=True,
        )

        assert result.observatory_grade is None
        assert result.observatory_score is None
        assert any("Observatory no disponible" in n and "timeout" in n for n in result.notes)


# --------------------------------------------------------------------------- #
# Async shell — mocked Observatory/WPScan/OSV
# --------------------------------------------------------------------------- #
def make_fakes(calls: dict, *, wpscan_result: VulnerabilityScan | None = None):
    async def fake_observatory(host: str) -> ObservatoryReport:
        calls["observatory"].append(host)
        return ObservatoryReport(grade="B", score=65)

    async def fake_wpscan(version: str, api_key: str) -> VulnerabilityScan:
        calls["wpscan"].append((version, api_key))
        return wpscan_result or VulnerabilityScan(source="WPScan")

    async def fake_osv(product: str, version: str) -> VulnerabilityScan:
        calls["osv"].append((product, version))
        return VulnerabilityScan(source="OSV.dev")

    return fake_observatory, fake_wpscan, fake_osv


def empty_calls() -> dict:
    return {"observatory": [], "wpscan": [], "osv": []}


class TestScanSecurityShell:
    def test_wordpress_with_version_and_key_goes_to_wpscan(self, monkeypatch):
        monkeypatch.setenv("WPSCAN_API_KEY", "k123")
        calls = empty_calls()
        fake_obs, fake_wpscan, fake_osv = make_fakes(
            calls, wpscan_result=VulnerabilityScan(source="WPScan", vulnerabilities=[make_vuln()])
        )
        stack = make_stack(cms="WordPress", technologies=[tech("WordPress", "6.4", ["CMS"])])

        result = asyncio.run(
            scan_security(
                make_fetch(headers=FULL_HEADERS),
                stack,
                fetch_observatory=fake_obs,
                run_wpscan=fake_wpscan,
                run_osv=fake_osv,
            )
        )

        assert calls["wpscan"] == [("6.4", "k123")]
        assert calls["osv"] == []  # WordPress branch, not OSV
        assert calls["observatory"] == ["example.com"]
        assert result.version_known is True
        assert result.has_known_vulns is True
        assert result.observatory_grade == "B"

    def test_wordpress_without_api_key_degrades_cleanly(self, monkeypatch):
        monkeypatch.delenv("WPSCAN_API_KEY", raising=False)
        calls = empty_calls()
        fake_obs, fake_wpscan, fake_osv = make_fakes(calls)
        stack = make_stack(cms="WordPress", technologies=[tech("WordPress", "6.4", ["CMS"])])

        result = asyncio.run(
            scan_security(
                make_fetch(headers=FULL_HEADERS),
                stack,
                fetch_observatory=fake_obs,
                run_wpscan=fake_wpscan,
                run_osv=fake_osv,
            )
        )

        assert calls["wpscan"] == []  # never called without a key
        assert calls["osv"] == []
        assert calls["observatory"] == ["example.com"]  # headers still graded
        assert result.version_known is True
        assert result.has_known_vulns is False
        assert any("WPScan no configurado" in n for n in result.notes)

    def test_non_wordpress_queries_osv_per_versioned_product(self):
        calls = empty_calls()
        fake_obs, fake_wpscan, fake_osv = make_fakes(calls)
        stack = make_stack(
            cms="Drupal",
            technologies=[
                tech("Drupal", "9.4", ["CMS"]),
                tech("Nginx", "1.18", ["Web servers"]),
                tech("Google Analytics", "4", ["Analytics"]),  # not stack-identifying
                tech("PHP", None, ["Programming languages"]),  # no version -> nothing to ask
            ],
        )

        result = asyncio.run(
            scan_security(
                make_fetch(headers=FULL_HEADERS),
                stack,
                fetch_observatory=fake_obs,
                run_wpscan=fake_wpscan,
                run_osv=fake_osv,
            )
        )

        assert calls["wpscan"] == []
        assert calls["osv"] == [("Drupal", "9.4"), ("Nginx", "1.18")]
        assert result.version_known is True
        assert result.has_known_vulns is False
        assert any("Sin vulnerabilidades conocidas" in n for n in result.notes)

    def test_version_not_visible_calls_no_cve_scanner_wordpress(self):
        calls = empty_calls()
        fake_obs, fake_wpscan, fake_osv = make_fakes(calls)
        stack = make_stack(cms="WordPress", technologies=[tech("WordPress", None, ["CMS"])])

        result = asyncio.run(
            scan_security(
                make_fetch(headers=FULL_HEADERS),
                stack,
                fetch_observatory=fake_obs,
                run_wpscan=fake_wpscan,
                run_osv=fake_osv,
            )
        )

        assert calls["wpscan"] == [] and calls["osv"] == []  # no scanner at all
        assert calls["observatory"] == ["example.com"]  # headers still graded
        assert result.version_known is False
        assert result.has_known_vulns is False
        assert any("sin datos suficientes" in n for n in result.notes)

    def test_version_not_visible_calls_no_cve_scanner_non_wordpress(self):
        calls = empty_calls()
        fake_obs, fake_wpscan, fake_osv = make_fakes(calls)
        stack = make_stack(
            cms=None,
            technologies=[
                tech("React", None, ["JavaScript frameworks"]),
            ],
        )

        result = asyncio.run(
            scan_security(
                make_fetch(headers=FULL_HEADERS),
                stack,
                fetch_observatory=fake_obs,
                run_wpscan=fake_wpscan,
                run_osv=fake_osv,
            )
        )

        assert calls["wpscan"] == [] and calls["osv"] == []
        assert result.version_known is False

    def test_observatory_timeout_does_not_cancel_cve_scan(self, monkeypatch):
        # Partial failure: Observatory answers with a failure, WPScan answers fine.
        monkeypatch.setenv("WPSCAN_API_KEY", "k123")
        calls = empty_calls()
        _, fake_wpscan, fake_osv = make_fakes(
            calls, wpscan_result=VulnerabilityScan(source="WPScan", vulnerabilities=[make_vuln()])
        )

        async def failing_observatory(host: str) -> ObservatoryReport:
            calls["observatory"].append(host)
            return ObservatoryReport(failed=True, error="timeout")

        stack = make_stack(cms="WordPress", technologies=[tech("WordPress", "6.4", ["CMS"])])

        result = asyncio.run(
            scan_security(
                make_fetch(headers=FULL_HEADERS),
                stack,
                fetch_observatory=failing_observatory,
                run_wpscan=fake_wpscan,
                run_osv=fake_osv,
            )
        )

        assert result.has_known_vulns is True  # the CVE side still ran
        assert result.observatory_grade is None
        assert any("Observatory no disponible" in n for n in result.notes)

    def test_unreachable_site_calls_nothing(self):
        calls = empty_calls()
        fake_obs, fake_wpscan, fake_osv = make_fakes(calls)

        result = asyncio.run(
            scan_security(
                make_fetch(reachability=Reachability.UNREACHABLE),
                make_stack(),
                fetch_observatory=fake_obs,
                run_wpscan=fake_wpscan,
                run_osv=fake_osv,
            )
        )

        assert calls == empty_calls()
        assert result.version_known is False
        assert any("no alcanzable" in n for n in result.notes)
