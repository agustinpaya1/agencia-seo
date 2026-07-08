// Frontend mirror of the backend lead contract (backend/app/models/leads.py and
// the leads endpoints). Only the fields the UI reads are typed; the raw audit
// document carries more that we ignore here.

export interface LeadNote {
  date: string;
  text: string;
}

export interface ManualFinding {
  date: string;
  text: string;
}

/** Shape returned by GET /api/leads (list) — enough to render a board card. */
export interface Lead {
  id: string;
  company: string;
  domain: string;
  status: string;
  geo_score: number;
  monthly_value?: number;
  tier?: string | null;
  audit_date?: string | null;
  updated_at?: string | null;
  /** Last stage reported by a background audit (see audit-stages.ts). */
  current_stage?: string | null;
  /** Pasted image URL for the media card; empty/absent -> initials placeholder. */
  logo_url?: string | null;
}

/** CRM aggregates from GET /api/leads (see services/core.py::crm_stats). */
export interface LeadStats {
  total: number;
  active: number;
  mrr: number;
  pipeline: number;
  avg_score: number;
  avg_tier: string;
}

export interface LeadsResponse {
  leads: Lead[];
  stats: LeadStats;
}

/** Shape returned by GET /api/leads/{id} (detail) — the full document. */
export interface LeadDetail extends Lead {
  notes?: LeadNote[];
  manual_findings?: ManualFinding[];
  has_pdf: boolean;
  is_lead?: boolean | null;
  reachability?: string | null;
  last_audit_id?: string | null;
}

// --- Audit report (GET /api/leads/{id}/report) ------------------------------
// Mirror of services/report.py::assemble_report. Category `detail` payloads are
// the flat *Result documents; only the fields the report view reads are typed.

/** One weighted dimension (Gate 2 breakdown or a technical sub-dimension). */
export interface ReportDimension {
  name: string;
  score: number;
  weight: number;
  points: number;
  findings: string[];
}

export interface ReportCategory {
  score: number | null;
  detail: Record<string, unknown> | null;
}

export interface LeadReport {
  lead: {
    id: string;
    company?: string | null;
    domain?: string | null;
    status?: string | null;
  };
  audit: {
    id: string;
    domain?: string | null;
    created_at?: string | null;
    reachability?: string | null;
    errors: string[];
  };
  score: {
    final_score: number;
    tier: string;
    breakdown: ReportDimension[];
  } | null;
  viability: {
    is_lead: boolean;
    reason: string;
    checked_dimensions: Record<string, number>;
  } | null;
  categories: Record<string, ReportCategory>;
  keywords: {
    suggestions?: { query: string; source: string }[];
  } | null;
  tech_stack: {
    technologies?: { name: string; version?: string | null; confidence?: string }[];
  } | null;
}

/**
 * Return value of the leads server actions, consumed by `useActionState` in the
 * client forms. Defined here (not in actions.ts) because a `"use server"` module
 * may only export async functions, not types.
 */
export type ActionState =
  | { ok: true; message: string }
  | { ok: false; error: string }
  | null;
