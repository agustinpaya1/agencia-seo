// Pure audit-stage domain logic — no JSX, no I/O. Frontend mirror of the
// backend AuditStage enum (backend/app/audit_engine/models.py): same ids, same
// pipeline order. The four parallel submodules (technical/security/performance/
// schema_org) are ONE step on purpose — the backend reports no per-submodule
// granularity.

export interface AuditStageMeta {
  id: string;
  label: string;
  description?: string;
}

export const AUDIT_STAGES: AuditStageMeta[] = [
  {
    id: "fetch",
    label: "Descarga inicial",
    description: "HTML, cabeceras, robots.txt y sitemap",
  },
  { id: "tech_stack", label: "Detección de stack tecnológico" },
  {
    id: "technical_analysis",
    label: "Análisis técnico",
    description: "SEO técnico, seguridad, rendimiento y schema.org en paralelo",
  },
  { id: "content_analysis", label: "Keywords y citabilidad" },
  { id: "gate_1", label: "Gate 1 · viabilidad como lead" },
  { id: "gate_2", label: "Gate 2 · puntuación ponderada" },
  { id: "persistence", label: "Guardado del informe" },
];

export type StageState = "pending" | "active" | "done";

/**
 * Visual state of one stage given the lead's `current_stage` and `status`.
 *
 * - status "audit" (running): stages before the current one are done, the
 *   current one is active, the rest pending. A missing/unknown current_stage
 *   means the run just started -> first stage active.
 * - status "failed"/"unreachable": the run stopped AT current_stage, so
 *   earlier stages are done and the rest (including the current one, which
 *   never finished) stay pending.
 * - any other status: the last audit ran to the end -> everything done.
 */
export function stageState(
  stageId: string,
  currentStage: string | null | undefined,
  leadStatus: string,
): StageState {
  const stageIndex = AUDIT_STAGES.findIndex((stage) => stage.id === stageId);
  const found = AUDIT_STAGES.findIndex((stage) => stage.id === currentStage);
  const currentIndex = found >= 0 ? found : 0;

  if (leadStatus === "audit") {
    if (stageIndex < currentIndex) return "done";
    if (stageIndex === currentIndex) return "active";
    return "pending";
  }

  if (leadStatus === "failed" || leadStatus === "unreachable") {
    return stageIndex < currentIndex ? "done" : "pending";
  }

  return "done";
}
