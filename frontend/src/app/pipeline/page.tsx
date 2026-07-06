import { Suspense } from "react";
import { Pipeline } from "@/features/leads";

export default function PipelinePage() {
  return (
    <div className="flex flex-col px-4 py-10 min-h-[80vh]">
      <Suspense fallback={<div className="text-center text-slate-400 py-10 animate-pulse">Cargando pipeline...</div>}>
        <Pipeline />
      </Suspense>
    </div>
  );
}
