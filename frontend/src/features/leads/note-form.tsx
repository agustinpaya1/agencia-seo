"use client";

import { useActionState, useEffect, useRef } from "react";
import { Loader2 } from "lucide-react";
import { Button, Field, Textarea } from "@/features/ui";
import { addNoteAction } from "./actions";

/** Add-note control for the detail sheet. Resets the textarea on success. */
export default function NoteForm({ leadId }: { leadId: string }) {
  const [state, formAction, isPending] = useActionState(addNoteAction, null);
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (state?.ok) formRef.current?.reset();
  }, [state]);

  return (
    <form ref={formRef} action={formAction} className="flex flex-col gap-3">
      <input type="hidden" name="leadId" value={leadId} />
      <Field
        label="Nueva nota"
        htmlFor="note-text"
        error={state?.ok === false ? state.error : undefined}
      >
        <Textarea
          id="note-text"
          name="text"
          placeholder="Escribe una nota de seguimiento…"
          required
          disabled={isPending}
        />
      </Field>
      <div className="flex items-center justify-between gap-3">
        {state?.ok ? (
          <p className="text-sm text-success-600">{state.message}</p>
        ) : (
          <span />
        )}
        <Button type="submit" size="sm" disabled={isPending}>
          {isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Guardando…
            </>
          ) : (
            "Añadir nota"
          )}
        </Button>
      </div>
    </form>
  );
}
