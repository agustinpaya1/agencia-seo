"use server";

import { revalidatePath } from "next/cache";
import {
  addLeadNoteRequest,
  ApiError,
  startAuditRequest,
  updateLeadLogoRequest,
  updateLeadStatusRequest,
} from "@/lib/api-client";
import type { ActionState } from "./types";

// Routes that render lead lists (board + projects); revalidated after any
// mutation that can change them so the UI reflects the write immediately
// (read-your-own-writes). Data itself is uncached (see api-client), so
// revalidating the path is what busts the client router cache and forces a
// fresh server render.
const LIST_ROUTES = ["/", "/tablero", "/proyectos"];

function toErrorState(error: unknown, fallback: string): ActionState {
  if (error instanceof ApiError) {
    return { ok: false, error: error.message };
  }
  return { ok: false, error: fallback };
}

/**
 * Alta de lead: kicks off an audit for a URL (ported from the old
 * audit/search-form flow). Used by `lead-form.tsx` via `useActionState`.
 */
export async function startAuditAction(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const url = String(formData.get("url") ?? "").trim();
  if (!url) {
    return { ok: false, error: "La URL es obligatoria." };
  }

  try {
    await startAuditRequest(url);
  } catch (error) {
    return toErrorState(error, "No se pudo contactar con el motor de auditoría.");
  }

  LIST_ROUTES.forEach((route) => revalidatePath(route));
  return { ok: true, message: "Auditoría iniciada correctamente." };
}

/**
 * Re-run the audit for an existing lead from its detail sheet. The backend
 * returns 409 if one is already in flight for the domain, surfaced as an error.
 */
export async function relaunchAuditAction(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const url = String(formData.get("url") ?? "").trim();
  const leadId = String(formData.get("leadId") ?? "").trim();
  if (!url) {
    return { ok: false, error: "Falta el dominio del lead." };
  }

  try {
    await startAuditRequest(url);
  } catch (error) {
    return toErrorState(error, "No se pudo relanzar la auditoría.");
  }

  if (leadId) revalidatePath(`/leads/${leadId}`);
  LIST_ROUTES.forEach((route) => revalidatePath(route));
  return { ok: true, message: "Auditoría relanzada." };
}

/** Append a CRM note to a lead (detail sheet). */
export async function addNoteAction(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const leadId = String(formData.get("leadId") ?? "").trim();
  const text = String(formData.get("text") ?? "").trim();
  if (!leadId) {
    return { ok: false, error: "Falta el identificador del lead." };
  }
  if (!text) {
    return { ok: false, error: "La nota no puede estar vacía." };
  }

  try {
    await addLeadNoteRequest(leadId, text);
  } catch (error) {
    return toErrorState(error, "No se pudo guardar la nota.");
  }

  revalidatePath(`/leads/${leadId}`);
  return { ok: true, message: "Nota añadida." };
}

/**
 * Move a lead between board columns (kanban drag & drop). Direct-call server
 * action — no form — awaited by `useBoardLeads`, which owns the optimistic
 * update and reverts it when this returns `ok: false`.
 */
export async function moveLeadAction(
  leadId: string,
  status: string,
): Promise<ActionState> {
  if (!leadId || !status) {
    return { ok: false, error: "Faltan datos para mover el lead." };
  }

  try {
    await updateLeadStatusRequest(leadId, status);
  } catch (error) {
    return toErrorState(error, "No se pudo mover el lead.");
  }

  LIST_ROUTES.forEach((route) => revalidatePath(route));
  return { ok: true, message: "Estado actualizado." };
}

/** Save the pasted logo URL for a lead (detail sheet, media card image). */
export async function updateLogoAction(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const leadId = String(formData.get("leadId") ?? "").trim();
  const logoUrl = String(formData.get("logoUrl") ?? "").trim();
  if (!leadId) {
    return { ok: false, error: "Falta el identificador del lead." };
  }

  try {
    await updateLeadLogoRequest(leadId, logoUrl);
  } catch (error) {
    return toErrorState(error, "No se pudo guardar el logo.");
  }

  revalidatePath(`/leads/${leadId}`);
  LIST_ROUTES.forEach((route) => revalidatePath(route));
  return { ok: true, message: logoUrl ? "Logo actualizado." : "Logo eliminado." };
}

/** Move a lead to a new board stage (detail sheet). */
export async function changeStatusAction(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const leadId = String(formData.get("leadId") ?? "").trim();
  const status = String(formData.get("status") ?? "").trim();
  if (!leadId || !status) {
    return { ok: false, error: "Faltan datos para cambiar el estado." };
  }

  try {
    await updateLeadStatusRequest(leadId, status);
  } catch (error) {
    return toErrorState(error, "No se pudo cambiar el estado.");
  }

  revalidatePath(`/leads/${leadId}`);
  LIST_ROUTES.forEach((route) => revalidatePath(route));
  return { ok: true, message: "Estado actualizado." };
}
