"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, X } from "lucide-react";
import { Button } from "@/features/ui";
import LeadForm from "./lead-form";

/**
 * "Nuevo cliente potencial" — the only entry point to launch an audit since
 * the audit tool left the top-level nav (it is a sales hook inside the leads
 * flow, not the product). Opens the existing `LeadForm` in a lightweight modal;
 * the form and its server action are reused untouched.
 */
export default function NewLeadButton() {
  const [open, setOpen] = useState(false);
  const close = useCallback(() => setOpen(false), []);

  useEffect(() => {
    if (!open) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") close();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, close]);

  return (
    <>
      <Button size="sm" onClick={() => setOpen(true)}>
        <Plus className="h-4 w-4" />
        Nuevo cliente potencial
      </Button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center bg-foreground/40 p-4 pt-24"
          onClick={close}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Nuevo cliente potencial"
            className="w-full max-w-2xl rounded-xl border border-border bg-card p-6 shadow-lg"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="mb-2 flex justify-end">
              <Button variant="ghost" size="sm" onClick={close} aria-label="Cerrar">
                <X className="h-4 w-4" />
              </Button>
            </div>
            <LeadForm />
          </div>
        </div>
      )}
    </>
  );
}
