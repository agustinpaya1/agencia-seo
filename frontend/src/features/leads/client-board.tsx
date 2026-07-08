import { fetchLeads, isPrerenderInterrupt } from "@/lib/api-client";
import ClientBoardView from "./client-board-view";
import type { Lead } from "./types";

/**
 * Container: fetches the leads and hands them to the interactive
 * `ClientBoardView`. This is an uncached (dynamic) fetch, so it must render
 * inside a <Suspense> boundary — the pages that use it (app/page.tsx,
 * app/tablero/page.tsx) provide that boundary and its fallback.
 *
 * Network failures (backend down) degrade to an inline message instead of
 * crashing the route; genuine Next.js prerender control-flow errors are
 * re-thrown untouched so the build/stream behaves correctly.
 */
export default async function ClientBoard() {
  let leads: Lead[] = [];

  try {
    const data = await fetchLeads({ sort: "score" });
    leads = data.leads ?? [];
  } catch (error) {
    if (isPrerenderInterrupt(error)) throw error;
    return (
      <div className="rounded-xl border border-danger-500/30 bg-danger-500/10 p-6 text-sm text-danger-700">
        No se pudo cargar el tablero de clientes. Comprueba que el backend esté
        disponible.
      </div>
    );
  }

  return <ClientBoardView leads={leads} />;
}
