"""Read-only assembly of one audit into a render-ready report.

The persistence layer (services/persistence.py) fans one audit out over the
light ``audit_runs`` document plus one document per scored category in the
``audit_reports_*`` collections. This module does the inverse, read-only walk:
lead -> ``last_audit_id`` -> run -> its ``reports`` map -> category documents,
and assembles everything into one plain-JSON dict the frontend renders
directly (``assemble_report``). The same dict feeds ``report_markdown``, the
guaranteed "Descargar como Markdown" fallback — one source structure, two
serialisations, no second assembly path to drift.

Same layering rule as the rest of ``services/``: the pure builders
(``assemble_report``, ``report_markdown``) never touch Mongo; the async shell
(``load_audit_report``) only fetches documents and delegates.
"""

from __future__ import annotations

from datetime import datetime

from bson import ObjectId

from .persistence import AUDIT_RUNS_COLLECTION, CATEGORY_COLLECTIONS

# Human labels for the Gate 2 breakdown names (the orchestrator uses "schema"
# for the schema_org category) and for the category sections.
CATEGORY_LABELS: dict[str, str] = {
    "technical": "SEO técnico",
    "citability": "Citabilidad IA",
    "performance": "Rendimiento (Core Web Vitals)",
    "schema": "Datos estructurados (Schema.org)",
    "schema_org": "Datos estructurados (Schema.org)",
    "security": "Seguridad",
}

TIER_LABELS: dict[str, str] = {
    "excellent": "Excelente (90-100)",
    "good": "Bueno (75-89)",
    "fair": "Aceptable (60-74)",
    "poor": "Pobre (40-59)",
    "critical": "Crítico (0-39)",
}


# --------------------------------------------------------------------------- #
# Pure helpers — JSON sanitisation + assembly, unit-testable without Mongo
# --------------------------------------------------------------------------- #
def _jsonable(value):
    """Recursively convert Mongo/BSON values to plain JSON types.

    ObjectId -> str, datetime -> ISO string; dicts/lists walked. The report is
    consumed by the frontend and by the markdown renderer, so it is normalised
    once here instead of leaning on FastAPI's encoder.
    """
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


def _category_detail(doc: dict) -> dict:
    """The renderable payload of one ``audit_reports_*`` document.

    Drops the storage-only keys (ids and the fields duplicated on the run) and
    keeps the flat ``*Result`` payload persistence stored.
    """
    return _jsonable(
        {k: v for k, v in doc.items() if k not in ("_id", "audit_id", "domain", "computed_at")}
    )


def assemble_report(lead: dict, run_doc: dict, category_docs: dict[str, dict]) -> dict:
    """Build the render-ready report dict from the stored documents.

    ``category_docs`` is keyed by category name (CATEGORY_COLLECTIONS keys);
    a category the run never produced is simply absent. Everything returned is
    plain JSON (str ids, ISO datetimes) — see ``_jsonable``.
    """
    reports = run_doc.get("reports") or {}
    categories = {}
    for name in CATEGORY_COLLECTIONS:
        entry = reports.get(name)
        if entry is None:
            continue
        doc = category_docs.get(name)
        categories[name] = {
            "score": entry.get("score"),
            "detail": _category_detail(doc) if doc else None,
        }

    return {
        "lead": {
            "id": str(lead["_id"]) if "_id" in lead else lead.get("id"),
            "company": lead.get("company"),
            "domain": lead.get("domain"),
            "status": lead.get("status"),
        },
        "audit": {
            "id": str(run_doc["_id"]),
            "domain": run_doc.get("domain"),
            "created_at": _jsonable(run_doc.get("created_at")),
            "reachability": run_doc.get("reachability"),
            "errors": run_doc.get("errors") or [],
        },
        "score": _jsonable(run_doc.get("weighted_score")),
        "viability": _jsonable(run_doc.get("lead_viability")),
        "categories": categories,
        "keywords": _jsonable(run_doc.get("keywords")),
        "tech_stack": _jsonable(run_doc.get("tech_stack")),
    }


# --------------------------------------------------------------------------- #
# Markdown rendering — pure over the assembled report
# --------------------------------------------------------------------------- #
def _md_score(value) -> str:
    if value is None:
        return "—"
    return f"{float(value):.1f}"


