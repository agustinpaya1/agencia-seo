"use client";

import { useActionState } from "react";
import { Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/features/ui";
import { relaunchAuditAction } from "./actions";

/**
 * Re-run the deterministic audit for an existing lead. Sends a full URL (the
 * backend derives the domain and rejects with 409 if one is already running).
 */
export default function RelaunchAuditButton({
  leadId,
  domain,
}: {
  leadId: string;
  domain: string;
}) {
  const [state, formAction, isPending] = useActionState(relaunchAuditAction, null);

  return (
    <form action={formAction} className="flex flex-col gap-2">
      <input type="hidden" name="leadId" value={leadId} />
      <input type="hidden" name="url" value={`https://${domain}`} />
      <Button type="submit" variant="secondary" size="sm" disabled={isPending}>
        {isPending ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <RefreshCw className="w-4 h-4" />
        )}
        Relanzar auditoría
      </Button>
      {state?.ok === false && (
        <p className="text-xs text-danger-600">{state.error}</p>
      )}
      {state?.ok && <p className="text-xs text-success-600">{state.message}</p>}
    </form>
  );
}
