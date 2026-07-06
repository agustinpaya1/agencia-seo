"""Shared server-side-rendering heuristics for the deterministic audit engine.

Single source of the "what does a JS-less crawler actually see?" judgment, so the
two places that reason about it — schema_org.py's ``server-rendered`` check and
technical.py's SSR dimension (the heaviest weight, 25%) — cannot produce
contradictory verdicts for the same fetch. Two SSR detectors with different
criteria in the same report would be a real credibility problem for the engine.

Two distinct signals live here, on purpose:

* :func:`main_content_server_rendered` — is the *page body* present in the raw
  HTML? This REUSES ``fetch_page.py:assess_ssr_content`` (the tuned Issue
  #19 heuristic), it does not re-implement it. The audit engine already wraps
  fetch_page.py for fetching, so importing its heuristic keeps one code
  path for both the ad-hoc CLI and the engine.
* :func:`structured_data_server_rendered` — is JSON-LD present in the raw HTML?
  This mirrors, byte-for-byte, the criterion schema_org.py uses
  (``server_rendered = bool(raw_blocks)``). schema_org.py is out of scope to edit
  in this task, so it keeps its own inline copy for now; this module is written so
  that when schema_org.py is next touched it can import from here and the criterion
  is already identical — no behavioural change, just de-duplication.

Everything here is pure and synchronous: parsing HTML, no network, no LLM.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from .fetch_page import assess_ssr_content


def main_content_server_rendered(html: str) -> tuple[bool, int, list[str]]:
    """Reuse the shared body-SSR heuristic -> (has_ssr_content, word_count, notes)."""
    result = assess_ssr_content(html or "")
    return result["has_ssr_content"], result["word_count"], result["errors"]


def iter_jsonld_blocks(html: str) -> list[str]:
    """Raw text bodies of every ``<script type="application/ld+json">`` block.

    Same extraction schema_org.py performs (``html.parser``, non-empty text only),
    so ``bool(iter_jsonld_blocks(html))`` matches its ``server_rendered`` flag.
    """
    soup = BeautifulSoup(html or "", "html.parser")
    blocks: list[str] = []
    for script in soup.find_all("script", type="application/ld+json"):
        text = script.string if script.string is not None else script.get_text()
        if text and text.strip():
            blocks.append(text)
    return blocks


def structured_data_server_rendered(html: str) -> bool:
    """Is JSON-LD structured data present in the raw server HTML?

    Mirrors schema_org.py's ``server_rendered = bool(raw_blocks)`` criterion so the
    schema report and the technical report never disagree about whether structured
    data is server-rendered on the same page.
    """
    return bool(iter_jsonld_blocks(html))
