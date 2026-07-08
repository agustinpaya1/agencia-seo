import { Suspense } from "react";
import { ProjectsGrid } from "@/features/leads";

export default function ProyectosPage() {
  return (
    <div className="flex flex-col px-4 py-10 min-h-[80vh]">
      <h1 className="text-2xl font-bold text-foreground mb-2">Proyectos</h1>
      <p className="text-sm text-muted-foreground mb-6">
        Clientes activos con proyecto en marcha.
      </p>
      <Suspense
        fallback={
          <div className="py-10 text-center text-muted-foreground animate-pulse">
            Cargando proyectos…
          </div>
        }
      >
        <ProjectsGrid />
      </Suspense>
    </div>
  );
}
