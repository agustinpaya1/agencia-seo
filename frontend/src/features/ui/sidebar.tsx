import Link from "next/link";
import { LayoutDashboard, GitMerge, BarChart3, Settings } from "lucide-react";

export default function Sidebar() {
  return (
    <aside className="w-64 flex flex-col bg-white/5 backdrop-blur-xl border-r border-white/10 sticky top-0 h-screen">
      <div className="p-6 border-b border-white/10">
        <h1 className="text-lg font-semibold tracking-tight text-slate-200">
          Agustín Payá | <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-orange-400 font-bold">
            Agentic SEO
          </span>
        </h1>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        <Link href="/" className="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-all">
          <LayoutDashboard className="w-5 h-5" />
          <span className="font-medium">Dashboard</span>
        </Link>
        <Link href="/pipeline" className="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-all">
          <GitMerge className="w-5 h-5" />
          <span className="font-medium">Pipeline</span>
        </Link>
        <Link href="/reportes" className="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-all">
          <BarChart3 className="w-5 h-5" />
          <span className="font-medium">Reportes B2B</span>
        </Link>
        <Link href="/configuracion" className="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-all">
          <Settings className="w-5 h-5" />
          <span className="font-medium">Configuración</span>
        </Link>
      </nav>
    </aside>
  );
}
