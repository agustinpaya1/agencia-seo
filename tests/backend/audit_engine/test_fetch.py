"""Tests for the initial site fetch (audit_engine/fetch.py, diagram 3.1, step B).

Two layers, tested separately:

* :func:`evaluate_fetch` — pure, synchronous, no network — exercised directly
  with raw ``PageFetchOutcome`` + robots.txt/sitemap/sub-sitemap text fixtures
  (full page, no robots.txt, a plain urlset, a sitemapindex expanded via
  already-fetched sub-sitemap text, a failed/nested sub-sitemap, no sitemap, a
  404, a 5xx).
* :func:`fetch_site` — the async shell — exercised with fake
  ``fetch_page_fn``/``fetch_robots_fn``/``fetch_sitemap_fn``/
  ``fetch_sub_sitemap_fn`` callables, so no real HTTP request happens in the
  suite. Driven with ``asyncio.run`` directly, same style as
  test_performance.py and test_tech_stack.py.
"""

import asyncio
from datetime import datetime, timezone

from backend.app.audit_engine.fetch import (
    MAX_SITEMAP_URLS,
    MAX_SUB_SITEMAPS,
    PageFetchOutcome,
    evaluate_fetch,
    fetch_site,
)
from backend.app.audit_engine.models import Reachability

SITEMAP_URLSET = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/</loc></url>
  <url><loc>https://example.com/about</loc></url>
</urlset>"""

SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/sitemap-posts.xml</loc></sitemap>
  <sitemap><loc>https://example.com/sitemap-pages.xml</loc></sitemap>
</sitemapindex>"""

SITEMAP_POSTS = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/posts/1</loc></url>
  <url><loc>https://example.com/posts/2</loc></url>
</urlset>"""

SITEMAP_PAGES = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/about</loc></url>
  <url><loc>https://example.com/contact</loc></url>
</urlset>"""

