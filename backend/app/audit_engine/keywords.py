"""Deterministic search-query suggester.

Derives candidate searches the business could target from on-page signals only:
title, meta description, H1, and the schema @type / location. No network, no LLM.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .models import FetchResult, KeywordsResult, KeywordSuggestion, SchemaResult

# Corte (task 7, parte A): hard cap on suggestions returned, to keep the list a
# shortlist a human can scan rather than every permutation of the signals.
_MAX_SUGGESTIONS = 8

_TITLE_SEPARATORS = re.compile(r"\s*[|–—·»]\s*|\s+-\s+")

# Curated business-type -> Spanish service noun, used to turn a schema.org @type
# into a query term. Deliberately small: only types with an unambiguous,
# single-word service label are mapped, everything else is skipped rather than
# guessed at.
_BUSINESS_TYPE_LABELS = {
    "Restaurant": "restaurante",
    "Store": "tienda",
    "Dentist": "dentista",
    "Physician": "médico",
    "Attorney": "abogado",
    "HomeAndConstructionBusiness": "construcción",
    "LocalBusiness": "negocio local",
    "Product": "producto",
    "SoftwareApplication": "software",
    "Service": "servicio",
    "Event": "evento",
    "Course": "curso",
}

# Subset of the above that implies a physical location worth looking for
# (mirrors schema_org.py's own LocalBusiness-subtype grouping).
_LOCALBUSINESS_TYPES = {
    "LocalBusiness",
    "Restaurant",
    "Store",
    "Dentist",
    "Physician",
    "Attorney",
    "HomeAndConstructionBusiness",
}


def suggest_keywords(fetch: FetchResult, schema: SchemaResult) -> KeywordsResult:
    """Suggest search queries from title, meta, H1 and schema type/location.

    Pure and synchronous: string derivation over already-fetched HTML and the
    already-resolved :class:`SchemaResult` (task 2), no network calls of its own.
    """
    soup = BeautifulSoup(fetch.html or "", "html.parser")

    title = _extract_title(soup)
    meta = _extract_meta_description(soup)
    h1 = _extract_h1(soup)
    schema_type = _extract_schema_type(schema.detected_types)
    # Corte: only bother looking for a location string when the schema signals a
    # LocalBusiness-family type — a location without a local-business context is
    # not a signal this module is meant to derive queries from (task wording:
    # "ubicación (si hay LocalBusiness/address en el schema)").
    location = _extract_location(soup) if _has_local_business(schema.detected_types) else None

    signals: dict[str, str | None] = {
        "title": title,
        "meta": meta,
        "h1": h1,
        "schema_type": schema_type,
        "location": location,
    }

    suggestions: list[KeywordSuggestion] = []
    seen: set[str] = set()

    def add(query: str | None, source: str, note: str) -> None:
        if not query or len(suggestions) >= _MAX_SUGGESTIONS:
            return
        key = query.strip().lower()
        if not key or key in seen:
            return
        seen.add(key)
        suggestions.append(KeywordSuggestion(query=query.strip(), source=source, notes=[note]))

    # Corte: when both a service label and a location are available, combine
    # them into one "{servicio} en {ubicación}" query instead of two separate
    # suggestions — that combined form is the actual local-SEO query pattern;
    # emitting them separately would just be noise.
    if schema_type and location:
        add(
            f"{schema_type} en {location}",
            "location",
            "Combina el tipo de negocio (schema.org) y la ubicación detectada.",
        )
    elif location:
        add(location, "location", "Ubicación detectada, sin tipo de negocio para combinar.")

    add(_primary_segment(title), "title", "Segmento principal de <title>.")
    add(h1, "h1", "Texto de H1.")
    add(_meta_candidate(meta), "meta", "Extracto de la meta description.")

    if schema_type and not location:
        add(schema_type, "schema_type", "Tipo de negocio detectado en schema.org.")

    return KeywordsResult(signals=signals, suggestions=suggestions)


# --------------------------------------------------------------------------- #
# Signal extraction (pure, over already-parsed HTML)
# --------------------------------------------------------------------------- #
def _extract_title(soup: BeautifulSoup) -> str | None:
    tag = soup.find("title")
    text = tag.get_text(strip=True) if tag else None
    return text or None


def _extract_meta_description(soup: BeautifulSoup) -> str | None:
    tag = soup.find("meta", attrs={"name": "description"})
    content = tag.get("content") if tag else None
    return content.strip() if content and content.strip() else None


def _extract_h1(soup: BeautifulSoup) -> str | None:
    tag = soup.find("h1")
    text = tag.get_text(strip=True) if tag else None
    return text or None


def _extract_schema_type(detected_types: list[str]) -> str | None:
    # detected_types is already sorted (schema_org.py), so the pick is deterministic.
    for t in detected_types:
        if t in _BUSINESS_TYPE_LABELS:
            return _BUSINESS_TYPE_LABELS[t]
    return None


def _has_local_business(detected_types: list[str]) -> bool:
    return bool(set(detected_types) & _LOCALBUSINESS_TYPES)


def _extract_location(soup: BeautifulSoup) -> str | None:
    address = soup.find("address")
    if address:
        text = address.get_text(" ", strip=True)
        if text:
            return text
    for name in ("geo.placename", "ICBM"):
        tag = soup.find("meta", attrs={"name": name})
        content = tag.get("content") if tag else None
        if content and content.strip():
            return content.strip()
    tag = soup.find("meta", attrs={"property": "business:contact_data:locality"})
    content = tag.get("content") if tag else None
    if content and content.strip():
        return content.strip()
    return None


def _primary_segment(title: str | None) -> str | None:
    """First segment of a "Service | Brand"-style <title>, else the whole title."""
    if not title:
        return None
    parts = [p for p in _TITLE_SEPARATORS.split(title) if p.strip()]
    return parts[0].strip() if parts else title


def _meta_candidate(meta: str | None) -> str | None:
    """Short query candidate from the meta description: first sentence, capped."""
    if not meta:
        return None
    first_sentence = meta.split(".")[0].strip()
    words = first_sentence.split()
    return " ".join(words[:12]) if words else None
