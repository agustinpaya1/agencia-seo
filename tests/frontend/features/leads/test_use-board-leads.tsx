// @vitest-environment happy-dom
//
// The rest of the suite runs in node (pure logic + renderToStaticMarkup); this
// file needs a DOM because it exercises a stateful hook through renderHook.
//
// NOTE: the hook adopts `serverLeads` whenever its identity changes (that is
// how revalidated server props flow in), so every renderHook call below MUST
// receive a stable array via initialProps — building it inline in the render
// callback would create a fresh array per render and loop the sync effect.
import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  useBoardLeads,
  type LeadStatusUpdater,
} from "@/features/leads/use-board-leads";
import type { ActionState, Lead } from "@/features/leads/types";

function makeLeads(): Lead[] {
  return [
    { id: "a", company: "Acme", domain: "acme.example", status: "lead", geo_score: 40 },
    { id: "b", company: "Beta", domain: "beta.example", status: "active", geo_score: 80 },
  ];
}

function renderBoard(updater: LeadStatusUpdater, leads: Lead[] = makeLeads()) {
  return renderHook(
    ({ leads: serverLeads }: { leads: Lead[] }) => useBoardLeads(serverLeads, updater),
    { initialProps: { leads } },
  );
}

function statusOf(leads: Lead[], id: string): string | undefined {
  return leads.find((lead) => lead.id === id)?.status;
}

describe("useBoardLeads", () => {
  it("applies the move optimistically before the server answers", async () => {
    let resolve!: (value: ActionState) => void;
    const pending = new Promise<ActionState>((r) => {
      resolve = r;
    });
    const updater: LeadStatusUpdater = vi.fn(() => pending);
    const { result } = renderBoard(updater);

    act(() => {
      void result.current.moveLead("a", "proposal");
    });

    // The card already sits in the target column while the request is in flight.
    expect(statusOf(result.current.leads, "a")).toBe("proposal");
    expect(result.current.error).toBeNull();

    await act(async () => {
      resolve({ ok: true, message: "Estado actualizado." });
      await pending;
    });
    expect(statusOf(result.current.leads, "a")).toBe("proposal");
  });

  it("reverts the optimistic move and surfaces the error when the API fails", async () => {
    const updater: LeadStatusUpdater = vi.fn(async () => ({
      ok: false as const,
      error: "Invalid status",
    }));
    const { result } = renderBoard(updater);

    await act(async () => {
      await result.current.moveLead("a", "proposal");
    });

    expect(updater).toHaveBeenCalledWith("a", "proposal");
    expect(statusOf(result.current.leads, "a")).toBe("lead"); // back where it was
    expect(result.current.error).toBe("Invalid status");
  });

  it("reverts too when the action itself rejects (network down)", async () => {
    const updater: LeadStatusUpdater = vi.fn(async () => {
      throw new Error("fetch failed");
    });
    const { result } = renderBoard(updater);

    await act(async () => {
      await result.current.moveLead("a", "proposal");
    });

    expect(statusOf(result.current.leads, "a")).toBe("lead");
    expect(result.current.error).toBe("No se pudo contactar con el servidor.");
  });

  it("ignores no-op moves onto the same column", async () => {
    const updater: LeadStatusUpdater = vi.fn(async () => ({
      ok: true as const,
      message: "x",
    }));
    const { result } = renderBoard(updater);

    await act(async () => {
      await result.current.moveLead("a", "lead");
    });

    expect(updater).not.toHaveBeenCalled();
  });

  it("adopts fresh server props as the new base state", async () => {
    const updater: LeadStatusUpdater = vi.fn(async () => ({
      ok: true as const,
      message: "x",
    }));
    const { result, rerender } = renderBoard(updater);

    const refreshed = makeLeads().map((lead) =>
      lead.id === "a" ? { ...lead, status: "proposal" } : lead,
    );
    rerender({ leads: refreshed });

    await waitFor(() => {
      expect(statusOf(result.current.leads, "a")).toBe("proposal");
    });
  });
});
