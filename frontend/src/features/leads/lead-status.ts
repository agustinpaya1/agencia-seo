// Pure lead-status domain logic — no JSX, no I/O. Everything the UI needs to
// know about "what a status means" lives here so presentation components stay
// dumb (task: no business logic inside JSX). Reused by the kanban board, the
// status badge and the status <select>.

import type { BadgeTone } from "@/features/ui";
import type { Lead } from "./types";

export interface StatusMeta {
  /** Human label shown in Spanish on badges and column headers. */
  label: string;
  /** Which Badge tone paints this status. */
  tone: BadgeTone;
}

// The full status vocabulary. The first seven mirror the backend whitelist
// (models/leads.py::EDITABLE_STATUSES, enforced by parse_editable_status);
// `unreachable` and `failed` are set by the audit engine and are NOT
// user-assignable (see EDITABLE_STATUSES below).
export const STATUS_META: Record<string, StatusMeta> = {
  lead: { label: "Cliente potencial", tone: "neutral" },
  audit: { label: "Auditando", tone: "warning" },
  proposal: { label: "Propuesta", tone: "brand" },
  active: { label: "Cliente activo", tone: "success" },
  // `completed` shares the success tone with `active` on purpose: both are
  // positive outcomes, and the reduced palette (brand blue + neutrals + three
  // muted status colours) overloads tones instead of adding hues.
  completed: { label: "Completado", tone: "success" },
  churned: { label: "Baja", tone: "danger" },
  lost: { label: "Perdido", tone: "neutral" },
  unreachable: { label: "No accesible", tone: "warning" },
  failed: { label: "Fallo auditoría", tone: "danger" },
};

// Canonical left-to-right order of the board funnel plus terminal states.
const STATUS_ORDER: string[] = [
  "lead",
  "audit",
  "proposal",
  "active",
  "completed",
  "churned",
  "lost",
  "unreachable",
  "failed",
];

// Columns always shown even when empty, so the funnel shape is visible on a
// fresh CRM. Terminal states only get a column when they actually hold leads.
const CORE_PIPELINE: string[] = ["lead", "audit", "proposal", "active"];

// Statuses a user may assign by hand — exactly the backend whitelist
// (models/leads.py::EDITABLE_STATUSES). A value outside this set
// (unreachable/failed) would 400 on the API, so the kanban only accepts drops
// on these columns and the detail <select> only offers these options.
export const EDITABLE_STATUSES: string[] = [
  "lead",
  "audit",
  "proposal",
  "active",
  "completed",
  "churned",
  "lost",
];

/** Metadata for any status string, with a safe fallback for unknown values. */
export function getStatusMeta(status: string): StatusMeta {
  return STATUS_META[status] ?? { label: status, tone: "neutral" };
}

/** Group leads by their status field, preserving insertion order per bucket. */
export function groupLeadsByStatus(leads: Lead[]): Map<string, Lead[]> {
  const groups = new Map<string, Lead[]>();
  for (const lead of leads) {
    const bucket = groups.get(lead.status) ?? [];
    bucket.push(lead);
    groups.set(lead.status, bucket);
  }
  return groups;
}

/**
 * Ordered list of columns to render: the core funnel always, plus any other
 * status actually present in the data (so nothing is hidden, but empty terminal
 * columns don't clutter the board).
 */
export function boardColumns(leads: Lead[]): string[] {
  const present = new Set(leads.map((lead) => lead.status));
  return STATUS_ORDER.filter(
    (status) => CORE_PIPELINE.includes(status) || present.has(status),
  );
}

const dateFormatter = new Intl.DateTimeFormat("es-ES", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

/** Format an ISO-ish date string for display; returns "" for empty/invalid. */
export function formatDate(value?: string | null): string {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return dateFormatter.format(parsed);
}

/** GEO score as a clean integer for the score ring. */
export function formatScore(score?: number | null): number {
  return Math.round(score ?? 0);
}
