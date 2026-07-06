import { Suspense } from "react";
import { SearchForm } from "@/features/audit";
import { Pipeline } from "@/features/leads";

export default function Home() {
  return (
    <div className="flex flex-col items-center px-4 py-20 min-h-[80vh]">
      <SearchForm />

      <div className="w-full max-w-6xl mt-20 border-t border-white/10 pt-16">
        <Suspense fallback={<div className="text-center text-slate-400 py-10 animate-pulse">Cargando prospectos...</div>}>
          <Pipeline />
        </Suspense>
      </div>
    </div>
  );
}
