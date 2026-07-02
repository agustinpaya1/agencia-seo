"""Deterministic technical SEO scoring (pure, synchronous, no network, no LLM).

Ports the 8-weight technical rubric to a pure function over the initial fetch
and the detected stack only. It deliberately does NOT consume SecurityResult or
PerformanceResult: the ``security_headers_estimate`` dimension reads the headers
already present in ``fetch.headers``, and ``cwv_static_estimate`` is a static
guess from the HTML. The authoritative security and Core Web Vitals numbers live
in security.py and performance.py and are combined separately in
:func:`audit_engine.orchestrator.evaluate_weighted_score`.

Per-dimension criteria follow skills/geo-technical/SKILL.md. Where the SKILL asks
for something a single static fetch cannot see (crawl depth, real-user Core Web
Vitals, tap-target sizes, redirect-chain length), the dimension scores what *is*
observable and says so in a finding rather than inventing a number.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .models import FetchResult, Reachability, TechnicalResult, TechStackResult, WeightedDimension
from .ssr import main_content_server_rendered, structured_data_server_rendered

# Rubric weights (sum = 100). "mobile" is 15 (not 10): the business priority is
# that the site is found and works well from mobile devices. The
# *_estimate keys are deliberately named to signal they are estimates, not the
# authoritative security.py / performance.py results.
WEIGHTS: dict[str, int] = {
    "ssr": 25,
    "meta_indexability": 15,
    "crawlability": 15,
    "security_headers_estimate": 10,
    "cwv_static_estimate": 10,
    "mobile": 15,
    "url_structure": 5,
    "status": 5,
}

# SSR sub-weights, normalised to 0-100 from the SKILL's 8 / 4 / 3 split (the "4"
# for "meta tags + structured data" is split evenly between the two).
_SSR_MAIN = 8 / 15 * 100
_SSR_META = 2 / 15 * 100
_SSR_STRUCT = 2 / 15 * 100
_SSR_LINKS = 3 / 15 * 100

# AI crawler user-agents whose robots.txt access matters most for GEO (SKILL 1.2).
_AI_AGENTS = {
    "gptbot", "oai-searchbot", "chatgpt-user", "perplexitybot", "claudebot",
    "anthropic-ai", "ccbot", "google-extended", "bytespider", "applebot-extended",
    "amazonbot", "facebookbot",
}


def score_technical(fetch: FetchResult, stack: TechStackResult) -> TechnicalResult:
    """Compute the weighted technical score from fetch + stack only.

    Pure and synchronous: no network calls, no LLM. Each key in :data:`WEIGHTS`
    becomes a :class:`WeightedDimension`; the total is their weighted sum on a
    0-100 scale.
    """
    html = fetch.html or ""
    soup = BeautifulSoup(html, "html.parser") if html else None
    headers_ci = {k.lower(): v for k, v in (fetch.headers or {}).items()}

    dimensions = [
        _score_ssr(fetch, soup, html, stack),
        _score_meta_indexability(soup, headers_ci),
        _score_crawlability(fetch),
        _score_security_headers(fetch, headers_ci),
        _score_cwv_static(soup, stack),
        _score_mobile(soup),
        _score_url_structure(fetch),
        _score_status(fetch),
    ]
    total = round(sum(d.points for d in dimensions), 2)
    return TechnicalResult(dimensions=dimensions, score=total)


# --------------------------------------------------------------------------- #
# Dimension builder
# --------------------------------------------------------------------------- #
def _dim(name: str, score: float, findings: list[str]) -> WeightedDimension:
    """Build a WeightedDimension, clamping score to 0-100 and deriving points."""
    weight = WEIGHTS[name] / 100.0
    score = max(0.0, min(100.0, score))
    return WeightedDimension(
        name=name,
        score=round(score, 2),
        weight=weight,
        points=round(score * weight, 2),
        findings=findings,
    )


# --------------------------------------------------------------------------- #
# 1. SSR (25%) — SKILL Category 7, the heaviest weight
# --------------------------------------------------------------------------- #
def _score_ssr(
    fetch: FetchResult, soup: BeautifulSoup | None, html: str, stack: TechStackResult
) -> WeightedDimension:
    if not html or soup is None:
        return _dim("ssr", 0.0, [
            "Sin HTML servido (sitio no alcanzable o respuesta vacía): un crawler "
            "sin JavaScript no vería contenido alguno."
        ])

    score = 0.0
    findings: list[str] = []

    # 1a. Main body in the raw HTML — reuses the shared Issue #19 heuristic.
    has_body, word_count, csr_notes = main_content_server_rendered(html)
    if has_body:
        score += _SSR_MAIN
        findings.append(f"Contenido principal presente en el HTML servido (~{word_count} palabras).")
    else:
        findings.append(
            f"El contenido principal NO está en el HTML servido (~{word_count} palabras): "
            "un crawler sin JS ve una shell vacía. GPTBot, PerplexityBot y ClaudeBot no "
            "ejecutan JavaScript."
        )
        findings.extend(csr_notes)

    # 1b. Meta tags in the raw HTML (title carries most of the weight).
    has_title = _has_title(soup)
    has_meta_extra = _meta_name_present(soup, "description") or _find_canonical(soup) is not None \
        or soup.find("meta", attrs={"property": re.compile(r"^og:", re.I)}) is not None
    meta_score = _SSR_META * (0.6 * has_title + 0.4 * has_meta_extra)
    score += meta_score
    if has_title and has_meta_extra:
        findings.append("Meta tags (title + description/canonical/OpenGraph) presentes en el HTML servido.")
    elif has_title:
        findings.append("Title presente en el HTML servido, pero falta description/canonical/OpenGraph.")
    else:
        findings.append("Sin <title> en el HTML servido.")

    # 1c. Structured data in the raw HTML — same criterion schema_org.py uses.
    if structured_data_server_rendered(html):
        score += _SSR_STRUCT
        findings.append("Datos estructurados (JSON-LD) presentes en el HTML servido.")
    else:
        findings.append("Sin JSON-LD en el HTML servido (ausente o inyectado por JS).")

    # 1d. Internal links in the raw HTML (crawl path).
    internal = _count_internal_links(soup, fetch)
    if internal >= 5:
        score += _SSR_LINKS
        findings.append(f"{internal} enlaces internos en el HTML servido (ruta de rastreo presente).")
    elif internal >= 1:
        score += _SSR_LINKS * 0.5
        findings.append(f"Solo {internal} enlaces internos en el HTML servido (ruta de rastreo pobre).")
    else:
        findings.append("Sin enlaces internos en el HTML servido: el rastreador no puede descubrir más páginas.")

    # Stack is corroborating context, not a score override: the HTML is what the
    # crawler actually sees, so it stays authoritative for SSR.
    stack_names = _stack_names(stack)
    ssr_stack = bool(stack.cms) or bool(
        stack_names & {"next.js", "nuxt", "nuxt.js", "gatsby", "remix", "sveltekit", "angular universal"}
    )
    spa_stack = bool(stack_names & {"react", "vue", "vue.js", "angular", "svelte"}) and not ssr_stack
    if not has_body and ssr_stack:
        findings.append(
            "Nota: el stack detectado sugiere render de servidor (CMS/framework SSR), pero el "
            "fetch estático no trajo el contenido — posible edge-cache o bloqueo del bot; se "
            "puntúa lo que ve el crawler."
        )
    elif spa_stack and has_body:
        findings.append("Nota: framework SPA detectado, pero el contenido sí aparece server-rendered.")

    return _dim("ssr", score, findings)


# --------------------------------------------------------------------------- #
# 2. Meta / Indexability (15%) — SKILL Category 2 + noindex management (1.5)
# --------------------------------------------------------------------------- #
def _score_meta_indexability(soup: BeautifulSoup | None, headers_ci: dict[str, str]) -> WeightedDimension:
    if soup is None:
        return _dim("meta_indexability", 0.0, ["Sin HTML servido: indexabilidad no evaluable."])

    findings: list[str] = []
    score = 0.0

    robots_meta = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    robots_content = (robots_meta.get("content", "") if robots_meta else "").lower()
    x_robots = (headers_ci.get("x-robots-tag", "") or "").lower()
    noindex = "noindex" in robots_content or "noindex" in x_robots

    if noindex:
        findings.append("La página declara noindex (meta robots / X-Robots-Tag): no será indexada ni citada.")
    else:
        score += 60.0
        findings.append("Indexable (sin directiva noindex).")

    canonical = _find_canonical(soup)
    if canonical:
        score += 40.0
        findings.append(f"Etiqueta canonical presente: {canonical}")
    else:
        findings.append("Sin etiqueta canonical: riesgo de contenido duplicado / dilución de señales.")

    findings.append(
        "Nota: duplicados www/http, paginación, hreflang e index bloat requieren varias URLs "
        "y no se evalúan desde un único fetch."
    )
    return _dim("meta_indexability", score, findings)


# --------------------------------------------------------------------------- #
# 3. Crawlability (15%) — SKILL Category 1 (robots.txt + AI crawler access)
# --------------------------------------------------------------------------- #
def _score_crawlability(fetch: FetchResult) -> WeightedDimension:
    if fetch.reachability != Reachability.OK:
        return _dim("crawlability", 0.0, ["Sitio no alcanzable: crawlability no evaluable."])

    findings: list[str] = []
    score = 0.0
    robots = fetch.robots_txt
    has_sitemap = bool(fetch.sitemap_urls)

    if not robots:
        # No robots.txt = everything crawlable by default (not a block).
        score += 25.0 + 35.0
        findings.append("Sin robots.txt: todo crawlable por defecto. Recomendable añadirlo con la referencia al sitemap.")
        sitemap_in_robots = False
    else:
        score += 20.0
        findings.append("robots.txt presente.")
        signals = _robots_signals(robots)
        sitemap_in_robots = signals["sitemap_referenced"]

        if signals["googlebot_blocked"]:
            findings.append("FATAL: robots.txt bloquea Googlebot (Disallow: /). Sin indexación en Google ni AI Overviews.")
        else:
            score += 25.0
            findings.append("Googlebot permitido.")

        blocked_ai = sorted(signals["ai_blocked"])
        if not blocked_ai:
            score += 35.0
            findings.append("Crawlers de IA (GPTBot, PerplexityBot, ClaudeBot, …) permitidos.")
        else:
            ratio = 1 - len(blocked_ai) / len(_AI_AGENTS)
            score += 35.0 * max(0.0, ratio)
            findings.append("Crawlers de IA bloqueados en robots.txt: " + ", ".join(blocked_ai) + " (impacto GEO).")

    if has_sitemap or sitemap_in_robots:
        score += 20.0
        findings.append("Sitemap XML localizado.")
    else:
        findings.append("Sin sitemap XML localizado (ni en robots.txt ni en sitemap_urls).")

    findings.append("Nota: profundidad de rastreo (≤3 clics) requiere varias páginas; no se evalúa aquí.")
    return _dim("crawlability", score, findings)


# --------------------------------------------------------------------------- #
# 4. Security headers estimate (10%) — SKILL Category 3.2 (from fetch headers)
# --------------------------------------------------------------------------- #
def _score_security_headers(fetch: FetchResult, headers_ci: dict[str, str]) -> WeightedDimension:
    findings: list[str] = []
    score = 0.0

    target = fetch.final_url or fetch.domain or ""
    if "//" not in target:
        target = "https://" + target
    is_https = urlparse(target).scheme == "https" and bool(fetch.final_url)

    if is_https:
        score += 40.0
        findings.append("Servido sobre HTTPS.")
    else:
        findings.append("No se confirma HTTPS desde la URL final del fetch.")

    header_points = {
        "strict-transport-security": (20.0, "HSTS"),
        "x-content-type-options": (10.0, "X-Content-Type-Options"),
        "x-frame-options": (10.0, "X-Frame-Options"),
        "referrer-policy": (10.0, "Referrer-Policy"),
        "content-security-policy": (10.0, "Content-Security-Policy"),
    }
    present, missing = [], []
    for header, (pts, label) in header_points.items():
        if headers_ci.get(header):
            score += pts
            present.append(label)
        else:
            missing.append(label)
    if present:
        findings.append("Cabeceras de seguridad presentes: " + ", ".join(present) + ".")
    if missing:
        findings.append("Cabeceras de seguridad ausentes: " + ", ".join(missing) + ".")

    findings.append("Estimación desde las cabeceras del fetch; el veredicto autoritativo (Observatory/CVEs) lo da security.py.")
    return _dim("security_headers_estimate", score, findings)


# --------------------------------------------------------------------------- #
# 5. Core Web Vitals static estimate (10%) — SKILL Category 6 (no field data)
# --------------------------------------------------------------------------- #
def _score_cwv_static(soup: BeautifulSoup | None, stack: TechStackResult) -> WeightedDimension:
    if soup is None:
        return _dim("cwv_static_estimate", 0.0, ["Sin HTML servido: estimación CWV no evaluable."])

    findings: list[str] = []
    imgs = soup.find_all("img")

    # CLS proxy (40): images that reserve space with explicit width + height.
    dimensioned = sum(1 for img in imgs if img.get("width") and img.get("height"))
    cls_ratio = dimensioned / len(imgs) if imgs else 1.0
    cls_score = 40.0 * cls_ratio
    if imgs:
        findings.append(f"CLS: {dimensioned}/{len(imgs)} imágenes con width+height explícitos (reservan espacio).")
    else:
        findings.append("CLS: sin imágenes; sin riesgo de desplazamiento por imagen.")

    # INP/LCP proxy (35): render-blocking scripts in <head> (no async/defer).
    head = soup.find("head")
    blocking = [
        s for s in (head.find_all("script") if head else [])
        if s.get("src") and not (s.has_attr("async") or s.has_attr("defer"))
    ]
    n_block = len(blocking)
    js_score = 35.0 if n_block == 0 else 25.0 if n_block <= 2 else 15.0 if n_block <= 5 else 5.0
    findings.append(f"INP/LCP: {n_block} script(s) bloqueantes en <head> (sin async/defer).")

    # LCP proxy (15): lazy-loading and/or modern image formats present.
    lazy = any(img.get("loading") == "lazy" for img in imgs)
    modern = any(re.search(r"\.(webp|avif)(\?|$)", (img.get("src") or ""), re.I) for img in imgs)
    lcp_score = 15.0 if (lazy or modern) else 8.0
    if lazy or modern:
        findings.append("LCP: se detecta lazy-loading y/o formatos modernos (WebP/AVIF).")

    # CDN (10): from the detected stack (SKILL Category 8 CDN signal).
    cdn_score = 10.0 if stack.behind_cdn else 5.0
    if stack.behind_cdn:
        findings.append("CDN detectado en el stack.")

    findings.append(
        "Estimación estática (sin datos de campo CrUX/Lighthouse); el número autoritativo "
        "(LCP/INP/CLS) lo da performance.py."
    )
    return _dim("cwv_static_estimate", cls_score + js_score + lcp_score + cdn_score, findings)


# --------------------------------------------------------------------------- #
# 6. Mobile (15%) — SKILL Category 5 (viewport is the reliable static signal)
# --------------------------------------------------------------------------- #
def _score_mobile(soup: BeautifulSoup | None) -> WeightedDimension:
    if soup is None:
        return _dim("mobile", 0.0, ["Sin HTML servido: optimización móvil no evaluable."])

    findings: list[str] = []
    viewport = soup.find("meta", attrs={"name": re.compile(r"^viewport$", re.I)})
    content = (viewport.get("content", "") if viewport else "").lower()

    if not viewport:
        findings.append("Sin meta viewport: no optimizada para móvil (Google indexa mobile-first desde julio 2024).")
        score = 0.0
    elif "width=device-width" in content:
        score = 100.0
        findings.append("Meta viewport responsive (width=device-width) presente.")
        if "user-scalable=no" in content or "maximum-scale=1" in content.replace(" ", ""):
            findings.append("Aviso de accesibilidad: el viewport bloquea el zoom (user-scalable=no / maximum-scale=1).")
    else:
        score = 30.0
        findings.append(f"Meta viewport presente pero no responsive (content={content!r}).")

    findings.append(
        "Estimación estática: tap targets, tamaños de fuente y layout responsive requieren "
        "render real; se usa el meta viewport como señal fiable."
    )
    return _dim("mobile", score, findings)


# --------------------------------------------------------------------------- #
# 7. URL structure (5%) — SKILL Category 4
# --------------------------------------------------------------------------- #
def _score_url_structure(fetch: FetchResult) -> WeightedDimension:
    target = fetch.final_url or fetch.domain or ""
    if not target:
        return _dim("url_structure", 0.0, ["Sin URL para evaluar."])
    if "//" not in target:
        target = "https://" + target
    parsed = urlparse(target)
    path = parsed.path or "/"
    query = parsed.query or ""

    findings: list[str] = []
    score = 0.0

    if path == path.lower():
        score += 25.0
    else:
        findings.append("URL con mayúsculas en el path (preferible minúsculas).")

    if "_" not in path:
        score += 25.0
    else:
        findings.append("URL usa guiones bajos; se recomiendan guiones medios como separador.")

    if not re.search(r"(?:^|&)(session|sid|sessionid|phpsessid|jsessionid|id)=", query, re.I):
        score += 25.0
    else:
        findings.append("Query con parámetros de sesión/ID que pueden generar duplicados indexables.")

    depth = len([seg for seg in path.split("/") if seg])
    if depth <= 4:
        score += 25.0
    else:
        findings.append(f"Jerarquía profunda ({depth} niveles); preferible ≤4 para presupuesto de rastreo.")

    if score == 100.0:
        findings.append("URL limpia: minúsculas, sin guiones bajos, sin IDs de sesión, jerarquía razonable.")
    findings.append("Nota: cadenas de redirección no se evalúan (FetchResult no expone el historial de saltos).")
    return _dim("url_structure", score, findings)


# --------------------------------------------------------------------------- #
# 8. HTTP status (5%)
# --------------------------------------------------------------------------- #
def _score_status(fetch: FetchResult) -> WeightedDimension:
    sc = fetch.status_code
    if fetch.reachability != Reachability.OK or sc is None:
        return _dim("status", 0.0, ["Sitio no alcanzable (sin respuesta HTTP)."])
    if 200 <= sc < 300:
        return _dim("status", 100.0, [f"HTTP {sc}: respuesta correcta."])
    if 300 <= sc < 400:
        return _dim("status", 70.0, [f"HTTP {sc}: redirección (resuelta al hacer el fetch)."])
    if 400 <= sc < 500:
        return _dim("status", 20.0, [f"HTTP {sc}: error de cliente."])
    return _dim("status", 0.0, [f"HTTP {sc}: error de servidor."])


# --------------------------------------------------------------------------- #
# Small HTML / robots helpers (pure)
# --------------------------------------------------------------------------- #
def _has_title(soup: BeautifulSoup) -> bool:
    title = soup.find("title")
    return bool(title and title.get_text(strip=True))


def _meta_name_present(soup: BeautifulSoup, name: str) -> bool:
    tag = soup.find("meta", attrs={"name": re.compile(rf"^{re.escape(name)}$", re.I)})
    return bool(tag and (tag.get("content") or "").strip())


def _find_canonical(soup: BeautifulSoup) -> str | None:
    for link in soup.find_all("link", href=True):
        rel = link.get("rel")
        rels = rel if isinstance(rel, list) else [rel] if rel else []
        if any(str(r).lower() == "canonical" for r in rels):
            return link.get("href")
    return None


def _base_netloc(fetch: FetchResult) -> str:
    target = fetch.final_url or fetch.domain or ""
    if "//" not in target:
        target = "https://" + target
    return urlparse(target).netloc.lower()


def _count_internal_links(soup: BeautifulSoup, fetch: FetchResult) -> int:
    base = _base_netloc(fetch)
    count = 0
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href or href.startswith("#"):
            continue
        if href.lower().startswith(("mailto:", "tel:", "javascript:")):
            continue
        parsed = urlparse(href)
        if not parsed.netloc:  # relative link -> same site
            count += 1
        elif parsed.netloc.lower() == base:
            count += 1
    return count


def _stack_names(stack: TechStackResult) -> set[str]:
    names = {t.name.lower() for t in stack.technologies}
    if stack.cms:
        names.add(stack.cms.lower())
    return names


def _robots_signals(robots_txt: str) -> dict:
    """Light static parse of robots.txt for the crawlability signals we score.

    Not a full RFC parser: it extracts, per user-agent, whether ``Disallow: /``
    blocks the whole site, plus whether any ``Sitemap:`` line is present. Good
    enough for "is Googlebot blocked?" and "are AI crawlers blocked?".
    """
    agents: dict[str, list[tuple[str, str]]] = {}
    sitemap_referenced = False
    current: list[tuple[str, str]] | None = None

    for raw_line in robots_txt.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key == "user-agent":
            current = agents.setdefault(value.lower(), [])
        elif key in ("disallow", "allow") and current is not None:
            current.append((key, value))
        elif key == "sitemap":
            sitemap_referenced = True

    def blocks_root(agent: str) -> bool:
        return any(d == "disallow" and p == "/" for d, p in agents.get(agent, []))

    wildcard_block = blocks_root("*")

    def is_blocked(agent: str) -> bool:
        if blocks_root(agent):
            return True
        # Wildcard Disallow: / blocks agents that have no explicit section.
        return wildcard_block and agent not in agents

    googlebot_blocked = is_blocked("googlebot")
    ai_blocked = {agent for agent in _AI_AGENTS if is_blocked(agent)}
    return {
        "googlebot_blocked": googlebot_blocked,
        "ai_blocked": ai_blocked,
        "sitemap_referenced": sitemap_referenced,
    }
