"use client";

import { useActionState } from "react";
import { startAuditAction } from "@/features/audit/actions";
import { Loader2 } from "lucide-react";

export default function SearchForm() {
  const [state, formAction, isPending] = useActionState(startAuditAction, null);

  return (
    <div className="max-w-4xl mx-auto text-center w-full">
      <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500 drop-shadow-sm mb-6">
        Motor de Diagnóstico Agentic SEO
      </h1>
      
      <p className="text-lg md:text-xl text-slate-300 mb-12 max-w-2xl mx-auto leading-relaxed">
        Introduce la URL del prospecto B2B para analizar la indexabilidad en LLMs (ChatGPT, Perplexity) y arquitecturas Next.js.
      </p>

      <form action={formAction} className="relative max-w-2xl mx-auto">
        <div className="flex flex-col md:flex-row gap-4 items-center p-2 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md shadow-2xl transition-all duration-300 focus-within:ring-2 focus-within:ring-cyan-500/50">
          <input
            type="url"
            name="url"
            placeholder="https://ejemplo.com"
            required
            className="w-full bg-transparent border-none text-slate-100 text-lg px-6 py-4 focus:ring-0 focus:outline-none placeholder:text-slate-500"
            disabled={isPending}
          />
          <button
            type="submit"
            disabled={isPending}
            className={`flex items-center justify-center gap-2 whitespace-nowrap px-8 py-4 rounded-xl font-semibold text-white transition-all duration-300 ${
              isPending
                ? "bg-cyan-900/50 text-cyan-200 cursor-not-allowed"
                : "bg-cyan-600 hover:bg-cyan-500 hover:shadow-[0_0_20px_rgba(8,145,178,0.4)]"
            }`}
          >
            {isPending ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Iniciando análisis neuronal...</span>
              </>
            ) : (
              <span>Iniciar Diagnóstico</span>
            )}
          </button>
        </div>
      </form>

      {/* Feedback Messages */}
      <div className="mt-8 min-h-[60px]">
        {state?.success && (
          <div className="inline-block px-6 py-3 rounded-lg bg-teal-500/10 border border-teal-500/20 text-teal-400 font-medium animate-in fade-in slide-in-from-bottom-4 duration-500">
            {state.message}
          </div>
        )}
        {state?.error && (
          <div className="inline-block px-6 py-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 font-medium animate-in fade-in slide-in-from-bottom-4 duration-500">
            {state.error}
          </div>
        )}
      </div>
    </div>
  );
}
