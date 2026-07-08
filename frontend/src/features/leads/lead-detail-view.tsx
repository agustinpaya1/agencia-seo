import Link from "next/link";
import { ArrowLeft, Download, FileSearch, FileText } from "lucide-react";
import {
  Badge,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  buttonClasses,
} from "@/features/ui";
import { leadPdfUrl } from "@/lib/api-client";
import type { LeadDetail } from "./types";
import { formatDate, formatScore, getStatusMeta } from "./lead-status";
import AuditProgress from "./audit-progress";
import AuditTimeline from "./audit-timeline";
import LogoForm from "./logo-form";
import NoteForm from "./note-form";
import StatusSelect from "./status-select";
import RelaunchAuditButton from "./relaunch-audit-button";

/**
 * Presentational lead detail sheet. Receives a fully-formed `LeadDetail` and
 * lays it out; the interactive bits (status change, note, re-run) are delegated
 * to small client components. No fetching, no business logic beyond the pure
 * helpers in lead-status.ts.
 */
export default function LeadDetailView({ lead }: { lead: LeadDetail }) {
  const status = getStatusMeta(lead.status);
  const score = formatScore(lead.geo_score);
  const notes = [...(lead.notes ?? [])].reverse();
  const findings = lead.manual_findings ?? [];
  const isAuditing = lead.status === "audit";
  // A lead that was never audited (fresh CRM entry) has no timeline to show.
  const hasAuditHistory = Boolean(
    lead.last_audit_id || lead.audit_date || lead.current_stage,
  );

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
      <Link
        href="/tablero"
        className="inline-flex w-fit items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Volver al tablero
      </Link>

      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="truncate text-2xl font-bold text-foreground">
            {lead.company || lead.domain}
          </h1>
          <p className="text-sm text-muted-foreground">{lead.domain}</p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Badge tone={status.tone}>{status.label}</Badge>
            {lead.tier && <Badge tone="neutral">Tier: {lead.tier}</Badge>}
          </div>
        </div>
        <div className="flex size-16 shrink-0 items-center justify-center rounded-full border border-brand-600/30 bg-brand-600/10 text-2xl font-bold text-brand-600 dark:text-brand-300">
          {score}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main column: notes + findings */}
        <div className="flex flex-col gap-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Notas de seguimiento</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <NoteForm leadId={lead.id} />
              <ul className="flex flex-col gap-3">
                {notes.length === 0 && (
                  <li className="text-sm text-muted-foreground">
                    Aún no hay notas.
                  </li>
                )}
                {notes.map((note, index) => (
                  <li
                    key={`${note.date}-${index}`}
                    className="rounded-lg border border-border bg-muted/40 p-3"
                  >
                    <p className="text-sm text-foreground">{note.text}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {formatDate(note.date)}
                    </p>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          {findings.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Hallazgos manuales</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="flex flex-col gap-3">
                  {findings.map((finding, index) => (
                    <li
                      key={`${finding.date}-${index}`}
                      className="rounded-lg border border-border bg-muted/40 p-3"
                    >
                      <p className="text-sm text-foreground">{finding.text}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {formatDate(finding.date)}
                      </p>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Aside: audit progress + actions + metadata */}
        <div className="flex flex-col gap-6">
          {(isAuditing || hasAuditHistory) && (
            <Card>
              <CardHeader>
                <CardTitle>
                  {isAuditing ? "Auditoría en curso" : "Última auditoría"}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isAuditing ? (
                  <AuditProgress leadId={lead.id} initialStage={lead.current_stage} />
                ) : (
                  <AuditTimeline
                    currentStage={lead.current_stage}
                    status={lead.status}
                  />
                )}
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Acciones</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <span className="text-sm font-medium text-foreground">
                  Etapa en el tablero
                </span>
                <StatusSelect leadId={lead.id} currentStatus={lead.status} />
              </div>

              <LogoForm leadId={lead.id} currentLogoUrl={lead.logo_url} />

              <RelaunchAuditButton leadId={lead.id} domain={lead.domain} />

              {lead.last_audit_id && (
                <Link
                  href={`/leads/${lead.id}/informe`}
                  className={buttonClasses("primary", "sm")}
                >
                  <FileSearch className="h-4 w-4" />
                  Ver informe de auditoría
                </Link>
              )}

              {lead.has_pdf ? (
                <a
                  href={leadPdfUrl(lead.id)}
                  className={buttonClasses("secondary", "sm")}
                >
                  <Download className="h-4 w-4" />
                  Descargar propuesta PDF
                </a>
              ) : (
                <p className="inline-flex items-center gap-2 text-sm text-muted-foreground">
                  <FileText className="h-4 w-4" />
                  Sin propuesta PDF generada
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Datos</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="flex flex-col gap-3 text-sm">
                <MetaRow label="Valor mensual">
                  {lead.monthly_value ? `${lead.monthly_value} €` : "—"}
                </MetaRow>
                <MetaRow label="Última auditoría">
                  {formatDate(lead.audit_date) || "—"}
                </MetaRow>
                <MetaRow label="Actualizado">
                  {formatDate(lead.updated_at) || "—"}
                </MetaRow>
              </dl>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function MetaRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="font-medium text-foreground">{children}</dd>
    </div>
  );
}
