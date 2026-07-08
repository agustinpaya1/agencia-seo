import { Settings } from "lucide-react";

export default function ConfiguracionPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <Settings className="w-16 h-16 text-muted-foreground mb-6" />
      <h1 className="text-3xl font-bold text-foreground mb-3">Configuración</h1>
      <p className="text-muted-foreground max-w-md">
        Panel de configuración del motor de auditoría y preferencias de cuenta.
        Próximamente disponible.
      </p>
    </div>
  );
}
