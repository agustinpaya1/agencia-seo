import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Sidebar } from "@/features/ui";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Agustín Payá - Agentic SEO Dashboard",
  description: "Plataforma B2B para diagnósticos de posicionamiento IA",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className={`${inter.className} min-h-screen flex antialiased`}>
        <Sidebar />

        {/* Main Content */}
        <main className="flex-1 p-8">
          {children}
        </main>
      </body>
    </html>
  );
}
