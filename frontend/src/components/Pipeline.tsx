import React from "react";

interface Prospect {
  id: string;
  company: string;
  domain: string;
  status: string;
  geo_score: number;
  audit_date: string;
}

export default async function Pipeline() {
  let prospects: Prospect[] = [];

  try {
    const res = await fetch("http://127.0.0.1:8000/api/prospects", {
      next: { tags: ["prospects"] },
    });
    if (res.ok) {
      prospects = await res.json();
    }
  } catch (error) {
    console.error("Error fetching prospects:", error);
  }

  return (
    <div className="w-full">
      <h2 className="text-3xl font-bold text-white mb-8">Pipeline de Prospectos</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {prospects.map((prospect) => (
          <div
            key={prospect.id}
            className="bg-white/5 border border-white/10 rounded-xl p-6 hover:bg-white/10 transition-colors flex flex-col justify-between"
          >
            <div>
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-white">
                    {prospect.company || prospect.domain}
                  </h3>
                  <p className="text-sm text-slate-400">{prospect.domain}</p>
                </div>
                <div className="shrink-0 ml-4 flex items-center justify-center w-14 h-14 rounded-full bg-cyan-500/10 text-cyan-400 font-bold text-xl border border-cyan-500/30 shadow-[0_0_15px_rgba(8,145,178,0.2)]">
                  {prospect.geo_score ?? 0}
                </div>
              </div>

              <div className="mt-4 flex items-center space-x-2">
                {prospect.status === "audit" && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    Auditando...
                  </span>
                )}
                {prospect.status === "completed" && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Completado
                  </span>
                )}
                {prospect.status !== "audit" && prospect.status !== "completed" && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-slate-500/10 text-slate-300 border border-slate-500/20">
                    {prospect.status}
                  </span>
                )}
              </div>
            </div>
            
            {prospect.audit_date && (
              <div className="mt-6 text-xs text-slate-500">
                Última auditoría: {new Date(prospect.audit_date).toLocaleDateString()}
              </div>
            )}
          </div>
        ))}

        {prospects.length === 0 && (
          <div className="col-span-full text-center py-12 text-slate-400">
            No hay prospectos en el pipeline. Añade una URL arriba para comenzar.
          </div>
        )}
      </div>
    </div>
  );
}
