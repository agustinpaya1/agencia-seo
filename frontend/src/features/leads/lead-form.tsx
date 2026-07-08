"use client";

import { useActionState } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/features/ui";
import { startAuditAction } from "./actions";

/**
 * Alta de lead — kicks off an audit for a lead URL. Client component so it
 * can show pending/feedback state via `useActionState`; the actual work runs in
 * the `startAuditAction` server action. Rendered inside the "Nuevo cliente
 * potencial" modal (new-lead-button.tsx), so the heading is panel-sized, not
 * the old full-page hero.
 */
export default function LeadForm() {
  const [state, formAction, isPending] = useActionState(startAuditAction, null);

  return (
    <div className="w-full max-w-2xl mx-auto text-center">
      <h2 className="text-xl font-bold tracking-tight mb-2">
        <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-700 to-brand-500">
          Nuevo cliente potencial
        </span>
      </h2>
      <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
        Introduce la URL del cliente potencial B2B para analizar su
        indexabilidad en LLMs (ChatGPT, Perplexity) y su arquitectura.
      </p>

      <form
        action={formAction}
        className="flex flex-col sm:flex-row gap-3 items-stretch"
      >
        <input
          type="url"
          name="url"
          placeholder="https://ejemplo.com"
          required
          disabled={isPending}
          className="h-11 flex-1 rounded-lg border border-input bg-card px-4 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-transparent disabled:opacity-50"
        />
        <Button type="submit" disabled={isPending}>
          {isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Iniciando análisis…
            </>
          ) : (
            "Iniciar diagnóstico"
          )}
        </Button>
      </form>

      <div className="mt-4 min-h-[24px] text-sm" aria-live="polite">
        {state?.ok === true && (
          <p className="text-success-600 font-medium">{state.message}</p>
        )}
        {state?.ok === false && (
          <p className="text-danger-600 font-medium">{state.error}</p>
        )}
      </div>
    </div>
  );
}
