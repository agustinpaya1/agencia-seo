// Pure label/format helpers for the audit report view — no JSX, no I/O (same
// rule as lead-status.ts). Mirrors the Spanish labels the backend markdown
// export uses (services/report.py) so both renderings read the same.

import type { BadgeTone } from "@/features/ui";

/** Human label per category name (Gate 2 uses "schema", collections "schema_org"). */
export const CATEGORY_LABELS: Record<string, string> = {
  technical: "SEO técnico",
  citability: "Citabilidad IA",
  performance: "Rendimiento (Core Web Vitals)",
  schema: "Datos estructurados (Schema.org)",
  schema_org: "Datos estructurados (Schema.org)",
  security: "Seguridad",
};

export function categoryLabel(name: string): string {
  return CATEGORY_LABELS[name] ?? name;
}

export interface TierMeta {
  label: string;
  tone: BadgeTone;
}

/** Tier band label + badge tone (bands from audit_engine ScoreTier). */
export const TIER_META: Record<string, TierMeta> = {
  excellent: { label: "Excelente", tone: "success" },
  good: { label: "Bueno", tone: "success" },
  fair: { label: "Aceptable", tone: "brand" },
  poor: { label: "Pobre", tone: "warning" },
  critical: { label: "Crítico", tone: "danger" },
};

export function tierMeta(tier?: string | null): TierMeta {
  if (!tier) return { label: "—", tone: "neutral" };
  return TIER_META[tier] ?? { label: tier, tone: "neutral" };
}

/** "35.0%" from a 0-1 weight share. */
export function formatWeight(weight?: number | null): string {
  return `${((weight ?? 0) * 100).toFixed(1)}%`;
}

/** One decimal, or "—" when the value is missing (excluded category). */
export function formatPoints(value?: number | null): string {
  if (value === null || value === undefined) return "—";
  return value.toFixed(1);
}
