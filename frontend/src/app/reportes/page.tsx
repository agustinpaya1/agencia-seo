import { BarChart3 } from "lucide-react";

export default function ReportesPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <BarChart3 className="w-16 h-16 text-muted-foreground mb-6" />
      <h1 className="text-3xl font-bold text-foreground mb-3">Reportes B2B</h1>
      <p className="text-muted-foreground max-w-md">
        Aquí se mostrarán los informes detallados de auditoría GEO-SEO para
        cada cliente potencial. Próximamente disponible.
      </p>
    </div>
  );
}
