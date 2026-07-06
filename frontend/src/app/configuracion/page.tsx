import { Settings } from "lucide-react";

export default function ConfiguracionPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <Settings className="w-16 h-16 text-slate-600 mb-6" />
      <h1 className="text-3xl font-bold text-white mb-3">Configuración</h1>
      <p className="text-slate-400 max-w-md">
        Panel de configuración del motor de auditoría y preferencias de cuenta.
        Próximamente disponible.
      </p>
    </div>
  );
}