def _breakdown_table(breakdown: list[dict]) -> list[str]:
    lines = [
        "| Categoría | Score | Peso | Puntos |",
        "| --- | ---: | ---: | ---: |",
    ]
    for dim in breakdown:
        label = CATEGORY_LABELS.get(dim.get("name", ""), dim.get("name", ""))
        weight = dim.get("weight") or 0.0
        lines.append(
            f"| {label} | {_md_score(dim.get('score'))} | {weight * 100:.1f}% "
            f"| {_md_score(dim.get('points'))} |"
        )
    return lines


def _technical_section(detail: dict) -> list[str]:
    lines = []
    dims = detail.get("dimensions") or []
    if dims:
        lines += ["| Dimensión | Score | Peso | Puntos |", "| --- | ---: | ---: | ---: |"]
        for dim in dims:
            weight = dim.get("weight") or 0.0
            lines.append(
                f"| {dim.get('name', '')} | {_md_score(dim.get('score'))} "
                f"| {weight * 100:.0f}% | {_md_score(dim.get('points'))} |"
            )
        lines.append("")
    for dim in dims:
        for finding in dim.get("findings") or []:
            lines.append(f"- **{dim.get('name', '')}**: {finding}")
    return lines


def _security_section(detail: dict) -> list[str]:
    lines = []
    headers = detail.get("headers") or {}
    present = [name for name, ok in headers.items() if ok]
    missing = [name for name, ok in headers.items() if not ok]
    lines.append(f"- Cabeceras presentes: {', '.join(present) if present else 'ninguna'}")
    lines.append(f"- Cabeceras ausentes: {', '.join(missing) if missing else 'ninguna'}")
    if detail.get("observatory_grade"):
        lines.append(
            f"- MDN Observatory: {detail['observatory_grade']}"
            f" ({detail.get('observatory_score', '—')})"
        )
    vulns = detail.get("vulnerabilities") or []
    if vulns:
        lines.append("- Vulnerabilidades conocidas sin parchear:")
        for vuln in vulns:
            lines.append(
                f"  - {vuln.get('cve_id')} ({vuln.get('severity')}) — "
                f"{vuln.get('product')} {vuln.get('affected_version') or ''}".rstrip()
            )
    for note in detail.get("notes") or []:
        lines.append(f"- {note}")
    return lines


def _performance_section(detail: dict) -> list[str]:
    lines = []
    metrics = (
        ("LCP", detail.get("lcp_ms"), "ms", detail.get("lcp_source")),
        ("INP", detail.get("inp_ms"), "ms", detail.get("inp_source")),
        ("CLS", detail.get("cls"), "", detail.get("cls_source")),
    )
    for label, value, unit, source in metrics:
        if value is None:
            lines.append(f"- {label}: sin datos")
        else:
            origin = f" (fuente: {source})" if source else ""
            lines.append(f"- {label}: {value:g} {unit}".rstrip() + origin)
    lines.append(f"- Origen global de los datos: {detail.get('source', '—')}")
    for note in detail.get("notes") or []:
        lines.append(f"- {note}")
    return lines


def _schema_section(detail: dict) -> list[str]:
    lines = [
        f"- Formato: {detail.get('format', 'none')}",
        f"- Tipos detectados: {', '.join(detail.get('detected_types') or []) or 'ninguno'}",
        f"- JSON-LD válido: {'sí' if detail.get('json_ld_valid') else 'no'}",
        f"- Renderizado en servidor: {'sí' if detail.get('server_rendered') else 'no'}",
    ]
    checks = detail.get("checks") or []
    if checks:
        lines += ["", "| Validación | Puntos |", "| --- | ---: |"]
        for check in checks:
            lines.append(
                f"| {check.get('label', check.get('id', ''))} "
                f"| {_md_score(check.get('points'))}/{_md_score(check.get('max_points'))} |"
            )
    return lines


def _citability_section(detail: dict) -> list[str]:
    lines = [
        f"- Bloques analizados: {detail.get('blocks_analyzed', 0)}",
        f"- Pasajes con longitud óptima: {detail.get('optimal_length_passages', 0)}",
    ]
    distribution = detail.get("grade_distribution") or {}
    if distribution:
        dist = ", ".join(f"{grade}: {count}" for grade, count in distribution.items())
        lines.append(f"- Distribución de notas: {dist}")
    for note in detail.get("notes") or []:
        lines.append(f"- {note}")
    return lines


_CATEGORY_RENDERERS = {
    "technical": _technical_section,
    "security": _security_section,
    "performance": _performance_section,
    "schema_org": _schema_section,
    "citability": _citability_section,
}


