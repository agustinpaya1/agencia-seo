import Link from "next/link";
import { ArrowLeft, Download, FileUp } from "lucide-react";
import {
  Badge,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  buttonClasses,
} from "@/features/ui";
import { leadReportMarkdownUrl } from "@/lib/api-client";
import type { LeadReport, ReportDimension } from "./types";
import { formatDate, formatScore } from "./lead-status";
import { categoryLabel, formatPoints, formatWeight, tierMeta } from "./report-labels";

/**
 * Presentational audit report: the render of GET /api/leads/{id}/report.
 * Structured JSON in, design-system components out — no markdown renderer in
 * the frontend on purpose (the markdown lives server-side, one source for the
 * download). Same rule as lead-detail-view: no fetching, no business logic.
 */
export default function ReportView({ report }: { report: LeadReport }) {
  const tier = tierMeta(report.score?.tier);
  const categories = report.categories ?? {};

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
      <Link
        href={`/leads/${report.lead.id}`}
        className="inline-flex w-fit items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Volver al lead
      </Link>

      {/* Header: identity + weighted score + export */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="truncate text-2xl font-bold text-foreground">
            Informe de auditoría — {report.lead.company || report.audit.domain}
          </h1>
          <p className="text-sm text-muted-foreground">
            {report.audit.domain} · {formatDate(report.audit.created_at) || "—"}
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Badge tone={tier.tone}>Tier: {tier.label}</Badge>
            {report.viability && (
              <Badge tone={report.viability.is_lead ? "brand" : "neutral"}>
                {report.viability.is_lead ? "Es lead" : "No es lead"}
              </Badge>
            )}
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex size-16 shrink-0 items-center justify-center rounded-full border border-brand-600/30 bg-brand-600/10 text-2xl font-bold text-brand-600 dark:text-brand-300">
            {formatScore(report.score?.final_score)}
          </div>
          <div className="flex flex-col gap-2">
            <a
              href={leadReportMarkdownUrl(report.lead.id)}
              className={buttonClasses("secondary", "sm")}
            >
              <Download className="h-4 w-4" />
              Descargar como Markdown
            </a>
            {/* UI-only placeholder: no OAuth/Google integration behind it yet
                (pending credentials — see Tarea 2 Parte B proposal). */}
            <button
              type="button"
              disabled
              title="Próximamente — pendiente de credenciales de Google"
              className={buttonClasses("secondary", "sm")}
            >
              <FileUp className="h-4 w-4" />
              Exportar a Google Docs
            </button>
          </div>
        </div>
      </div>

      {/* Gate 2 breakdown */}
      {report.score && (
        <Card>
          <CardHeader>
            <CardTitle>Desglose ponderado (Gate 2)</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="py-2 font-medium">Categoría</th>
                  <th className="py-2 text-right font-medium">Score</th>
                  <th className="py-2 text-right font-medium">Peso</th>
                  <th className="py-2 text-right font-medium">Puntos</th>
                </tr>
              </thead>
              <tbody>
                {report.score.breakdown.map((dim) => (
                  <tr key={dim.name} className="border-b border-border/60">
                    <td className="py-2 text-foreground">{categoryLabel(dim.name)}</td>
                    <td className="py-2 text-right font-medium text-foreground">
                      {formatPoints(dim.score)}
                    </td>
                    <td className="py-2 text-right text-muted-foreground">
                      {formatWeight(dim.weight)}
                    </td>
                    <td className="py-2 text-right text-muted-foreground">
                      {formatPoints(dim.points)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <FindingsList dimensions={report.score.breakdown} />
          </CardContent>
        </Card>
      )}

      {/* Gate 1 verdict */}
      {report.viability && (
        <Card>
          <CardHeader>
            <CardTitle>Viabilidad como lead (Gate 1)</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 text-sm">
            <p className="text-foreground">{report.viability.reason}</p>
            <dl className="flex flex-wrap gap-x-8 gap-y-2">
              {Object.entries(report.viability.checked_dimensions).map(
                ([name, value]) => (
                  <div key={name} className="flex items-center gap-2">
                    <dt className="text-muted-foreground">{categoryLabel(name)}</dt>
                    <dd className="font-medium text-foreground">
                      {formatPoints(value)}
                    </dd>
                  </div>
                ),
              )}
            </dl>
          </CardContent>
        </Card>
      )}

      {/* Per-category findings */}
      <div className="grid gap-6 lg:grid-cols-2">
        {Object.entries(categories).map(([name, category]) => (
          <Card key={name}>
            <CardHeader>
              <CardTitle>
                {categoryLabel(name)}
                <span className="ml-2 text-muted-foreground">
                  {formatPoints(category.score)}/100
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CategoryDetail name={name} detail={category.detail} />
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Suggested searches + tech stack */}
      {(report.keywords?.suggestions?.length ?? 0) > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Búsquedas sugeridas</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-2 text-sm">
              {report.keywords?.suggestions?.map((suggestion) => (
                <li key={suggestion.query} className="text-foreground">
                  {suggestion.query}{" "}
                  <span className="text-muted-foreground">
                    (fuente: {suggestion.source})
                  </span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {(report.tech_stack?.technologies?.length ?? 0) > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Stack tecnológico detectado</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {report.tech_stack?.technologies?.map((tech) => (
                <Badge key={tech.name} tone="neutral">
                  {tech.name}
                  {tech.version ? ` ${tech.version}` : ""}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {report.audit.errors.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Incidencias del motor</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-2 text-sm text-muted-foreground">
              {report.audit.errors.map((error) => (
                <li key={error}>{error}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function FindingsList({ dimensions }: { dimensions: ReportDimension[] }) {
  const findings = dimensions.flatMap((dim) =>
    (dim.findings ?? []).map((finding) => ({ name: dim.name, finding })),
  );
  if (findings.length === 0) return null;
  return (
    <ul className="flex flex-col gap-1.5 text-sm text-muted-foreground">
      {findings.map(({ name, finding }) => (
        <li key={`${name}-${finding}`}>
          <span className="font-medium text-foreground">{categoryLabel(name)}:</span>{" "}
          {finding}
        </li>
      ))}
    </ul>
  );
}

// --- Per-category detail renderers ------------------------------------------
// The `detail` payloads are the flat *Result documents persisted per category
// (services/persistence.py); each renderer reads only the fields it shows and
// tolerates their absence.

function CategoryDetail({
  name,
  detail,
}: {
  name: string;
  detail: Record<string, unknown> | null;
}) {
  if (!detail) {
    return <p className="text-sm text-muted-foreground">Sin detalle almacenado.</p>;
  }
  switch (name) {
    case "technical":
      return <TechnicalDetail detail={detail} />;
    case "security":
      return <SecurityDetail detail={detail} />;
    case "performance":
      return <PerformanceDetail detail={detail} />;
    case "schema_org":
      return <SchemaDetail detail={detail} />;
    case "citability":
      return <CitabilityDetail detail={detail} />;
    default:
      return null;
  }
}

interface DetailProps {
  detail: Record<string, unknown>;
}

function NotesList({ notes }: { notes: unknown }) {
  if (!Array.isArray(notes) || notes.length === 0) return null;
  return (
    <ul className="mt-3 flex flex-col gap-1.5 text-sm text-muted-foreground">
      {notes.map((note) => (
        <li key={String(note)}>{String(note)}</li>
      ))}
    </ul>
  );
}

function TechnicalDetail({ detail }: DetailProps) {
  const dimensions = (detail.dimensions ?? []) as ReportDimension[];
  return (
    <div className="flex flex-col gap-1.5 text-sm">
      {dimensions.map((dim) => (
        <div key={dim.name}>
          <div className="flex items-center justify-between gap-4">
            <span className="text-muted-foreground">{dim.name}</span>
            <span className="font-medium text-foreground">
              {formatPoints(dim.score)}
            </span>
          </div>
          {(dim.findings ?? []).map((finding) => (
            <p key={finding} className="text-xs text-muted-foreground">
              {finding}
            </p>
          ))}
        </div>
      ))}
    </div>
  );
}

function SecurityDetail({ detail }: DetailProps) {
  const headers = (detail.headers ?? {}) as Record<string, boolean>;
  const vulnerabilities = (detail.vulnerabilities ?? []) as {
    cve_id: string;
    severity: string;
    product: string;
  }[];
  return (
    <div className="text-sm">
      <div className="flex flex-wrap gap-2">
        {Object.entries(headers).map(([header, present]) => (
          <Badge key={header} tone={present ? "success" : "danger"}>
            {header}
          </Badge>
        ))}
      </div>
      {typeof detail.observatory_grade === "string" && (
        <p className="mt-3 text-muted-foreground">
          MDN Observatory: {detail.observatory_grade}
        </p>
      )}
      {vulnerabilities.length > 0 && (
        <ul className="mt-3 flex flex-col gap-1.5">
          {vulnerabilities.map((vuln) => (
            <li key={vuln.cve_id} className="text-danger-700">
              {vuln.cve_id} ({vuln.severity}) — {vuln.product}
            </li>
          ))}
        </ul>
      )}
      <NotesList notes={detail.notes} />
    </div>
  );
}

function PerformanceDetail({ detail }: DetailProps) {
  const metrics: [string, unknown, string][] = [
    ["LCP", detail.lcp_ms, "ms"],
    ["INP", detail.inp_ms, "ms"],
    ["CLS", detail.cls, ""],
  ];
  return (
    <div className="text-sm">
      <dl className="flex flex-col gap-2">
        {metrics.map(([label, value, unit]) => (
          <div key={label} className="flex items-center justify-between gap-4">
            <dt className="text-muted-foreground">{label}</dt>
            <dd className="font-medium text-foreground">
              {typeof value === "number" ? `${value} ${unit}`.trim() : "sin datos"}
            </dd>
          </div>
        ))}
        <div className="flex items-center justify-between gap-4">
          <dt className="text-muted-foreground">Origen de los datos</dt>
          <dd className="font-medium text-foreground">{String(detail.source ?? "—")}</dd>
        </div>
      </dl>
      <NotesList notes={detail.notes} />
    </div>
  );
}

function SchemaDetail({ detail }: DetailProps) {
  const types = (detail.detected_types ?? []) as string[];
  const checks = (detail.checks ?? []) as {
    id: string;
    label: string;
    points: number;
    max_points: number;
  }[];
  return (
    <div className="text-sm">
      <p className="text-muted-foreground">
        Formato: <span className="font-medium text-foreground">{String(detail.format ?? "none")}</span>
        {types.length > 0 && <> · Tipos: {types.join(", ")}</>}
      </p>
      {checks.length > 0 && (
        <ul className="mt-3 flex flex-col gap-1.5">
          {checks.map((check) => (
            <li key={check.id} className="flex items-center justify-between gap-4">
              <span className="text-muted-foreground">{check.label}</span>
              <span className="font-medium text-foreground">
                {formatPoints(check.points)}/{formatPoints(check.max_points)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function CitabilityDetail({ detail }: DetailProps) {
  const distribution = (detail.grade_distribution ?? {}) as Record<string, number>;
  return (
    <div className="text-sm">
      <dl className="flex flex-col gap-2">
        <div className="flex items-center justify-between gap-4">
          <dt className="text-muted-foreground">Bloques analizados</dt>
          <dd className="font-medium text-foreground">
            {String(detail.blocks_analyzed ?? 0)}
          </dd>
        </div>
        <div className="flex items-center justify-between gap-4">
          <dt className="text-muted-foreground">Pasajes con longitud óptima</dt>
          <dd className="font-medium text-foreground">
            {String(detail.optimal_length_passages ?? 0)}
          </dd>
        </div>
      </dl>
      {Object.keys(distribution).length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {Object.entries(distribution).map(([grade, count]) => (
            <Badge key={grade} tone="neutral">
              {grade}: {count}
            </Badge>
          ))}
        </div>
      )}
      <NotesList notes={detail.notes} />
    </div>
  );
}
