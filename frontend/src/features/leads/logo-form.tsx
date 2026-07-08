"use client";

import { useActionState } from "react";
import { Loader2 } from "lucide-react";
import { Button, Field, Input } from "@/features/ui";
import { updateLogoAction } from "./actions";

/**
 * Paste-a-URL logo editor for the detail sheet. "Editable image" is exactly
 * this for now — a text field persisted as `logo_url`, no file upload. An
 * empty value clears the logo back to the initials placeholder.
 */
export default function LogoForm({
  leadId,
  currentLogoUrl,
}: {
  leadId: string;
  currentLogoUrl?: string | null;
}) {
  const [state, formAction, isPending] = useActionState(updateLogoAction, null);

  return (
    <form action={formAction} className="flex flex-col gap-2">
      <input type="hidden" name="leadId" value={leadId} />
      <Field
        label="Logo (URL de imagen)"
        htmlFor="logo-url"
        hint="Pega una URL http(s); vacío para volver a las iniciales."
        error={state?.ok === false ? state.error : undefined}
      >
        <div className="flex gap-2">
          <Input
            id="logo-url"
            name="logoUrl"
            type="url"
            placeholder="https://ejemplo.com/logo.png"
            defaultValue={currentLogoUrl ?? ""}
            disabled={isPending}
            className="h-9"
          />
          <Button type="submit" variant="secondary" size="sm" disabled={isPending}>
            {isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : "Guardar"}
          </Button>
        </div>
      </Field>
      {state?.ok && <p className="text-xs text-success-600">{state.message}</p>}
    </form>
  );
}
