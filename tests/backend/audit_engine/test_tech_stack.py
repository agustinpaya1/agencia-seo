"""Tests for technology stack detection (audit_engine/tech_stack.py).

Two layers, tested separately (task 5, point 5):

* :func:`evaluate_tech_stack` — pure, synchronous, no network/browser —
  exercised directly with normalized ``StackSignal`` fixtures (clear signatures,
  weak signatures, no signatures, contradiction, CDN).
* :func:`detect_tech_stack` — the async shell — exercised with fake
  ``run_static``/``run_rendered`` callables, so no real wappalyzer-next scan or
  browser render happens in the suite. Driven with ``asyncio.run`` directly to
  avoid a pytest-asyncio dependency (same style as test_performance.py).
"""

import asyncio
from datetime import datetime, timezone

from backend.app.audit_engine.models import Confidence, FetchResult, Reachability
from backend.app.audit_engine.tech_stack import (
    StackSignal,
    detect_tech_stack,
    evaluate_tech_stack,
)


def make_fetch(
    *,
    reachability: Reachability = Reachability.OK,
    final_url: str | None = "https://example.com/",
    headers: dict[str, str] | None = None,
) -> FetchResult:
    return FetchResult(
        domain="example.com",
        reachability=reachability,
        status_code=200,
        final_url=final_url,
        html="<html></html>",
        headers=headers or {},
        fetched_at=datetime.now(timezone.utc),
    )


