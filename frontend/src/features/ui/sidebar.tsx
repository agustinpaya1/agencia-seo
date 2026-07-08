import Link from "next/link";
import {
  LayoutDashboard,
  SquareKanban,
  FolderKanban,
  BarChart3,
  Settings,
} from "lucide-react";

const navLinkClasses =
  "flex items-center gap-3 px-4 py-3 rounded-lg text-muted-foreground " +
  "hover:text-foreground hover:bg-muted transition-colors";

export default function Sidebar() {
  return (
    <aside className="w-64 flex flex-col bg-card border-r border-border sticky top-0 h-screen">
      <div className="p-6 border-b border-border">
        <h1 className="text-lg font-semibold tracking-tight text-foreground">
          Agustín Payá | <br />
          {/* Monochrome brand gradient (700→500 centred on the brand blue):
              keeps the logo lively without a second hue in the palette. */}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-700 to-brand-500 font-bold">
            Agentic SEO
          </span>
        </h1>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        <Link href="/" className={navLinkClasses}>
          <LayoutDashboard className="w-5 h-5" />
          <span className="font-medium">Dashboard</span>
        </Link>
        <Link href="/tablero" className={navLinkClasses}>
          <SquareKanban className="w-5 h-5" />
          <span className="font-medium">Tablero de clientes</span>
        </Link>
        <Link href="/proyectos" className={navLinkClasses}>
          <FolderKanban className="w-5 h-5" />
          <span className="font-medium">Proyectos</span>
        </Link>
        <Link href="/reportes" className={navLinkClasses}>
          <BarChart3 className="w-5 h-5" />
          <span className="font-medium">Reportes B2B</span>
        </Link>
        <Link href="/configuracion" className={navLinkClasses}>
          <Settings className="w-5 h-5" />
          <span className="font-medium">Configuración</span>
        </Link>
      </nav>
    </aside>
  );
}
