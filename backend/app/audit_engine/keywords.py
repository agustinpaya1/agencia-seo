"""Deterministic search-query suggester.

Derives candidate searches the business could target from on-page signals only:
title, meta description, H1, and the schema @type / location. No network, no LLM.
"""

from .models import FetchResult, KeywordsResult, SchemaResult


def suggest_keywords(fetch: FetchResult, schema: SchemaResult) -> KeywordsResult:
    """Suggest search queries from title, meta, H1 and schema type/location.

    Pure and synchronous: string derivation over already-extracted signals.
    """
    raise NotImplementedError
