import { describe, expect, it } from "vitest";
import {
  EDITABLE_STATUSES,
  boardColumns,
  formatDate,
  formatScore,
  getStatusMeta,
  groupLeadsByStatus,
  STATUS_META,
} from "@/features/leads/lead-status";
import type { Lead } from "@/features/leads/types";

function makeLead(overrides: Partial<Lead> = {}): Lead {
  return {
    id: "l1",
    company: "Acme",
    domain: "acme.example",
    status: "lead",
    geo_score: 50,
    ...overrides,
  };
}

describe("getStatusMeta", () => {
  it("returns the Spanish label and tone for a known status", () => {
    expect(getStatusMeta("lead")).toEqual({
      label: "Cliente potencial",
      tone: "neutral",
    });
    expect(getStatusMeta("audit")).toEqual({ label: "Auditando", tone: "warning" });
    expect(getStatusMeta("completed")).toEqual({
      label: "Completado",
      tone: "success",
    });
  });

  it("falls back to the raw status string with a neutral tone", () => {
    expect(getStatusMeta("something-new")).toEqual({
      label: "something-new",
      tone: "neutral",
    });
  });
});

describe("EDITABLE_STATUSES", () => {
  it("excludes the engine-only statuses while STATUS_META still knows them", () => {
    expect(EDITABLE_STATUSES).not.toContain("unreachable");
    expect(EDITABLE_STATUSES).not.toContain("failed");
    expect(STATUS_META).toHaveProperty("unreachable");
    expect(STATUS_META).toHaveProperty("failed");
  });

  it("only contains statuses the backend PUT whitelist accepts", () => {
    expect(EDITABLE_STATUSES).toEqual([
      "lead",
      "audit",
      "proposal",
      "active",
      "completed",
      "churned",
      "lost",
    ]);
  });
});

describe("groupLeadsByStatus", () => {
  it("buckets leads by status preserving insertion order per bucket", () => {
    const a = makeLead({ id: "a", status: "lead" });
    const b = makeLead({ id: "b", status: "active" });
    const c = makeLead({ id: "c", status: "lead" });

    const groups = groupLeadsByStatus([a, b, c]);

    expect([...groups.keys()]).toEqual(["lead", "active"]);
    expect(groups.get("lead")?.map((l) => l.id)).toEqual(["a", "c"]);
    expect(groups.get("active")?.map((l) => l.id)).toEqual(["b"]);
  });

  it("returns an empty map for no leads", () => {
    expect(groupLeadsByStatus([]).size).toBe(0);
  });
});

describe("boardColumns", () => {
  it("always shows the core funnel, even with no leads", () => {
    expect(boardColumns([])).toEqual(["lead", "audit", "proposal", "active"]);
  });

  it("adds terminal columns only when they hold leads, in canonical order", () => {
    const leads = [
      makeLead({ id: "a", status: "failed" }),
      makeLead({ id: "b", status: "completed" }),
    ];
    expect(boardColumns(leads)).toEqual([
      "lead",
      "audit",
      "proposal",
      "active",
      "completed",
      "failed",
    ]);
  });

  it("hides statuses outside the canonical vocabulary (documents current behaviour)", () => {
    // A brand-new backend status would NOT get a column until it is added to
    // STATUS_ORDER in lead-status.ts — this test pins that contract.
    const leads = [makeLead({ id: "a", status: "negotiating" })];
    expect(boardColumns(leads)).toEqual(["lead", "audit", "proposal", "active"]);
  });
});

describe("formatDate", () => {
  it("returns empty string for missing values", () => {
    expect(formatDate(undefined)).toBe("");
    expect(formatDate(null)).toBe("");
    expect(formatDate("")).toBe("");
  });

  it("returns the raw value when it is not parseable as a date", () => {
    expect(formatDate("no-es-fecha")).toBe("no-es-fecha");
  });

  it("formats ISO dates as es-ES short dates", () => {
    expect(formatDate("2026-01-15")).toBe("15 ene 2026");
    expect(formatDate("2026-09-03T10:30:00Z")).toBe("03 sept 2026");
  });
});

describe("formatScore", () => {
  it("rounds to the nearest integer", () => {
    expect(formatScore(87.6)).toBe(88);
    expect(formatScore(87.4)).toBe(87);
  });

  it("treats missing scores as zero", () => {
    expect(formatScore(null)).toBe(0);
    expect(formatScore(undefined)).toBe(0);
  });
});
