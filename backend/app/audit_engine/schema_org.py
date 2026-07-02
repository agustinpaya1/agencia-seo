"""Structured-data validation: the 12 checks from skills/geo-schema/SKILL.md.

Pure Python checklist over the page's JSON-LD — parse blocks, verify properties.
No LLM at any point. The 12 checks are the 12 rows of the scoring rubric in
``skills/geo-schema/SKILL.md`` (they sum to exactly 100 points).

Two layers, kept apart on purpose (task 2, point 2):

* :func:`evaluate_schema_blocks` — **pure and synchronous**. Receives the raw
  ``<script type="application/ld+json">`` block strings already lifted out of the
  HTML, plus a few HTML-derived flags, and returns a full :class:`SchemaResult`.
  It parses the JSON itself, because "is the JSON-LD syntactically valid?" is
  validation step #1 in the SKILL and one of the 12 checks — so malformed JSON
  has to be observable here. No network, trivially unit-testable.
* :func:`validate_schema` — the **async shell**. It only does the two things that
  need I/O or the DOM: pull the JSON-LD blocks (and microdata/RDFa signals) out of
  ``fetch.html``, and resolve the ``sameAs`` URLs with HEAD so the checklist can
  tell a live profile link from a dead one. It then delegates to the pure layer.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .models import FetchResult, SchemaCheck, SchemaResult

# --------------------------------------------------------------------------- #
# Vocabulary the checklist reasons about
# --------------------------------------------------------------------------- #
# schema.org Organization + the common subtypes that "extend" it (SKILL Step 3).
_ORGANIZATION_TYPES = {
    "Organization",
    "Corporation",
    "LocalBusiness",
    "OnlineBusiness",
    "OnlineStore",
    "NGO",
    "GovernmentOrganization",
    "EducationalOrganization",
    "MedicalOrganization",
    "NewsMediaOrganization",
    "Airline",
    "Consortium",
}

_ARTICLE_TYPES = {"Article", "NewsArticle", "BlogPosting", "TechArticle", "Report"}

# "Business-type-specific" schema (rubric row 4) -> its own required props.
# Article/LocalBusiness subtypes are folded onto their base below.
_BUSINESS_TYPE_REQUIRED: dict[str, set[str]] = {
    "LocalBusiness": {"name", "address", "telephone"},
    "Product": {"name", "offers"},
    "SoftwareApplication": {"name", "applicationCategory", "offers"},
    "Article": {"headline", "author", "datePublished"},
    "FAQPage": {"mainEntity"},
    "Recipe": {"name", "recipeIngredient", "recipeInstructions"},
    "Event": {"name", "startDate", "location"},
    "Course": {"name", "description"},
    "Service": {"name", "provider"},
}

# Deprecated schemas the SKILL says to *remove/replace* (Step 4). HowTo and
# FAQPage are "changed/restricted" but still useful for GEO, so they are NOT
# penalised here — only flagged as a note when present.
_DEPRECATED_TYPES = {"SpecialAnnouncement", "CourseInfo"}
_CHANGED_BUT_USEFUL_TYPES = {"HowTo", "FAQPage"}

# Curated subset of recognised schema.org @types (GEO-relevant + the nested types
# that show up inside them). This is intentionally NOT the full schema.org
# vocabulary: an unknown @type is treated as a *minor* issue, never a hard error.
_KNOWN_TYPES = (
    _ORGANIZATION_TYPES
    | _ARTICLE_TYPES
    | set(_BUSINESS_TYPE_REQUIRED)
    | _DEPRECATED_TYPES
    | _CHANGED_BUT_USEFUL_TYPES
    | {
        "WebSite", "WebPage", "BreadcrumbList", "ListItem", "Person", "Brand",
        "Offer", "AggregateOffer", "AggregateRating", "Rating", "Review",
        "ImageObject", "VideoObject", "AudioObject", "PostalAddress",
        "ContactPoint", "GeoCoordinates", "OpeningHoursSpecification", "Place",
        "SearchAction", "EntryPoint", "Question", "Answer",
        "SpeakableSpecification", "QuantitativeValue", "MonetaryAmount",
        "DefinedTerm", "PropertyValue", "Occupation", "EducationalOrganization",
        "CollectionPage", "AboutPage", "ContactPage", "ProfilePage",
        "Restaurant", "Store", "Dentist", "Physician", "Attorney", "HomeAndConstructionBusiness",
    }
)

# Browser-ish UA for the sameAs HEAD probes (mirrors scripts/fetch_page.py).
_HEAD_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
_HEAD_TIMEOUT = 8  # seconds per sameAs probe


# --------------------------------------------------------------------------- #
# Small JSON-LD helpers (pure)
# --------------------------------------------------------------------------- #
def _iter_nodes(obj: Any):
    """Yield every entity ``dict`` from a parsed JSON-LD value.

    Flattens top-level lists and the ``@graph`` container so each schema entity
    becomes one node. Nested entities (an ``author`` Person inside an Article)
    stay attached to their parent — the checks that care about them read the
    property directly.
    """
    if isinstance(obj, list):
        for item in obj:
            yield from _iter_nodes(item)
    elif isinstance(obj, dict):
        graph = obj.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                yield from _iter_nodes(item)
        else:
            yield obj


def _parse_nodes(raw_blocks: Sequence[str]) -> tuple[list[dict], int, int]:
    """Parse raw JSON-LD strings into (nodes, valid_block_count, invalid_block_count).

    Pure: JSON syntax errors are counted, not raised, because "valid JSON" is one
    of the 12 checks.
    """
    nodes: list[dict] = []
    valid = 0
    invalid = 0
    for raw in raw_blocks:
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError, ValueError):
            invalid += 1
            continue
        valid += 1
        nodes.extend(_iter_nodes(parsed))
    return nodes, valid, invalid


def _short_type(value: str) -> str:
    """``http://schema.org/Organization`` / ``schema:Person`` -> bare type name."""
    return value.rsplit("/", 1)[-1].rsplit("#", 1)[-1].split(":")[-1].strip()


