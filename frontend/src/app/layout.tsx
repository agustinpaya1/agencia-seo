import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Sidebar } from "@/features/ui";
import "./globals.css";

// Exposed as a CSS variable so Tailwind's `font-sans` (see --font-sans in
// globals.css) resolves to Inter, instead of pinning the class on <body>.
const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });

export const metadata: Metadata = {
  title: "Agustín Payá - Agentic SEO Dashboard",
  description: "Plataforma B2B para diagnósticos de posicionamiento IA",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Light theme by default — no `dark` class. A future toggle would add it
  // here (selector-based dark mode, see globals.css).
  return (
    <html lang="es" className={inter.variable}>
      <body className="min-h-screen flex font-sans antialiased bg-background text-foreground">
        <Sidebar />

        {/* Main content. min-w-0 is load-bearing: as a flex item, <main>
            defaults to min-width:auto, so a wide child (the kanban columns)
            would stretch it past the viewport and force a page-level
            horizontal scroll instead of scrolling inside the board. */}
        <main className="flex-1 min-w-0 p-8">
          {children}
        </main>
      </body>
    </html>
  );
}