# --------------------------------------------------------------------------- #
# Pure layer
# --------------------------------------------------------------------------- #
class TestEvaluateTechStackPure:
    def test_clear_signature_is_identified_high_confidence(self):
        signals = [
            StackSignal(
                name="WordPress", version="6.4", categories=["CMS", "Blogs"], confidence=100
            )
        ]

        result = evaluate_tech_stack(signals, {})

        assert result.identified is True
        assert result.confidence == Confidence.HIGH
        assert result.cms == "WordPress"
        assert len(result.technologies) == 1
        tech = result.technologies[0]
        assert tech.name == "WordPress"
        assert tech.version == "6.4"
        assert tech.confidence == Confidence.HIGH
        assert any("alta confianza" in n for n in result.notes)

    def test_weak_signature_is_identified_but_medium(self):
        signals = [StackSignal(name="React", categories=["JavaScript frameworks"], confidence=50)]

        result = evaluate_tech_stack(signals, {})

        assert result.identified is True
        assert result.confidence == Confidence.MEDIUM
        assert result.technologies[0].confidence == Confidence.MEDIUM
        assert result.cms is None

    def test_no_signature_is_unidentified_low(self):
        result = evaluate_tech_stack([], {})

        assert result.identified is False
        assert result.confidence == Confidence.LOW
        assert result.technologies == []
        assert any("no identificado" in n for n in result.notes)

    def test_non_identifying_only_is_unidentified_but_lists_tech(self):
        # Analytics is a real detection but does not identify the *stack*.
        signals = [StackSignal(name="Google Analytics", categories=["Analytics"], confidence=100)]

        result = evaluate_tech_stack(signals, {})

        assert result.identified is False
        assert result.confidence == Confidence.LOW
        assert [t.name for t in result.technologies] == ["Google Analytics"]

    def test_two_cms_is_a_contradiction_medium(self):
        signals = [
            StackSignal(name="WordPress", categories=["CMS"], confidence=100),
            StackSignal(name="Drupal", categories=["CMS"], confidence=100),
        ]

        result = evaluate_tech_stack(signals, {})

        assert result.identified is True
        assert result.confidence == Confidence.MEDIUM  # never HIGH while contradictory
        assert any(
            "contradictorias" in n and "WordPress" in n and "Drupal" in n for n in result.notes
        )

    def test_cms_plus_strong_frontend_framework_is_a_contradiction(self):
        # Diagram 3.2's own casuística: CMS base + headless frontend on top.
        signals = [
            StackSignal(name="WordPress", categories=["CMS"], confidence=100),
            StackSignal(name="React", categories=["JavaScript frameworks"], confidence=100),
        ]

        result = evaluate_tech_stack(signals, {})

        assert result.identified is True
        assert result.confidence == Confidence.MEDIUM  # forces the render in the shell
        assert any(
            "contradictorias" in n and "WordPress" in n and "React" in n for n in result.notes
        )

    def test_cms_plus_weak_frontend_framework_is_not_a_contradiction(self):
        # An incidental widget: the framework does not fingerprint strongly.
        signals = [
            StackSignal(name="WordPress", categories=["CMS"], confidence=100),
            StackSignal(name="React", categories=["JavaScript frameworks"], confidence=50),
        ]

        result = evaluate_tech_stack(signals, {})

        assert result.confidence == Confidence.HIGH
        assert not any("contradictorias" in n for n in result.notes)

    def test_cms_plus_frontend_confirmed_after_render_is_headless_high(self):
        static = [
            StackSignal(name="WordPress", categories=["CMS"], confidence=100),
            StackSignal(name="React", categories=["JavaScript frameworks"], confidence=100),
        ]
        rendered = [
            StackSignal(
                name="React", version="18.2", categories=["JavaScript frameworks"], confidence=100
            ),
            StackSignal(
                name="Next.js", version="14", categories=["Web frameworks"], confidence=100
            ),
        ]

        result = evaluate_tech_stack(static, {}, rendered_signals=rendered)

        assert result.confidence == Confidence.HIGH
        assert result.cms == "WordPress"
        assert any("headless" in n for n in result.notes)

    def test_cms_plus_frontend_not_confirmed_after_render_stays_medium(self):
        static = [
            StackSignal(name="WordPress", categories=["CMS"], confidence=100),
            StackSignal(name="React", categories=["JavaScript frameworks"], confidence=100),
        ]

        result = evaluate_tech_stack(static, {}, rendered_signals=[])

        assert result.confidence == Confidence.MEDIUM
        assert any("no se confirmó" in n for n in result.notes)

    def test_wordpress_plus_woocommerce_is_not_a_contradiction(self):
        signals = [
            StackSignal(name="WordPress", categories=["CMS"], confidence=100),
            StackSignal(name="WooCommerce", categories=["Ecommerce"], confidence=100),
        ]

        result = evaluate_tech_stack(signals, {})

        assert result.confidence == Confidence.HIGH
        assert not any("contradictorias" in n for n in result.notes)

    def test_cdn_from_wappalyzer_category(self):
        signals = [
            StackSignal(name="WordPress", categories=["CMS"], confidence=100),
            StackSignal(name="Cloudflare", categories=["CDN"], confidence=100),
        ]

        result = evaluate_tech_stack(signals, {})

        assert result.behind_cdn is True
        assert result.origin_visible is False
        assert any("origen no es visible" in n for n in result.notes)

    def test_cdn_from_response_headers(self):
        signals = [StackSignal(name="WordPress", categories=["CMS"], confidence=100)]

        result = evaluate_tech_stack(signals, {"CF-RAY": "7d1c-MAD", "Server": "cloudflare"})

        assert result.behind_cdn is True
        assert result.origin_visible is False
        assert any("Cloudflare" in n for n in result.notes)

    def test_rendered_signals_merge_and_fill_version(self):
        static = [StackSignal(name="React", categories=["JavaScript frameworks"], confidence=50)]
        rendered = [
            StackSignal(
                name="React", version="18.2", categories=["JavaScript frameworks"], confidence=100
            )
        ]

        result = evaluate_tech_stack(static, {}, rendered_signals=rendered)

        assert len(result.technologies) == 1
        tech = result.technologies[0]
        assert tech.version == "18.2"  # filled from the rendered detection
        assert tech.confidence == Confidence.HIGH  # max(50, 100)
        assert result.confidence == Confidence.HIGH
        assert any("renderiz" in n for n in result.notes)  # render note present

    def test_rendered_but_still_nothing_notes_the_render(self):
        result = evaluate_tech_stack([], {}, rendered_signals=[])

        assert result.identified is False
        assert result.confidence == Confidence.LOW
        assert any("ni siquiera tras renderizar" in n for n in result.notes)


