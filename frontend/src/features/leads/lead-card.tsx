import Link from "next/link";
import { Badge } from "@/features/ui";
import type { Lead } from "./types";
import { formatDate, formatScore, getStatusMeta } from "./lead-status";

/**
 * Presentational kanban card. Receives a fully-formed `Lead` and renders it —
 * no data fetching, no status logic beyond the pure helpers in lead-status.ts.
 * Links to the lead's detail sheet.
 */
export default function LeadCard({ lead }: { lead: Lead }) {
  const status = getStatusMeta(lead.status);
  const score = formatScore(lead.geo_score);

  return (
    <Link
      href={`/leads/${lead.id}`}
      className="group block rounded-xl border border-border bg-card p-4 shadow-sm transition-colors hover:border-brand-500/50 hover:bg-muted focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h4 className="truncate font-semibold text-card-foreground">
            {lead.company || lead.domain}
          </h4>
          <p className="truncate text-sm text-muted-foreground">{lead.domain}</p>
        </div>
        <div className="flex size-11 shrink-0 items-center justify-center rounded-full border border-brand-600/30 bg-brand-600/10 text-base font-bold text-brand-600 dark:text-brand-300">
          {score}
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between gap-2">
        <Badge tone={status.tone}>{status.label}</Badge>
        {lead.audit_date && (
          <span className="text-xs text-muted-foreground">
            {formatDate(lead.audit_date)}
          </span>
        )}
      </div>
    </Link>
  );
}
