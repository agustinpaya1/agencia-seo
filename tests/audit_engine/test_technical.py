"""Tests for the pure technical scorer (audit_engine/technical.py).

score_technical is 100% pure and synchronous, so every case is built from a
FetchResult + TechStackResult fixture — no network, no detect_tech_stack. The
goal is representative coverage per dimension (SKILL rubric), not an exhaustive
sweep of every threshold.
"""

from datetime import datetime, timezone

from backend.app.audit_engine.models import (
    Confidence,
    DetectedTechnology,
    FetchResult,
    Reachability,
    TechStackResult,
)
from backend.app.audit_engine.technical import WEIGHTS, score_technical


# --------------------------------------------------------------------------- #
# Fixture builders
# --------------------------------------------------------------------------- #
def make_fetch(
    html: str = "",
    *,
    domain: str = "example.com",
    reachability: Reachability = Reachability.OK,
    status_code: int | None = 200,
    final_url: str | None = "https://example.com/",
    headers: dict | None = None,
    robots_txt: str | None = None,
    sitemap_urls: list | None = None,
) -> FetchResult:
    return FetchResult(
        domain=domain,
        reachability=reachability,
        status_code=status_code,
        final_url=final_url,
        html=html,
        headers=headers or {},
        robots_txt=robots_txt,
        sitemap_urls=sitemap_urls or [],
        fetched_at=datetime.now(timezone.utc),
    )


def make_stack(
    *, identified: bool = False, technologies: list | None = None, cms: str | None = None,
    behind_cdn: bool = False,
) -> TechStackResult:
    return TechStackResult(
        identified=identified,
        technologies=technologies or [],
        cms=cms,
        behind_cdn=behind_cdn,
    )


def dim(result, name):
    for d in result.dimensions:
        if d.name == name:
            return d
    raise AssertionError(f"dimension not found: {name} (have {[d.name for d in result.dimensions]})")


SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}

ROBOTS_ALLOW_ALL = "User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml\n"

# A complete, server-rendered page: title + description + canonical + og, JSON-LD,
# six internal links, responsive viewport, dimensioned images, no blocking script.
GOOD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Example — GEO agency</title>
  <meta name="description" content="We help brands get cited by AI search.">
  <meta property="og:title" content="Example">
  <link rel="canonical" href="https://example.com/">
  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"Organization","name":"Example","url":"https://example.com","logo":"https://example.com/logo.png"}
  </script>
</head>
<body>
  <nav>
    <a href="/">Home</a>
    <a href="/services">Services</a>
    <a href="/about">About</a>
    <a href="/blog">Blog</a>
    <a href="/contact">Contact</a>
    <a href="/pricing">Pricing</a>
  </nav>
  <main>
    <h1>GEO agency</h1>
    <p>This is a fully server-rendered marketing page delivered as complete HTML.
    Every crawler and AI bot that requests it without running JavaScript receives
    the same rich content that a browser would, which is exactly what generative
    engines need in order to cite the brand accurately in their answers.</p>
    <img src="/hero.webp" width="1200" height="600" alt="hero" loading="lazy">
  </main>
