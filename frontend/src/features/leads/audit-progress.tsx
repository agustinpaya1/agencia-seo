"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiUrl } from "@/lib/api-client";
import type { LeadDetail } from "./types";
import AuditTimeline from "./audit-timeline";

const POLL_INTERVAL_MS = 4000;

/**
 * Live variant of the audit timeline for a lead whose audit is running.
 *
 * Polls the backend detail endpoint (directly from the browser — same base URL
 * the PDF link uses) every few seconds and advances the stepper. When the
 * status leaves "audit", polling stops and `router.refresh()` re-renders the
 * server components so the final score/status replace the in-progress view.
 * Transient poll failures are ignored: the next tick retries.
 */
export default function AuditProgress({
  leadId,
  initialStage,
}: {
  leadId: string;
  initialStage?: string | null;
}) {
  const [stage, setStage] = useState<string | null>(initialStage ?? null);
  const [status, setStatus] = useState("audit");
  const router = useRouter();

  useEffect(() => {
    if (status !== "audit") return;

    const timer = setInterval(async () => {
      try {
        const res = await fetch(apiUrl(`/api/leads/${leadId}`), { cache: "no-store" });
        if (!res.ok) return;
        const lead: LeadDetail = await res.json();
        setStage(lead.current_stage ?? null);
        if (lead.status !== "audit") {
          setStatus(lead.status);
          router.refresh();
        }
      } catch {
        // backend momentarily unreachable; keep polling
      }
    }, POLL_INTERVAL_MS);

    return () => clearInterval(timer);
  }, [leadId, status, router]);

  return <AuditTimeline currentStage={stage} status={status} />;
}
