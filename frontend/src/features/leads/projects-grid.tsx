import { fetchLeads, isPrerenderInterrupt } from "@/lib/api-client";
import { MediaCard } from "@/features/ui";
import type { Lead } from "./types";

/**
 * "Proyectos" is deliberately NOT a new backend entity: it is the leads that
 * already are active clients (status="active", see lead-status.ts), rendered
 * as media cards. Clicking one opens the same lead detail sheet, where the
 * audit timeline lives. Uncached fetch -> must render inside <Suspense>
 * (app/proyectos/page.tsx provides the boundary).
 */
export default async function ProjectsGrid() {
  let projects: Lead[] = [];

  try {
    const data = await fetchLeads({ status: "active", sort: "company" });
    projects = data.leads ?? [];
  } catch (error) {
    if (isPrerenderInterrupt(error)) throw error;
    return (
      <div className="rounded-xl border border-danger-500/30 bg-danger-500/10 p-6 text-sm text-danger-700">
        No se pudieron cargar los proyectos. Comprueba que el backend esté
        disponible.
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border p-12 text-center text-muted-foreground">
        No hay proyectos todavía. Un cliente potencial se convierte en proyecto
        al pasarlo a «Cliente activo» en el tablero.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-6">
      {projects.map((project) => (
        <MediaCard
          key={project.id}
          href={`/leads/${project.id}`}
          imageUrl={project.logo_url}
          title={project.company || project.domain}
          subtitle={project.domain}
        />
      ))}
    </div>
  );
}