def report_markdown(report: dict) -> str:
    """Render the assembled report as Markdown (the guaranteed export path)."""
    lead = report.get("lead") or {}
    audit = report.get("audit") or {}
    title = lead.get("company") or audit.get("domain") or ""
    created = (audit.get("created_at") or "")[:10]

    lines: list[str] = [
        f"# Informe de auditoría GEO — {title}",
        "",
        f"- **Dominio:** {audit.get('domain', '—')}",
        f"- **Fecha de auditoría:** {created or '—'}",
        f"- **Auditoría:** `{audit.get('id', '—')}`",
        "",
    ]

    score = report.get("score")
    if score:
        tier = score.get("tier") or ""
        lines += [
            "## Puntuación global",
            "",
            f"**{_md_score(score.get('final_score'))} / 100** — tier "
            f"**{TIER_LABELS.get(tier, tier)}**",
            "",
            *_breakdown_table(score.get("breakdown") or []),
            "",
        ]
        for dim in score.get("breakdown") or []:
            for finding in dim.get("findings") or []:
                label = CATEGORY_LABELS.get(dim.get("name", ""), dim.get("name", ""))
                lines.append(f"- **{label}**: {finding}")
        lines.append("")

    viability = report.get("viability")
    if viability:
        verdict = "Sí, es lead" if viability.get("is_lead") else "No es lead"
        lines += [
            "## Viabilidad como lead (Gate 1)",
            "",
            f"**{verdict}** — {viability.get('reason', '')}",
            "",
        ]
        checked = viability.get("checked_dimensions") or {}
        for name, value in checked.items():
            label = CATEGORY_LABELS.get(name, name)
            lines.append(f"- {label}: {_md_score(value)}")
        if checked:
            lines.append("")

    categories = report.get("categories") or {}
    if categories:
        lines += ["## Detalle por categoría", ""]
        for name in CATEGORY_COLLECTIONS:
            category = categories.get(name)
            if not category:
                continue
            label = CATEGORY_LABELS.get(name, name)
            lines.append(f"### {label} — {_md_score(category.get('score'))}/100")
            lines.append("")
            detail = category.get("detail")
            if detail:
                lines += _CATEGORY_RENDERERS[name](detail)
            lines.append("")

    keywords = report.get("keywords")
    suggestions = (keywords or {}).get("suggestions") or []
    if suggestions:
        lines += ["## Búsquedas sugeridas", ""]
        for suggestion in suggestions:
            lines.append(f"- {suggestion.get('query')} _(fuente: {suggestion.get('source')})_")
        lines.append("")

    tech_stack = report.get("tech_stack")
    technologies = (tech_stack or {}).get("technologies") or []
    if technologies:
        lines += ["## Stack tecnológico detectado", ""]
        for tech in technologies:
            version = f" {tech.get('version')}" if tech.get("version") else ""
            lines.append(f"- {tech.get('name')}{version} ({tech.get('confidence')})")
        lines.append("")

    errors = audit.get("errors") or []
    if errors:
        lines += ["## Incidencias del motor", ""]
        for error in errors:
            lines.append(f"- {error}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# --------------------------------------------------------------------------- #
# Async shell — Mongo reads only, assembly delegated to the pure builder
# --------------------------------------------------------------------------- #
async def load_audit_report(db, lead: dict) -> dict | None:
    """Load and assemble the report for a lead's last audit.

    Returns ``None`` when the lead has no ``last_audit_id`` or the referenced
    run no longer exists (the endpoint turns both into a 404: there is no
    report to show). Missing category documents (harmless orphans aside, they
    should always exist) degrade to ``detail: None`` instead of failing.
    """
    last_audit_id = lead.get("last_audit_id")
    if not last_audit_id:
        return None
    try:
        run_id = ObjectId(last_audit_id)
    except Exception:
        return None

    run_doc = await db[AUDIT_RUNS_COLLECTION].find_one({"_id": run_id})
    if run_doc is None:
        return None

    category_docs: dict[str, dict] = {}
    for name, collection_name in CATEGORY_COLLECTIONS.items():
        entry = (run_doc.get("reports") or {}).get(name)
        if entry is None:
            continue
        doc = await db[collection_name].find_one({"_id": entry["id"]})
        if doc is not None:
            category_docs[name] = doc

    return assemble_report(lead, run_doc, category_docs)
