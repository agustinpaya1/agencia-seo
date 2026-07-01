"use server";

import { updateTag } from "next/cache";

export async function startAuditAction(url: string) {
  if (!url) return { error: "URL is required" };
  
  try {
    const res = await fetch("http://127.0.0.1:5050/api/audit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    
    if (res.ok) {
      updateTag("prospects");
      return { success: true };
    }
    return { error: "Failed to start audit" };
  } catch (e) {
    return { error: "Backend unreachable" };
  }
}
