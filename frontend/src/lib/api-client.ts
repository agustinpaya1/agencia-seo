/**
 * Single source of truth for talking to the FastAPI backend.
 *
 * The base URL is read from `NEXT_PUBLIC_API_URL` (falling back to the local
 * dev backend) so it is never hardcoded at the call sites and is reachable from
 * both server components / server actions AND the browser — the latter matters
 * for the PDF download link, which is a plain <a href> the browser follows
 * directly (see `leadPdfUrl`).
 *
 * These helpers are intentionally thin: server components call the `fetch*`
 * readers, server actions call the `*Request` mutators, and both share one
 * request builder. No caching is applied — the CRM must always render fresh
 * data (Next.js 16 `cacheComponents` treats uncached fetches as dynamic and
 * streams them inside <Suspense>). Freshness after a mutation is handled by
 * `revalidatePath` in the server actions, not here.
 */
import type { LeadDetail, LeadReport, LeadsResponse } from "@/features/leads/types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

/** Build an absolute backend URL from a path like `/api/leads`. */
export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

/** Browser-followable URL for a lead's pre-generated proposal PDF. */
export function leadPdfUrl(leadId: string): string {
  return apiUrl(`/api/leads/${leadId}/pdf`);
}

/** Browser-followable download URL for the audit report as Markdown. */
export function leadReportMarkdownUrl(leadId: string): string {
  return apiUrl(`/api/leads/${leadId}/report.md`);
}

class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Headers must be a plain object: spreading a `Headers` instance or a tuple
 * array into the merge below would silently drop every entry.
 */
type JsonRequestInit = Omit<RequestInit, "headers"> & {
  headers?: Record<string, string>;
};

export async function request<T>(path: string, init?: JsonRequestInit): Promise<T> {
  const res = await fetch(apiUrl(path), {
    // `...init` goes first so `cache` and the headers merge below always win.
    ...init,
    // The CRM changes constantly; never serve a stale list/detail from cache.
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...init?.headers },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body?.detail ?? detail;
    } catch {
      // response had no JSON body; keep the status text
    }
    throw new ApiError(detail, res.status);
  }

  return res.json() as Promise<T>;
}

// --- Readers (server components) -------------------------------------------

export interface ListLeadsParams {
  status?: string;
  sort?: "score" | "company" | "mrr";
}

export function fetchLeads(params: ListLeadsParams = {}): Promise<LeadsResponse> {
  const query = new URLSearchParams();
  if (params.status) query.set("status", params.status);
  if (params.sort) query.set("sort", params.sort);
  const qs = query.toString();
  return request<LeadsResponse>(`/api/leads${qs ? `?${qs}` : ""}`);
}

export function fetchLeadDetail(leadId: string): Promise<LeadDetail> {
  return request<LeadDetail>(`/api/leads/${leadId}`);
}

export function fetchLeadReport(leadId: string): Promise<LeadReport> {
  return request<LeadReport>(`/api/leads/${leadId}/report`);
}

// --- Mutators (server actions) ---------------------------------------------

export function startAuditRequest(url: string): Promise<unknown> {
  return request("/api/audit", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export function addLeadNoteRequest(leadId: string, text: string): Promise<unknown> {
  return request(`/api/leads/${leadId}/note`, {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export function updateLeadStatusRequest(
  leadId: string,
  status: string,
): Promise<unknown> {
  return request(`/api/leads/${leadId}/status`, {
    method: "PUT",
    body: JSON.stringify({ status }),
  });
}

export function updateLeadLogoRequest(
  leadId: string,
  logoUrl: string,
): Promise<unknown> {
  return request(`/api/leads/${leadId}/logo`, {
    method: "PUT",
    body: JSON.stringify({ logo_url: logoUrl }),
  });
}

export { ApiError };

/**
 * Next.js throws internal control-flow errors while prerendering the static
 * shell (a fetch that hasn't resolved yet). These must bubble up untouched —
 * swallowing them breaks the build. Genuine runtime failures (backend down)
 * do not match this and can be handled as normal errors by the caller.
 */
export function isPrerenderInterrupt(error: unknown): boolean {
  return (
    (error instanceof Error &&
      error.message.includes("During prerendering, fetch() rejects")) ||
    (typeof error === "object" &&
      error !== null &&
      "digest" in error &&
      (error as { digest?: string }).digest === "HANGING_PROMISE_REJECTION")
  );
}
