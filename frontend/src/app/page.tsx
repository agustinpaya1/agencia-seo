import { cacheTag } from "next/cache";
import AuditForm from "./AuditForm";

type Prospect = {
  id: string;
  company: string;
  domain: string;
  status: string;
  geo_score: number;
  monthly_value: number;
  audit_date: string;
  has_pdf?: boolean;
};

type Stats = {
  total: number;
  active: number;
  mrr: number;
  pipeline: number;
  avg_score: number;
  avg_tier: string;
};

async function getProspects() {
  "use cache";
  cacheTag("prospects");
  try {
    const res = await fetch("http://127.0.0.1:5050/api/prospects", {
      cache: "no-store", // In Next.js 16, fetch is un-cached by default unless 'use cache' is used, but we enforce it just in case if the API changes.
    });
    if (!res.ok) return { prospects: [], stats: null };
    return await res.json();
  } catch (e) {
    console.error(e);
    return { prospects: [], stats: null };
  }
}

export default async function Dashboard() {
  const data = await getProspects();
  const prospects: Prospect[] = data.prospects || [];
  const stats: Stats | null = data.stats || null;

  const getTierColor = (score: number) => {
    if (score >= 80) return "text-emerald-400 bg-emerald-400/10 border-emerald-400/20";
    if (score >= 60) return "text-blue-400 bg-blue-400/10 border-blue-400/20";
    if (score >= 40) return "text-orange-400 bg-orange-400/10 border-orange-400/20";
    return "text-rose-500 bg-rose-500/10 border-rose-500/20";
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("es-ES", {
      style: "currency",
      currency: "EUR",
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-cyan-500/30">
      {/* Navbar */}
      <nav className="border-b border-white/10 bg-slate-950/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shadow-[0_0_15px_rgba(34,211,238,0.4)]">
              <span className="font-bold text-white tracking-tighter">AP</span>
            </div>
            <h1 className="text-xl font-semibold tracking-tight text-white">
              Agustín Payá <span className="text-cyan-400 font-light">— Agentic SEO</span>
            </h1>
          </div>
          <div className="text-xs text-slate-400 bg-slate-900 px-3 py-1.5 rounded-full border border-slate-800">
            {new Date().toLocaleDateString("es-ES", { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">
        
        {/* Top Action Bar */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
          <div>
            <h2 className="text-3xl font-bold text-white tracking-tight mb-1">Panel de Control</h2>
            <p className="text-slate-400 text-sm">Gestiona tus prospectos y lanza auditorías automatizadas.</p>
          </div>
          
          <AuditForm />
        </div>

        {/* KPIs */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-10">
            {[
              { label: "Prospectos", value: stats.total },
              { label: "Clientes Activos", value: stats.active, color: "text-emerald-400" },
              { label: "MRR", value: formatCurrency(stats.mrr), color: "text-cyan-400" },
              { label: "Pipeline", value: formatCurrency(stats.pipeline), color: "text-orange-400" },
              { label: "GEO Score Medio", value: `${stats.avg_score}/100`, color: getTierColor(stats.avg_score).split(" ")[0] },
            ].map((kpi, i) => (
              <div key={i} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-5 hover:bg-white/[0.07] transition-colors relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                  <svg className="w-12 h-12" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/></svg>
                </div>
                <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">{kpi.label}</div>
                <div className={`text-2xl font-bold ${kpi.color || 'text-white'}`}>{kpi.value}</div>
              </div>
            ))}
          </div>
        )}

        {/* Table */}
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl overflow-hidden shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/10 bg-white/[0.02]">
                  <th className="py-4 px-6 text-xs font-semibold text-slate-400 uppercase tracking-wider">Compañía</th>
                  <th className="py-4 px-6 text-xs font-semibold text-slate-400 uppercase tracking-wider">Estado</th>
                  <th className="py-4 px-6 text-xs font-semibold text-slate-400 uppercase tracking-wider">GEO Score</th>
                  <th className="py-4 px-6 text-xs font-semibold text-slate-400 uppercase tracking-wider">MRR</th>
                  <th className="py-4 px-6 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {prospects.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-slate-500">No hay prospectos. Inicia un nuevo diagnóstico.</td>
                  </tr>
                ) : (
                  prospects.map((p) => {
                    const tierClasses = getTierColor(p.geo_score);
                    // Disable link completely if there's no PDF, removing the href
                    const canExport = p.has_pdf || p.status === 'proposal';
                    return (
                      <tr key={p.id} className="hover:bg-white/[0.04] transition-colors group cursor-pointer">
                        <td className="py-4 px-6">
                          <div className="font-semibold text-slate-200 group-hover:text-cyan-400 transition-colors">{p.company}</div>
                          <div className="text-xs text-slate-500">{p.domain}</div>
                        </td>
                        <td className="py-4 px-6">
                          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700 capitalize">
                            {p.status}
                          </span>
                        </td>
                        <td className="py-4 px-6">
                          <div className="flex items-center gap-3">
                            <div className="w-full max-w-[120px] bg-slate-800 rounded-full h-2 overflow-hidden">
                              <div className={`h-full rounded-full ${tierClasses.split(' ')[1].replace('/10', '')}`} style={{ width: `${p.geo_score}%` }}></div>
                            </div>
                            <span className={`text-xs font-bold px-2 py-1 rounded-md border ${tierClasses}`}>
                              {p.geo_score}/100
                            </span>
                          </div>
                        </td>
                        <td className="py-4 px-6 font-medium text-slate-300">
                          {formatCurrency(p.monthly_value)}
                        </td>
                        <td className="py-4 px-6 text-right">
                          {canExport ? (
                            <a 
                              href={`http://localhost:5050/api/prospects/${p.id}/pdf`}
                              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500/20 border border-cyan-500/20"
                            >
                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                              Exportar PDF
                            </a>
                          ) : (
                            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-500 cursor-not-allowed">
                              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                              Exportar PDF
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
