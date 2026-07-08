import { Check } from "lucide-react";
import { cn } from "@/lib/cn";
import { AUDIT_STAGES, stageState, type StageState } from "./audit-stages";

// dot + connector + label classes per visual state, on the existing tokens:
// brand = in progress, success = completed, muted slate = pending.
const dotClasses: Record<StageState, string> = {
  done: "border-success-500 bg-success-500 text-white",
  active: "border-brand-600 bg-brand-600/10 text-brand-600 animate-pulse",
  pending: "border-border bg-muted text-muted-foreground",
};

const labelClasses: Record<StageState, string> = {
  done: "text-foreground",
  active: "text-brand-700 font-semibold",
  pending: "text-muted-foreground",
};

/**
 * Vertical stepper with the deterministic pipeline stages. Presentational and
 * pure over (currentStage, status) — the running variant with polling lives in
 * audit-progress.tsx; this same component renders the static all-done timeline
 * on finished audits (also reused by the Proyectos detail flow).
 */
export default function AuditTimeline({
  currentStage,
  status,
}: {
  currentStage?: string | null;
  status: string;
}) {
  return (
    <ol className="flex flex-col">
      {AUDIT_STAGES.map((stage, index) => {
        const state = stageState(stage.id, currentStage, status);
        const isLast = index === AUDIT_STAGES.length - 1;
        return (
          <li key={stage.id} className="flex gap-3" data-stage={stage.id} data-state={state}>
            <div className="flex flex-col items-center">
              <span
                className={cn(
                  "flex size-6 shrink-0 items-center justify-center rounded-full border-2",
                  dotClasses[state],
                )}
              >
                {state === "done" ? (
                  <Check className="h-3.5 w-3.5" />
                ) : (
                  <span
                    className={cn(
                      "size-1.5 rounded-full",
                      state === "active" ? "bg-brand-600" : "bg-muted-foreground/40",
                    )}
                  />
                )}
              </span>
              {!isLast && (
                <span
                  className={cn(
                    "w-px flex-1 min-h-4",
                    state === "done" ? "bg-success-400" : "bg-border",
                  )}
                />
              )}
            </div>
            <div className={cn("pb-4", isLast && "pb-0")}>
              <p className={cn("text-sm leading-6", labelClasses[state])}>
                {stage.label}
              </p>
              {stage.description && (
                <p className="text-xs text-muted-foreground">{stage.description}</p>
              )}
              {state === "active" && (
                <p className="text-xs font-medium text-brand-600">En curso…</p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