</body>
</html>"""

CSR_SHELL_HTML = """<!DOCTYPE html>
<html><head><title>App</title></head>
<body><div id="root">Loading...</div><script src="/main.js"></script></body></html>"""


# --------------------------------------------------------------------------- #
# Shape / weighting invariants
# --------------------------------------------------------------------------- #
class TestShape:
    def test_eight_dimensions_named_after_weights(self):
        result = score_technical(make_fetch(GOOD_HTML), make_stack())
        assert len(result.dimensions) == 8
        assert {d.name for d in result.dimensions} == set(WEIGHTS)

    def test_weights_sum_to_one_and_points_are_score_times_weight(self):
        result = score_technical(make_fetch(GOOD_HTML), make_stack())
        assert round(sum(d.weight for d in result.dimensions), 6) == 1.0
        for d in result.dimensions:
            assert d.points == round(d.score * d.weight, 2)
            assert 0.0 <= d.score <= 100.0
        assert 0.0 <= result.score <= 100.0
        assert result.score == round(sum(d.points for d in result.dimensions), 2)


# --------------------------------------------------------------------------- #
# SSR (25%) — the heaviest dimension
# --------------------------------------------------------------------------- #
class TestSSR:
    def test_complete_ssr_page_full(self):
        result = score_technical(
            make_fetch(GOOD_HTML, headers=SECURITY_HEADERS, robots_txt=ROBOTS_ALLOW_ALL),
            make_stack(),
        )
        assert dim(result, "ssr").score == 100.0
        assert result.score >= 95.0  # a technically-sound page lands near the top

    def test_client_side_shell_scores_low(self):
        result = score_technical(make_fetch(CSR_SHELL_HTML), make_stack())
        ssr = dim(result, "ssr")
        # Only the <title> earns anything; body/structured-data/links are all absent.
        assert ssr.score < 20.0
        assert any("crawler sin JS" in f or "shell" in f.lower() for f in ssr.findings)

    def test_structured_data_flag_matches_presence(self):
        with_jsonld = dim(score_technical(make_fetch(GOOD_HTML), make_stack()), "ssr")
        without = dim(score_technical(make_fetch(CSR_SHELL_HTML), make_stack()), "ssr")
        assert any("(JSON-LD) presentes" in f for f in with_jsonld.findings)
        assert any("Sin JSON-LD" in f for f in without.findings)

    def test_unreachable_fetch_is_zero_not_crash(self):
        result = score_technical(
            make_fetch("", reachability=Reachability.UNREACHABLE, status_code=None, final_url=None),
            make_stack(),
        )
        assert dim(result, "ssr").score == 0.0
        assert dim(result, "status").score == 0.0
        assert any("no alcanzable" in f for f in dim(result, "ssr").findings)


# --------------------------------------------------------------------------- #
# Meta / indexability (15%)
# --------------------------------------------------------------------------- #
class TestMetaIndexability:
    def test_noindex_drops_indexable_half(self):
        html = GOOD_HTML.replace(
            '<meta name="description"',
            '<meta name="robots" content="noindex, nofollow">\n  <meta name="description"',
        )
        result = score_technical(make_fetch(html), make_stack())
        mi = dim(result, "meta_indexability")
        assert mi.score == 40.0  # canonical kept (40), indexable lost (60)
        assert any("noindex" in f for f in mi.findings)

    def test_missing_canonical_costs_forty(self):
        html = GOOD_HTML.replace('<link rel="canonical" href="https://example.com/">', "")
        result = score_technical(make_fetch(html), make_stack())
        assert dim(result, "meta_indexability").score == 60.0


# --------------------------------------------------------------------------- #
# Crawlability (15%)
# --------------------------------------------------------------------------- #
class TestCrawlability:
    def test_blocking_googlebot_is_fatal(self):
        robots = "User-agent: Googlebot\nDisallow: /\n"
        result = score_technical(make_fetch(GOOD_HTML, robots_txt=robots), make_stack())
        crawl = dim(result, "crawlability")
        assert any("FATAL" in f and "Googlebot" in f for f in crawl.findings)
        assert crawl.score <= 55.0  # loses the 25-pt Googlebot slice

    def test_blocking_gptbot_flagged(self):
        robots = "User-agent: GPTBot\nDisallow: /\nSitemap: https://example.com/sitemap.xml\n"
        result = score_technical(make_fetch(GOOD_HTML, robots_txt=robots), make_stack())
        crawl = dim(result, "crawlability")
        assert any("gptbot" in f.lower() for f in crawl.findings)
        assert crawl.score < 100.0

    def test_no_robots_is_default_allowed_not_blocked(self):
        result = score_technical(
            make_fetch(GOOD_HTML, robots_txt=None, sitemap_urls=["https://example.com/sitemap.xml"]),
            make_stack(),
        )
        crawl = dim(result, "crawlability")
        assert any("todo crawlable por defecto" in f for f in crawl.findings)
        # default-allow (25+35) + sitemap (20), robots-present slice (20) not earned.
        assert crawl.score == 80.0


# --------------------------------------------------------------------------- #
# Security headers estimate (10%)
# --------------------------------------------------------------------------- #
class TestSecurityHeaders:
    def test_all_headers_and_https_full(self):
        result = score_technical(make_fetch(GOOD_HTML, headers=SECURITY_HEADERS), make_stack())
        assert dim(result, "security_headers_estimate").score == 100.0

    def test_http_without_headers_low(self):
        result = score_technical(
            make_fetch(GOOD_HTML, headers={}, final_url="http://example.com/"), make_stack()
        )
        sec = dim(result, "security_headers_estimate")
        assert sec.score == 0.0
        assert any("autoritativo" in f for f in sec.findings)  # points to security.py


# --------------------------------------------------------------------------- #
# CWV static estimate (10%) + stack usage
# --------------------------------------------------------------------------- #
class TestCwvStatic:
    def test_cdn_from_stack_bumps_score(self):
        base = make_fetch(GOOD_HTML)
        no_cdn = dim(score_technical(base, make_stack(behind_cdn=False)), "cwv_static_estimate")
        with_cdn = dim(score_technical(base, make_stack(behind_cdn=True)), "cwv_static_estimate")
        assert with_cdn.score == no_cdn.score + 5.0

    def test_labelled_as_estimate(self):
        result = score_technical(make_fetch(GOOD_HTML), make_stack())
        assert any("performance.py" in f for f in dim(result, "cwv_static_estimate").findings)


# --------------------------------------------------------------------------- #
# Mobile (15%)
# --------------------------------------------------------------------------- #
class TestMobile:
    def test_responsive_viewport_full(self):
        assert dim(score_technical(make_fetch(GOOD_HTML), make_stack()), "mobile").score == 100.0

    def test_no_viewport_zero(self):
        html = GOOD_HTML.replace('<meta name="viewport" content="width=device-width, initial-scale=1">', "")
        result = score_technical(make_fetch(html), make_stack())
        assert dim(result, "mobile").score == 0.0


# --------------------------------------------------------------------------- #
# URL structure (5%) and status (5%)
# --------------------------------------------------------------------------- #
class TestUrlAndStatus:
    def test_dirty_url_loses_points(self):
        result = score_technical(
            make_fetch(GOOD_HTML, final_url="https://example.com/Blog_Section/Page?sessionid=abc"),
            make_stack(),
        )
        assert dim(result, "url_structure").score <= 50.0

    def test_clean_homepage_full(self):
        result = score_technical(make_fetch(GOOD_HTML, final_url="https://example.com/"), make_stack())
        assert dim(result, "url_structure").score == 100.0

    def test_server_error_status(self):
        result = score_technical(make_fetch(GOOD_HTML, status_code=503), make_stack())
        assert dim(result, "status").score == 0.0

    def test_redirect_status_partial(self):
        result = score_technical(make_fetch(GOOD_HTML, status_code=301), make_stack())
        assert dim(result, "status").score == 70.0


# --------------------------------------------------------------------------- #
# Stack corroboration in SSR findings
# --------------------------------------------------------------------------- #
def test_spa_stack_noted_when_content_present():
    stack = make_stack(
        identified=True,
        technologies=[DetectedTechnology(name="React", categories=["JavaScript frameworks"], confidence=Confidence.HIGH)],
    )
    result = score_technical(make_fetch(GOOD_HTML), stack)
    assert any("SPA" in f for f in dim(result, "ssr").findings)
