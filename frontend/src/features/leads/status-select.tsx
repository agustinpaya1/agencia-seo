"use client";

import { useActionState } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/features/ui";
import { changeStatusAction } from "./actions";
import { EDITABLE_STATUSES, getStatusMeta } from "./lead-status";

/** Board-stage changer for the detail sheet. */
export default function StatusSelect({
  leadId,
  currentStatus,
}: {
  leadId: string;
  currentStatus: string;
}) {
  const [state, formAction, isPending] = useActionState(changeStatusAction, null);

  // If the current status was set by the engine (failed/unreachable) and isn't
  // user-assignable, still surface it as the selected value alongside the
  // editable options so the select tells the truth.
  const options = EDITABLE_STATUSES.includes(currentStatus)
    ? EDITABLE_STATUSES
    : [currentStatus, ...EDITABLE_STATUSES];

  return (
    <form action={formAction} className="flex flex-col gap-2">
      <input type="hidden" name="leadId" value={leadId} />
      <div className="flex gap-2">
        <select
          name="status"
          defaultValue={currentStatus}
          disabled={isPending}
          className="h-9 flex-1 rounded-lg border border-input bg-card px-3 text-sm text-foreground focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
        >
          {options.map((status) => (
            <option key={status} value={status}>
              {getStatusMeta(status).label}
            </option>
          ))}
        </select>
        <Button type="submit" variant="secondary" size="sm" disabled={isPending}>
          {isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : "Cambiar"}
        </Button>
      </div>
      {state?.ok === false && (
        <p className="text-xs text-danger-600">{state.error}</p>
      )}
      {state?.ok && <p className="text-xs text-success-600">{state.message}</p>}
    </form>
  );
}
