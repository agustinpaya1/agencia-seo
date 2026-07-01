"use client";

import { useState, useTransition } from "react";
import { startAuditAction } from "./actions";

export default function AuditForm() {
  const [newUrl, setNewUrl] = useState("");
  const [isPending, startTransition] = useTransition();

  const handleAudit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUrl) return;
    
    startTransition(async () => {
      const res = await startAuditAction(newUrl);
      if (res.success) {
        setNewUrl("");
      } else {
        console.error(res.error);
      }
    });
  };

  return (
    <form onSubmit={handleAudit} className="flex w-full md:w-auto relative group">
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <svg className="h-5 w-5 text-slate-500 group-focus-within:text-cyan-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
      <input
        type="url"
        required
        placeholder="https://ejemplo.com"
        className="w-full md:w-80 pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-l-xl text-sm focus:outline-none focus:ring-1 focus:ring-cyan-400 focus:border-cyan-400 transition-all placeholder:text-slate-500 text-white"
        value={newUrl}
        onChange={(e) => setNewUrl(e.target.value)}
        disabled={isPending}
      />
      <button
        type="submit"
        disabled={isPending}
        className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold px-6 py-2.5 rounded-r-xl transition-colors flex items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
      >
        {isPending ? (
          <>
            <svg className="animate-spin h-4 w-4 text-slate-900" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            Analizando...
          </>
        ) : (
          "Nuevo Diagnóstico"
        )}
      </button>
    </form>
  );
}