NESTED_SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/sitemap-nested-deeper.xml</loc></sitemap>
</sitemapindex>"""


def make_page(
    *,
    ok: bool = True,
    status_code: int | None = 200,
    final_url: str | None = "https://example.com/",
    html: str | None = "<html><body>hi</body></html>",
    headers: dict[str, str] | None = None,
    error: str | None = None,
) -> PageFetchOutcome:
    return PageFetchOutcome(
        ok=ok,
        status_code=status_code,
        final_url=final_url,
        html=html,
        headers=headers or {"Content-Type": "text/html"},
        error=error,
    )


NOW = datetime(2026, 7, 4, tzinfo=timezone.utc)


# --------------------------------------------------------------------------- #
# Pure layer
# --------------------------------------------------------------------------- #
class TestEvaluateFetchPure:
    def test_full_page_with_robots_and_sitemap_is_ok(self):
        page = make_page()

        result = evaluate_fetch(
            "example.com", page, "User-agent: *\nAllow: /", SITEMAP_URLSET, None, now=NOW
        )

        assert result.reachability == Reachability.OK
        assert result.status_code == 200
        assert result.final_url == "https://example.com/"
        assert result.html == "<html><body>hi</body></html>"
        assert result.headers == {"Content-Type": "text/html"}
        assert result.robots_txt == "User-agent: *\nAllow: /"
        assert result.sitemap_urls == ["https://example.com/", "https://example.com/about"]
        assert result.fetched_at == NOW

    def test_missing_robots_txt_is_none_not_error(self):
        page = make_page()

        result = evaluate_fetch("example.com", page, None, SITEMAP_URLSET, None, now=NOW)

        assert result.reachability == Reachability.OK
        assert result.robots_txt is None

    def test_sitemap_index_without_sub_sitemaps_fetched_yields_no_pages(self):
        # The shell decided not to (or could not) fetch any sub-sitemap; the
        # index's own <loc> values are sitemap files, never pages.
        page = make_page()

        result = evaluate_fetch("example.com", page, None, SITEMAP_INDEX, None, now=NOW)

        assert result.sitemap_urls == []
        assert any("sitemapindex" in note for note in result.notes)

    def test_sitemap_index_expands_via_already_fetched_sub_sitemaps(self):
        page = make_page()

        result = evaluate_fetch(
            "example.com",
            page,
            None,
            SITEMAP_INDEX,
            None,
            sub_sitemap_xmls=[SITEMAP_POSTS, SITEMAP_PAGES],
            now=NOW,
        )

        assert result.sitemap_urls == [
            "https://example.com/posts/1",
            "https://example.com/posts/2",
            "https://example.com/about",
            "https://example.com/contact",
        ]
        assert any("sitemapindex" in note for note in result.notes)

    def test_sitemap_index_skips_failed_sub_sitemap_and_keeps_the_rest(self):
        page = make_page()

        result = evaluate_fetch(
            "example.com",
            page,
            None,
            SITEMAP_INDEX,
            None,
            sub_sitemap_xmls=[SITEMAP_POSTS, None],
            now=NOW,
        )

        assert result.sitemap_urls == [
            "https://example.com/posts/1",
            "https://example.com/posts/2",
        ]
        assert any("failed" in note for note in result.notes)

    def test_sitemap_index_does_not_follow_a_second_level(self):
        page = make_page()

        result = evaluate_fetch(
            "example.com",
            page,
            None,
            SITEMAP_INDEX,
            None,
            sub_sitemap_xmls=[NESTED_SITEMAP_INDEX, SITEMAP_PAGES],
            now=NOW,
        )

        assert result.sitemap_urls == ["https://example.com/about", "https://example.com/contact"]
        assert any("second level" in note for note in result.notes)

    def test_sitemap_index_notes_when_sub_sitemaps_were_truncated(self):
        # Only 1 of the 2 sub-sitemaps declared by SITEMAP_INDEX was followed
        # (simulating the shell's MAX_SUB_SITEMAPS cap) -- must be noted, not
        # silently dropped.
        page = make_page()

        result = evaluate_fetch(
            "example.com",
            page,
            None,
            SITEMAP_INDEX,
            None,
            sub_sitemap_xmls=[SITEMAP_POSTS],
            now=NOW,
        )

        assert result.sitemap_urls == [
            "https://example.com/posts/1",
            "https://example.com/posts/2",
        ]
        assert any("MAX_SUB_SITEMAPS" in note for note in result.notes)

    def test_missing_sitemap_is_empty_list(self):
        page = make_page()

        result = evaluate_fetch("example.com", page, None, None, None, now=NOW)

        assert result.sitemap_urls == []
        assert result.notes == []

    def test_sitemap_urls_are_deduplicated(self):
        page = make_page()
        entries = "".join(
            f"<url><loc>https://example.com/p{i % 5}</loc></url>" for i in range(1000)
        )
        xml = f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{entries}</urlset>'

        result = evaluate_fetch("example.com", page, None, xml, None, now=NOW)

        assert len(result.sitemap_urls) == 5  # deduplicated: only p0..p4 are distinct
        assert result.notes == []

    def test_sitemap_urls_capped_at_max_and_noted(self):
        page = make_page()
        entries = "".join(
            f"<url><loc>https://example.com/p{i}</loc></url>" for i in range(MAX_SITEMAP_URLS + 50)
        )
        xml = f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{entries}</urlset>'

        result = evaluate_fetch("example.com", page, None, xml, None, now=NOW)

        assert len(result.sitemap_urls) == MAX_SITEMAP_URLS
        assert any("MAX_SITEMAP_URLS" in note for note in result.notes)

    def test_404_on_main_page_is_ok_with_status_code(self):
        page = make_page(status_code=404, html="<html>not found</html>")

        result = evaluate_fetch("example.com", page, None, None, None, now=NOW)

        assert result.reachability == Reachability.OK
        assert result.status_code == 404
        assert result.html == "<html>not found</html>"

    def test_5xx_on_main_page_is_unreachable(self):
        page = make_page(status_code=503, final_url="https://example.com/", html="<html></html>")

        result = evaluate_fetch("example.com", page, "User-agent: *", SITEMAP_URLSET, None, now=NOW)

        assert result.reachability == Reachability.UNREACHABLE
        assert result.status_code == 503
        assert result.html is None
        assert result.headers == {}
        assert result.robots_txt is None
        assert result.sitemap_urls == []

    def test_request_failure_is_unreachable(self):
        page = make_page(ok=False, status_code=None, final_url=None, html=None, error="timeout")

        result = evaluate_fetch("example.com", page, None, None, None, now=NOW)

        assert result.reachability == Reachability.UNREACHABLE
        assert result.status_code is None
        assert result.html is None


# --------------------------------------------------------------------------- #
# Async shell
# --------------------------------------------------------------------------- #
class TestFetchSiteShell:
    def test_timeout_on_main_page_is_unreachable_and_skips_robots_and_sitemap(self):
        calls = {"robots": 0, "sitemap": 0}

        async def fake_page(url, timeout):
            return PageFetchOutcome(ok=False, error="timeout")

        async def fake_robots(base_url, timeout):
            calls["robots"] += 1
            return "should not be called"

        async def fake_sitemap(base_url, timeout):
            calls["sitemap"] += 1
            return "should not be called"

        result = asyncio.run(
            fetch_site(
                "example.com",
                fetch_page_fn=fake_page,
                fetch_robots_fn=fake_robots,
                fetch_sitemap_fn=fake_sitemap,
                now=NOW,
            )
        )

        assert result.reachability == Reachability.UNREACHABLE
        assert calls == {"robots": 0, "sitemap": 0}

    def test_robots_and_sitemap_down_with_page_ok_degrades_both_to_none(self):
        async def fake_page(url, timeout):
            return PageFetchOutcome(
                ok=True,
                status_code=200,
                final_url="https://example.com/",
                html="<html>hi</html>",
                headers={"Server": "nginx"},
            )

        async def fake_robots(base_url, timeout):
            return None

        async def fake_sitemap(base_url, timeout):
            return None

        result = asyncio.run(
            fetch_site(
                "example.com",
                fetch_page_fn=fake_page,
                fetch_robots_fn=fake_robots,
                fetch_sitemap_fn=fake_sitemap,
                now=NOW,
            )
        )

        assert result.reachability == Reachability.OK
        assert result.html == "<html>hi</html>"
        assert result.robots_txt is None
        assert result.sitemap_urls == []

    def test_happy_path_end_to_end(self):
        async def fake_page(url, timeout):
            assert url == "https://example.com"
            return PageFetchOutcome(
                ok=True,
                status_code=200,
                final_url="https://example.com/",
                html="<html>hi</html>",
                headers={"Server": "nginx"},
            )

        async def fake_robots(base_url, timeout):
            assert base_url == "https://example.com/"
            return "User-agent: *\nAllow: /"

        async def fake_sitemap(base_url, timeout):
            assert base_url == "https://example.com/"
            return SITEMAP_URLSET

        result = asyncio.run(
            fetch_site(
                "example.com",
                fetch_page_fn=fake_page,
                fetch_robots_fn=fake_robots,
                fetch_sitemap_fn=fake_sitemap,
                now=NOW,
            )
        )

        assert result.reachability == Reachability.OK
        assert result.robots_txt == "User-agent: *\nAllow: /"
        assert result.sitemap_urls == ["https://example.com/", "https://example.com/about"]

    def test_sitemap_index_is_expanded_by_fetching_each_sub_sitemap(self):
        sub_sitemaps_by_url = {
            "https://example.com/sitemap-posts.xml": SITEMAP_POSTS,
            "https://example.com/sitemap-pages.xml": SITEMAP_PAGES,
        }

        async def fake_page(url, timeout):
            return PageFetchOutcome(
                ok=True, status_code=200, final_url="https://example.com/", html="<html/>"
            )

        async def fake_robots(base_url, timeout):
            return None

        async def fake_sitemap(base_url, timeout):
            return SITEMAP_INDEX

        async def fake_sub_sitemap(url, timeout):
            return sub_sitemaps_by_url[url]

        result = asyncio.run(
            fetch_site(
                "example.com",
                fetch_page_fn=fake_page,
                fetch_robots_fn=fake_robots,
                fetch_sitemap_fn=fake_sitemap,
                fetch_sub_sitemap_fn=fake_sub_sitemap,
                now=NOW,
            )
        )

        assert result.reachability == Reachability.OK
        assert result.sitemap_urls == [
            "https://example.com/posts/1",
            "https://example.com/posts/2",
            "https://example.com/about",
            "https://example.com/contact",
        ]

    def test_sitemap_index_with_one_failing_sub_sitemap_keeps_the_rest(self):
        async def fake_page(url, timeout):
            return PageFetchOutcome(
                ok=True, status_code=200, final_url="https://example.com/", html="<html/>"
            )

        async def fake_robots(base_url, timeout):
            return None

        async def fake_sitemap(base_url, timeout):
            return SITEMAP_INDEX

        async def fake_sub_sitemap(url, timeout):
            if url == "https://example.com/sitemap-posts.xml":
                raise TimeoutError("sub-sitemap timed out")
            assert url == "https://example.com/sitemap-pages.xml"
            return SITEMAP_PAGES

        result = asyncio.run(
            fetch_site(
                "example.com",
                fetch_page_fn=fake_page,
                fetch_robots_fn=fake_robots,
                fetch_sitemap_fn=fake_sitemap,
                fetch_sub_sitemap_fn=fake_sub_sitemap,
                now=NOW,
            )
        )

        assert result.reachability == Reachability.OK
        assert result.sitemap_urls == ["https://example.com/about", "https://example.com/contact"]
        assert any("failed" in note for note in result.notes)

    def test_sitemap_index_beyond_max_sub_sitemaps_cap_is_noted_not_failed(self):
        declared = MAX_SUB_SITEMAPS + 5
        big_index = "".join(
            f"<sitemap><loc>https://example.com/sm-{i}.xml</loc></sitemap>" for i in range(declared)
        )
        big_index_xml = (
            f'<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f"{big_index}</sitemapindex>"
        )
        fetched_urls: list[str] = []

        async def fake_page(url, timeout):
            return PageFetchOutcome(
                ok=True, status_code=200, final_url="https://example.com/", html="<html/>"
            )

        async def fake_robots(base_url, timeout):
            return None

        async def fake_sitemap(base_url, timeout):
            return big_index_xml

        async def fake_sub_sitemap(url, timeout):
            fetched_urls.append(url)
            return (
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                f"<url><loc>{url}#page</loc></url></urlset>"
            )

        result = asyncio.run(
            fetch_site(
                "example.com",
                fetch_page_fn=fake_page,
                fetch_robots_fn=fake_robots,
                fetch_sitemap_fn=fake_sitemap,
                fetch_sub_sitemap_fn=fake_sub_sitemap,
                now=NOW,
            )
        )

        assert result.reachability == Reachability.OK
        assert (
            len(fetched_urls) == MAX_SUB_SITEMAPS
        )  # cap respected, not all declared were followed
        assert len(result.sitemap_urls) == MAX_SUB_SITEMAPS
        assert any("MAX_SUB_SITEMAPS" in note for note in result.notes)