def _types_of(node: Any) -> set[str]:
    """Normalised set of ``@type`` names for a node (handles str or list)."""
    if not isinstance(node, dict):
        return set()
    raw = node.get("@type")
    if isinstance(raw, str):
        return {_short_type(raw)}
    if isinstance(raw, list):
        return {_short_type(t) for t in raw if isinstance(t, str)}
    return set()


def _has(node: Mapping[str, Any], key: str) -> bool:
    """True if ``key`` is present with a non-empty value."""
    if key not in node:
        return False
    value = node[key]
    if value is None:
        return False
    if isinstance(value, (str, list, dict, tuple)) and len(value) == 0:
        return False
    return True


def _as_list(value: Any) -> list:
    """Coerce a scalar / list JSON-LD property into a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _is_org(node: Any) -> bool:
    return bool(_types_of(node) & _ORGANIZATION_TYPES)


def _is_person(node: Any) -> bool:
    return "Person" in _types_of(node)


def _check(cid: str, label: str, points: float, max_points: float, notes: list[str]) -> SchemaCheck:
    return SchemaCheck(id=cid, label=label, points=points, max_points=max_points, notes=notes)


# --------------------------------------------------------------------------- #
# Pure layer: the 12 checks
# --------------------------------------------------------------------------- #
def evaluate_schema_blocks(
    raw_blocks: Sequence[str],
    *,
    has_microdata: bool = False,
    has_rdfa: bool = False,
    server_rendered: bool = True,
    is_homepage: bool = False,
    url_status: Mapping[str, bool] | None = None,
) -> SchemaResult:
    """Run the 12 geo-schema validations over already-extracted JSON-LD blocks.

    Pure and synchronous — no network. ``raw_blocks`` are the text bodies of the
    ``<script type="application/ld+json">`` tags (the async shell extracts them);
    JSON parsing happens here so malformed JSON is caught by the "valid JSON"
    check.

    ``url_status`` maps a ``sameAs`` URL to whether it resolves (HEAD, filled in
    by the shell). When it is ``None`` the links are counted but reported as
    unverified, so this function stays runnable with zero I/O.
    """
    nodes, valid_blocks, invalid_blocks = _parse_nodes(raw_blocks)
    has_jsonld = bool(list(raw_blocks))

    org_person = [n for n in nodes if _is_org(n) or _is_person(n)]
    article_nodes = [n for n in nodes if _types_of(n) & _ARTICLE_TYPES]
    website_nodes = [n for n in nodes if "WebSite" in _types_of(n)]
    breadcrumb_nodes = [n for n in nodes if "BreadcrumbList" in _types_of(n)]
    types_present = {t for n in nodes for t in _types_of(n)}

    checks: list[SchemaCheck] = [
        _check_organization(org_person),
        _check_sameas(org_person, url_status),
        _check_article_author(article_nodes),
        _check_business_type(nodes),
        _check_website_searchaction(website_nodes),
        _check_breadcrumb(breadcrumb_nodes, is_homepage),
        _check_format(has_jsonld, has_microdata, has_rdfa),
        _check_server_rendered(has_jsonld, server_rendered),
        _check_speakable(nodes, article_nodes),
        _check_valid_json(has_jsonld, invalid_blocks, nodes),
        _check_knowsabout(org_person),
        _check_no_deprecated(types_present),
    ]

    return SchemaResult(
        detected_types=sorted(types_present),
        format=_schema_format(has_jsonld, has_microdata, has_rdfa),
        json_ld_valid=has_jsonld and invalid_blocks == 0,
        server_rendered=server_rendered and has_jsonld,
        checks=checks,
        score=round(sum(c.points for c in checks), 2),
    )


def _check_organization(org_person: list[dict]) -> SchemaCheck:
    """Rubric row 1 (max 15): Organization/Person present and complete."""
    cid, label, mx = "organization-or-person-present", "Organization/Person schema present and complete", 15.0
    if not org_person:
        return _check(cid, label, 0.0, mx, ["No se encontró esquema Organization ni Person."])

    best = 0.0
    best_notes: list[str] = []
    for node in org_person:
        if _is_org(node):
            required = {"name", "url", "logo"}
            recommended = {"description", "sameAs", "foundingDate", "founder",
                           "address", "contactPoint", "areaServed", "knowsAbout"}
            kind = "Organization"
        else:
            required = {"name", "url"}
            recommended = {"sameAs", "jobTitle", "worksFor", "knowsAbout",
                           "alumniOf", "award", "description", "image"}
            kind = "Person"
        missing_req = sorted(k for k in required if not _has(node, k))
        rec_count = sum(1 for k in recommended if _has(node, k))
        if not missing_req and rec_count >= 2:
            return _check(cid, label, mx, mx,
                          [f"{kind} completo: requeridos presentes y {rec_count} recomendados."])
        if best < 10.0:
            best = 10.0
            note = f"{kind} básico."
            if missing_req:
                note += f" Faltan requeridos: {', '.join(missing_req)}."
            note += f" Recomendados presentes: {rec_count} (se necesitan ≥2 para 'completo')."
            best_notes = [note]
    return _check(cid, label, best, mx, best_notes)


def _check_sameas(org_person: list[dict], url_status: Mapping[str, bool] | None) -> SchemaCheck:
    """Rubric row 2 (max 15): sameAs links, 3 pts each capped at 15."""
    cid, label, mx = "sameas-links", "sameAs links to external platforms (3 pts each, max 15)", 15.0
    urls: list[str] = []
    for node in org_person:
        for value in _as_list(node.get("sameAs")):
            if isinstance(value, str) and value.strip() and value not in urls:
                urls.append(value.strip())

    if not urls:
        note = ("Sin sameAs en Organization/Person." if org_person
                else "Sin Organization/Person, no hay sameAs que evaluar.")
        return _check(cid, label, 0.0, mx, [note])

    if url_status is None:
        points = min(len(urls) * 3.0, mx)
        return _check(cid, label, points, mx,
                      [f"{len(urls)} sameAs declarados (sin verificar resolución de red)."])

    resolving = [u for u in urls if url_status.get(u, False)]
    dead = [u for u in urls if not url_status.get(u, False)]
    points = min(len(resolving) * 3.0, mx)
    notes = [f"{len(resolving)}/{len(urls)} sameAs resuelven vía HEAD (3 pts c/u, máx 15)."]
    if dead:
        notes.append("No resuelven (404/timeout): " + ", ".join(dead))
    return _check(cid, label, points, mx, notes)


def _check_article_author(article_nodes: list[dict]) -> SchemaCheck:
    """Rubric row 3 (max 10): Article with author details."""
    cid, label, mx = "article-author-details", "Article schema with author details", 10.0
    if not article_nodes:
        return _check(cid, label, 0.0, mx, ["No hay esquema Article."])

    best = 0.0
    detail_props = ("url", "sameAs", "jobTitle", "worksFor", "knowsAbout")
    for article in article_nodes:
        for author in _as_list(article.get("author")):
            if isinstance(author, dict):
                if _has(author, "name") and any(_has(author, p) for p in detail_props):
                    return _check(cid, label, mx, mx, ["Autor con nombre y datos de perfil (E-E-A-T)."])
                if _has(author, "name"):
                    best = max(best, 5.0)
            elif isinstance(author, str) and author.strip():
                best = max(best, 5.0)
    if best == 0.0:
        return _check(cid, label, 0.0, mx, ["Article sin propiedad author."])
    return _check(cid, label, best, mx, ["Autor presente solo con nombre (sin url/sameAs/jobTitle…)."])


def _check_business_type(nodes: list[dict]) -> SchemaCheck:
    """Rubric row 4 (max 10): business-type-specific schema present."""
    cid, label, mx = "business-type-schema", "Business-type-specific schema present", 10.0
    best = 0.0
    best_notes: list[str] = []
    for node in nodes:
        req = _business_type_requirement(_types_of(node))
        if req is None:
            continue
        type_name, required = req
        missing = sorted(k for k in required if not _has(node, k))
        if not missing:
            return _check(cid, label, mx, mx, [f"{type_name} completo (requeridos presentes)."])
        if best < 5.0:
            best = 5.0
            best_notes = [f"{type_name} parcial. Faltan requeridos: {', '.join(missing)}."]
    if best == 0.0:
        return _check(cid, label, 0.0, mx,
                      ["Sin esquema específico de tipo de negocio (LocalBusiness/Product/SoftwareApplication/Article…)."])
    return _check(cid, label, best, mx, best_notes)


def _business_type_requirement(types: set[str]) -> tuple[str, set[str]] | None:
    """Map a node's @types onto a business-type name + its required props.

    Plain Organization/Person is rubric row 1, not a "business-type-specific"
    schema, so it is intentionally not matched here. Article and LocalBusiness
    subtypes fold onto their base type's requirements.
    """
    if types & _ARTICLE_TYPES:
        return "Article", _BUSINESS_TYPE_REQUIRED["Article"]
    # LocalBusiness subtypes (Restaurant, Store, Dentist, …) count as LocalBusiness.
    if types & {"Restaurant", "Store", "Dentist", "Physician", "Attorney",
                "HomeAndConstructionBusiness"}:
        return "LocalBusiness", _BUSINESS_TYPE_REQUIRED["LocalBusiness"]
    for name, required in _BUSINESS_TYPE_REQUIRED.items():
        if name in types:
            return name, required
    return None


def _check_website_searchaction(website_nodes: list[dict]) -> SchemaCheck:
    """Rubric row 5 (max 5): WebSite + SearchAction."""
    cid, label, mx = "website-searchaction", "WebSite schema with SearchAction", 5.0
    for site in website_nodes:
        for action in _as_list(site.get("potentialAction")):
            if isinstance(action, dict) and "SearchAction" in _types_of(action):
                return _check(cid, label, mx, mx, ["WebSite con potentialAction SearchAction."])
    if website_nodes:
        return _check(cid, label, 0.0, mx, ["WebSite presente pero sin SearchAction."])
    return _check(cid, label, 0.0, mx, ["Sin esquema WebSite + SearchAction."])


def _check_breadcrumb(breadcrumb_nodes: list[dict], is_homepage: bool) -> SchemaCheck:
    """Rubric row 6 (max 5): BreadcrumbList on inner pages.

    The rubric scopes this to *inner* pages. On the homepage a breadcrumb is not
    expected, so its absence is treated as N/A (full points) rather than a miss.
    """
    cid, label, mx = "breadcrumblist", "BreadcrumbList on inner pages", 5.0
    if breadcrumb_nodes:
        return _check(cid, label, mx, mx, ["BreadcrumbList presente."])
    if is_homepage:
        return _check(cid, label, mx, mx,
                      ["N/A: es la homepage; el rubric solo pide breadcrumb en páginas internas."])
    return _check(cid, label, 0.0, mx, ["Falta BreadcrumbList en una página interna."])


def _check_format(has_jsonld: bool, has_microdata: bool, has_rdfa: bool) -> SchemaCheck:
    """Rubric row 7 (max 5): JSON-LD (5) / mixed (3) / only microdata|rdfa (0)."""
    cid, label, mx = "json-ld-format", "Structured data uses JSON-LD (not Microdata/RDFa)", 5.0
    other = has_microdata or has_rdfa
    if has_jsonld and not other:
        return _check(cid, label, mx, mx, ["Solo JSON-LD (formato recomendado para GEO)."])
    if has_jsonld and other:
        return _check(cid, label, 3.0, mx, ["Mixto: JSON-LD junto a microdata/RDFa."])
    if other:
        return _check(cid, label, 0.0, mx, ["Solo microdata/RDFa; migrar a JSON-LD."])
    return _check(cid, label, 0.0, mx, ["Sin datos estructurados."])


def _check_server_rendered(has_jsonld: bool, server_rendered: bool) -> SchemaCheck:
    """Rubric row 8 (max 10): JSON-LD in the server HTML, not JS-injected."""
    cid, label, mx = "server-rendered", "Structured data server-rendered (not JS-injected)", 10.0
    if has_jsonld and server_rendered:
        return _check(cid, label, mx, mx, ["JSON-LD presente en el HTML servido por el origen."])
    return _check(cid, label, 0.0, mx,
                  ["Sin JSON-LD en el HTML servido (ausente o inyectado por JS; "
                   "el fetch estático no ejecuta JavaScript)."])


def _check_speakable(nodes: list[dict], article_nodes: list[dict]) -> SchemaCheck:
    """Rubric row 9 (max 5): speakable property on Article/WebPage."""
    cid, label, mx = "speakable-property", "speakable property on Article/WebPage", 5.0
    if any(_has(n, "speakable") for n in nodes):
        return _check(cid, label, mx, mx, ["Propiedad speakable presente."])
    note = "Sin propiedad speakable."
    if not article_nodes:
        note += " (speakable aplica a Article/WebPage.)"
    return _check(cid, label, 0.0, mx, [note])


def _check_valid_json(has_jsonld: bool, invalid_blocks: int, nodes: list[dict]) -> SchemaCheck:
    """Rubric row 10 (max 10): valid JSON (10) / minor type issues (5) / errors (0)."""
    cid, label, mx = "valid-json-and-types", "Valid JSON and recognized Schema.org @type", 10.0
    if not has_jsonld:
        return _check(cid, label, 0.0, mx, ["Sin datos estructurados que validar."])
    if invalid_blocks:
        return _check(cid, label, 0.0, mx,
                      [f"{invalid_blocks} bloque(s) JSON-LD con JSON inválido (error mayor)."])
    missing_type = sum(1 for n in nodes if not _types_of(n))
    unknown = sorted({t for n in nodes for t in _types_of(n) if t not in _KNOWN_TYPES})
    if missing_type or unknown:
        notes = ["JSON válido, con incidencias menores."]
        if missing_type:
            notes.append(f"{missing_type} nodo(s) sin @type.")
        if unknown:
            notes.append("@type no reconocidos (subconjunto curado): " + ", ".join(unknown))
        return _check(cid, label, 5.0, mx, notes)
    return _check(cid, label, mx, mx, ["JSON válido y todos los @type reconocidos."])


def _check_knowsabout(org_person: list[dict]) -> SchemaCheck:
    """Rubric row 11 (max 5): knowsAbout with 3+ topics on Organization/Person."""
    cid, label, mx = "knowsabout-topics", "knowsAbout property on Organization/Person (3+ topics)", 5.0
    topics: list[Any] = []
    for node in org_person:
        topics.extend(t for t in _as_list(node.get("knowsAbout")) if t)
    if len(topics) >= 3:
        return _check(cid, label, mx, mx, [f"knowsAbout con {len(topics)} temas."])
    if topics:
        return _check(cid, label, 0.0, mx, [f"knowsAbout con solo {len(topics)} tema(s); se necesitan ≥3."])
    return _check(cid, label, 0.0, mx, ["Sin propiedad knowsAbout en Organization/Person."])


def _check_no_deprecated(types_present: set[str]) -> SchemaCheck:
    """Rubric row 12 (max 5): no deprecated schemas present."""
    cid, label, mx = "no-deprecated-schemas", "No deprecated schemas present", 5.0
    deprecated = sorted(types_present & _DEPRECATED_TYPES)
    if deprecated:
        return _check(cid, label, 0.0, mx,
                      ["Esquemas obsoletos presentes (eliminar/reemplazar): " + ", ".join(deprecated)])
    changed = sorted(types_present & _CHANGED_BUT_USEFUL_TYPES)
    if changed:
        return _check(cid, label, mx, mx,
                      ["Sin esquemas obsoletos. Cambiados pero aún útiles para GEO: " + ", ".join(changed)])
    return _check(cid, label, mx, mx, ["Sin esquemas obsoletos."])


def _schema_format(has_jsonld: bool, has_microdata: bool, has_rdfa: bool) -> str:
    other = has_microdata or has_rdfa
    if has_jsonld and other:
        return "mixed"
    if has_jsonld:
        return "json-ld"
    if has_microdata and has_rdfa:
        return "mixed"
    if has_microdata:
        return "microdata"
    if has_rdfa:
        return "rdfa"
    return "none"


# --------------------------------------------------------------------------- #
# Async shell: HTML extraction + sameAs HEAD resolution
# --------------------------------------------------------------------------- #
async def validate_schema(fetch: FetchResult) -> SchemaResult:
    """Parse and validate JSON-LD structured data against the 12-point rubric.

    Thin async wrapper around :func:`evaluate_schema_blocks`: it extracts the
    JSON-LD blocks (and microdata/RDFa signals) from ``fetch.html`` and resolves
    the ``sameAs`` URLs with HEAD. All scoring is delegated to the pure layer.
    """
    html = fetch.html or ""
    is_homepage = _is_homepage(fetch)

    if not html:
        return evaluate_schema_blocks(
            [], has_microdata=False, has_rdfa=False,
            server_rendered=False, is_homepage=is_homepage, url_status={},
        )

    soup = BeautifulSoup(html, "html.parser")
    raw_blocks = _extract_jsonld_blocks(soup)
    has_microdata = _detect_microdata(soup)
    has_rdfa = _detect_rdfa(soup)

    # JSON-LD found in the server response HTML is, by definition, server-rendered
    # (the static fetch never executes JavaScript).
    server_rendered = bool(raw_blocks)

    same_as_urls = _collect_sameas_urls(raw_blocks)
    url_status = await _resolve_urls(same_as_urls)

    return evaluate_schema_blocks(
        raw_blocks,
        has_microdata=has_microdata,
        has_rdfa=has_rdfa,
        server_rendered=server_rendered,
        is_homepage=is_homepage,
        url_status=url_status,
    )


def _extract_jsonld_blocks(soup: BeautifulSoup) -> list[str]:
    """Raw text bodies of every ``<script type="application/ld+json">`` block."""
    blocks: list[str] = []
    for script in soup.find_all("script", type="application/ld+json"):
        text = script.string if script.string is not None else script.get_text()
        if text and text.strip():
            blocks.append(text)
    return blocks


def _detect_microdata(soup: BeautifulSoup) -> bool:
    return soup.find(attrs={"itemscope": True}) is not None or soup.find(attrs={"itemtype": True}) is not None


def _detect_rdfa(soup: BeautifulSoup) -> bool:
    # `typeof`/`vocab` are RDFa-specific; `property` alone is skipped (OpenGraph
    # meta tags also use it and would give false positives).
    return soup.find(attrs={"typeof": True}) is not None or soup.find(attrs={"vocab": True}) is not None


def _is_homepage(fetch: FetchResult) -> bool:
    target = fetch.final_url or fetch.domain or ""
    if "//" not in target:
        target = "https://" + target
    return urlparse(target).path.strip("/") == ""


def _collect_sameas_urls(raw_blocks: Sequence[str]) -> list[str]:
    """HTTP(S) ``sameAs`` URLs from Organization/Person nodes, de-duplicated."""
    nodes, _, _ = _parse_nodes(raw_blocks)
    urls: list[str] = []
    for node in nodes:
        if not (_is_org(node) or _is_person(node)):
            continue
        for value in _as_list(node.get("sameAs")):
            if not (isinstance(value, str) and value.strip()):
                continue
            candidate = value.strip()
            if urlparse(candidate).scheme in ("http", "https") and candidate not in urls:
                urls.append(candidate)
    return urls


async def _resolve_urls(urls: Sequence[str]) -> dict[str, bool]:
    """HEAD each URL concurrently -> {url: resolves (final status < 400)}."""
    if not urls:
        return {}
    results = await asyncio.gather(*(_head_ok(u) for u in urls))
    return dict(zip(urls, results))


async def _head_ok(url: str) -> bool:
    try:
        return await asyncio.to_thread(_sync_head_ok, url)
    except Exception:
        return False


def _sync_head_ok(url: str) -> bool:
    """True if the URL resolves (not 404). Falls back to GET when HEAD is rejected."""
    try:
        resp = requests.head(url, allow_redirects=True, timeout=_HEAD_TIMEOUT, headers=_HEAD_HEADERS)
        if resp.status_code == 405 or resp.status_code >= 400:
            resp = requests.get(
                url, allow_redirects=True, timeout=_HEAD_TIMEOUT,
                headers=_HEAD_HEADERS, stream=True,
            )
            resp.close()
        return 200 <= resp.status_code < 400
    except requests.RequestException:
        return False
