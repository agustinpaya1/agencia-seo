"use client";

import { useCallback, useState } from "react";
import type { ActionState, Lead } from "./types";

export type LeadStatusUpdater = (
  leadId: string,
  status: string,
) => Promise<ActionState>;

/**
 * Optimistic board state for the kanban drag & drop.
 *
 * `moveLead` applies the status change locally first (the card jumps to the
 * target column on drop), then awaits `updateStatus`; on failure the previous
 * state is restored and `error` carries a short message for an inline banner.
 *
 * `updateStatus` is injected (the board passes the `moveLeadAction` server
 * action) so this hook has no server-module imports and the revert path is
 * unit-testable with a stubbed updater — same DI shape the backend uses.
 */
export function useBoardLeads(serverLeads: Lead[], updateStatus: LeadStatusUpdater) {
  const [leads, setLeads] = useState(serverLeads);
  const [error, setError] = useState<string | null>(null);

  // A successful move revalidates the list routes, so fresh server props flow
  // down; adopt them as the new base state (covers concurrent edits too).
  // "Adjust state during render" pattern — not an effect — so the stale board
  // is never committed and the react-hooks/set-state-in-effect rule stays happy.
  const [prevServerLeads, setPrevServerLeads] = useState(serverLeads);
  if (prevServerLeads !== serverLeads) {
    setPrevServerLeads(serverLeads);
    setLeads(serverLeads);
  }

  const moveLead = useCallback(
    async (leadId: string, toStatus: string) => {
      const lead = leads.find((candidate) => candidate.id === leadId);
      if (!lead || lead.status === toStatus) return;

      const snapshot = leads;
      setError(null);
      setLeads(
        leads.map((candidate) =>
          candidate.id === leadId ? { ...candidate, status: toStatus } : candidate,
        ),
      );

      let result: ActionState;
      try {
        result = await updateStatus(leadId, toStatus);
      } catch {
        result = { ok: false, error: "No se pudo contactar con el servidor." };
      }

      if (result && !result.ok) {
        setLeads(snapshot);
        setError(result.error);
      }
    },
    [leads, updateStatus],
  );

  return { leads, moveLead, error };
}
