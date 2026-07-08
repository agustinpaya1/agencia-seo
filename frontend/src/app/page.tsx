import { Suspense } from "react";
import { ClientBoard, NewLeadButton } from "@/features/leads";

export default function Home() {
  return (
    <div className="flex flex-col px-4 py-10 min-h-[80vh]">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-foreground">
          Tablero de clientes
        </h1>
        <NewLeadButton />
      </div>
      <Suspense
        fallback={
          <div className="py-10 text-center text-muted-foreground animate-pulse">
            Cargando clientes potenciales…
          </div>
        }
      >
        <ClientBoard />
      </Suspense>
    </div>
  );
}