# --------------------------------------------------------------------------- #
# Async shell — mocked wappalyzer-next scans
# --------------------------------------------------------------------------- #
class TestDetectTechStackShell:
    def test_clear_static_signature_skips_render(self):
        calls = {"static": 0, "rendered": 0}

        async def fake_static(_url):
            calls["static"] += 1
            return [
                StackSignal(name="WordPress", version="6.4", categories=["CMS"], confidence=100)
            ]

        async def fake_rendered(_url):
            calls["rendered"] += 1
            return []

        result = asyncio.run(
            detect_tech_stack(
                make_fetch(),
                run_static=fake_static,
                run_rendered=fake_rendered,
            )
        )

        assert result.confidence == Confidence.HIGH
        assert result.cms == "WordPress"
        assert calls == {"static": 1, "rendered": 0}  # no render needed

    def test_weak_static_triggers_render_that_resolves_it(self):
        calls = {"static": 0, "rendered": 0}

        async def fake_static(_url):
            calls["static"] += 1
            return [StackSignal(name="React", categories=["JavaScript frameworks"], confidence=50)]

        async def fake_rendered(_url):
            calls["rendered"] += 1
            return [
                StackSignal(
                    name="React",
                    version="18.2",
                    categories=["JavaScript frameworks"],
                    confidence=100,
                ),
                StackSignal(
                    name="Next.js", version="14", categories=["Web frameworks"], confidence=100
                ),
            ]

        result = asyncio.run(
            detect_tech_stack(
                make_fetch(),
                run_static=fake_static,
                run_rendered=fake_rendered,
            )
        )

        assert calls == {"static": 1, "rendered": 1}  # weak static -> render
        assert result.identified is True
        assert result.confidence == Confidence.HIGH
        assert {t.name for t in result.technologies} == {"React", "Next.js"}

    def test_wordpress_plus_react_strong_forces_render(self):
        # The exact scenario from the hygiene fix: WordPress + React/Next.js with
        # strong signatures of both must NOT exit HIGH on the static scan alone.
        calls = {"static": 0, "rendered": 0}

        async def fake_static(_url):
            calls["static"] += 1
            return [
                StackSignal(name="WordPress", version="6.4", categories=["CMS"], confidence=100),
                StackSignal(name="React", categories=["JavaScript frameworks"], confidence=100),
            ]

        async def fake_rendered(_url):
            calls["rendered"] += 1
            return [
                StackSignal(
                    name="React",
                    version="18.2",
                    categories=["JavaScript frameworks"],
                    confidence=100,
                ),
                StackSignal(
                    name="Next.js", version="14", categories=["Web frameworks"], confidence=100
                ),
            ]

        result = asyncio.run(
            detect_tech_stack(
                make_fetch(),
                run_static=fake_static,
                run_rendered=fake_rendered,
            )
        )

        assert calls == {"static": 1, "rendered": 1}  # render was forced
        assert result.cms == "WordPress"
        assert result.confidence == Confidence.HIGH  # resolved after the render
        assert any("headless" in n for n in result.notes)

    def test_render_still_finds_nothing_is_unidentified(self):
        calls = {"static": 0, "rendered": 0}

        async def fake_static(_url):
            calls["static"] += 1
            return []

        async def fake_rendered(_url):
            calls["rendered"] += 1
            return []

        result = asyncio.run(
            detect_tech_stack(
                make_fetch(),
                run_static=fake_static,
                run_rendered=fake_rendered,
            )
        )

        assert calls == {"static": 1, "rendered": 1}
        assert result.identified is False
        assert result.confidence == Confidence.LOW
        assert any("ni siquiera tras renderizar" in n for n in result.notes)

    def test_unreachable_site_skips_all_scans(self):
        calls = {"static": 0, "rendered": 0}

        async def fake_static(_url):
            calls["static"] += 1
            return []

        async def fake_rendered(_url):
            calls["rendered"] += 1
            return []

        result = asyncio.run(
            detect_tech_stack(
                make_fetch(reachability=Reachability.UNREACHABLE),
                run_static=fake_static,
                run_rendered=fake_rendered,
            )
        )

        assert calls == {"static": 0, "rendered": 0}  # nothing scanned
        assert result.identified is False
        assert result.confidence == Confidence.LOW
        assert any("no alcanzable" in n for n in result.notes)

    def test_cdn_headers_flow_through_from_fetch(self):
        async def fake_static(_url):
            return [StackSignal(name="WordPress", categories=["CMS"], confidence=100)]

        async def fake_rendered(_url):  # pragma: no cover - should not be called
            return []

        result = asyncio.run(
            detect_tech_stack(
                make_fetch(headers={"cf-ray": "abc123"}),
                run_static=fake_static,
                run_rendered=fake_rendered,
            )
        )

        assert result.behind_cdn is True
        assert result.origin_visible is False
