import { notFound } from "next/navigation";
import { ApiError, fetchLeadDetail, isPrerenderInterrupt } from "@/lib/api-client";
import LeadDetailView from "./lead-detail-view";
import type { LeadDetail as LeadDetailData } from "./types";

/**
 * Container: fetches one lead and hands it to the presentational
 * `LeadDetailView`. Uncached (dynamic) fetch, so it must render inside a
 * <Suspense> boundary (provided by app/leads/[id]/page.tsx). A missing lead
 * (400/404) maps to the Next.js not-found page; other network errors degrade to
 * an inline message.
 *
 * The fetch is isolated in try/catch and the JSX is returned afterwards — a
 * render error thrown by `LeadDetailView` must reach an error boundary, not be
 * swallowed here (see react-hooks/error-boundaries lint rule).
 */
export default async function LeadDetail({ id }: { id: string }) {
  let lead: LeadDetailData;
  try {
    lead = await fetchLeadDetail(id);
  } catch (error) {
    if (isPrerenderInterrupt(error)) throw error;
    if (error instanceof ApiError && (error.status === 404 || error.status === 400)) {
      notFound();
    }
    return (
      <div className="mx-auto max-w-5xl rounded-xl border border-danger-500/30 bg-danger-500/10 p-6 text-sm text-danger-700">
        No se pudo cargar el lead. Comprueba que el backend esté disponible.
      </div>
    );
  }

  return <LeadDetailView lead={lead} />;
}
