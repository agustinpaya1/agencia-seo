import { notFound } from "next/navigation";
import { ApiError, fetchLeadReport, isPrerenderInterrupt } from "@/lib/api-client";
import ReportView from "./report-view";
import type { LeadReport as LeadReportData } from "./types";

/**
 * Container: fetches the assembled audit report and hands it to the
 * presentational `ReportView` (same shape as lead-detail.tsx). A 400 (bad id)
 * maps to not-found; a 404 can also mean "lead exists but was never audited",
 * so it degrades to an inline explanation instead of the not-found page.
 */
export default async function LeadReport({ id }: { id: string }) {
  let report: LeadReportData;
  try {
    report = await fetchLeadReport(id);
  } catch (error) {
    if (isPrerenderInterrupt(error)) throw error;
    if (error instanceof ApiError && error.status === 400) {
      notFound();
    }
    if (error instanceof ApiError && error.status === 404) {
      return (
        <div className="mx-auto max-w-5xl rounded-xl border border-dashed border-border p-12 text-center text-sm text-muted-foreground">
          Este lead no tiene todavía ninguna auditoría terminada de la que
          generar un informe.
        </div>
      );
    }
    return (
      <div className="mx-auto max-w-5xl rounded-xl border border-danger-500/30 bg-danger-500/10 p-6 text-sm text-danger-700">
        No se pudo cargar el informe. Comprueba que el backend esté disponible.
      </div>
    );
  }

  return <ReportView report={report} />;
}
