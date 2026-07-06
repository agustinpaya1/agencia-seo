import { BarChart3 } from "lucide-react";

export default function ReportesPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <BarChart3 className="w-16 h-16 text-slate-600 mb-6" />
      <h1 className="text-3xl font-bold text-white mb-3">Reportes B2B</h1>
      <p className="text-slate-400 max-w-md">
        Aquí se mostrarán los informes detallados de auditoría GEO-SEO para
        cada prospecto. Próximamente disponible.
      </p>
    </div>
  );
}
