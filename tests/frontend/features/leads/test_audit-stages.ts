import { describe, expect, it } from "vitest";
import {
  AUDIT_STAGES,
  stageState,
} from "@/features/leads/audit-stages";

const ids = AUDIT_STAGES.map((stage) => stage.id);

describe("AUDIT_STAGES", () => {
  it("mirrors the backend AuditStage enum in pipeline order", () => {
    expect(ids).toEqual([
      "fetch",
      "tech_stack",
      "technical_analysis",
      "content_analysis",
      "gate_1",
      "gate_2",
      "persistence",
    ]);
  });
});

describe("stageState while the audit is running (status=audit)", () => {
  it("marks earlier stages done, the current one active, the rest pending", () => {
    expect(stageState("fetch", "technical_analysis", "audit")).toBe("done");
    expect(stageState("tech_stack", "technical_analysis", "audit")).toBe("done");
    expect(stageState("technical_analysis", "technical_analysis", "audit")).toBe(
      "active",
    );
    expect(stageState("content_analysis", "technical_analysis", "audit")).toBe(
      "pending",
    );
    expect(stageState("persistence", "technical_analysis", "audit")).toBe("pending");
  });

  it("treats a missing current_stage as a just-started run", () => {
    expect(stageState("fetch", null, "audit")).toBe("active");
    expect(stageState("tech_stack", undefined, "audit")).toBe("pending");
  });

  it("treats an unknown current_stage like a just-started run (safe fallback)", () => {
    expect(stageState("fetch", "not-a-stage", "audit")).toBe("active");
  });
});

describe("stageState after the audit ended", () => {
  it("marks everything done on any finished status", () => {
    for (const status of ["completed", "active", "proposal", "lost"]) {
      for (const id of ids) {
        expect(stageState(id, "persistence", status)).toBe("done");
      }
    }
  });

  it("on failed/unreachable, the stage it stopped at never completes", () => {
    // Crashed during the technical block: fetch/tech_stack finished, the
    // current stage did not, and nothing after it ran.
    expect(stageState("fetch", "technical_analysis", "failed")).toBe("done");
    expect(stageState("tech_stack", "technical_analysis", "failed")).toBe("done");
    expect(stageState("technical_analysis", "technical_analysis", "failed")).toBe(
      "pending",
    );
    expect(stageState("gate_2", "technical_analysis", "failed")).toBe("pending");
    expect(stageState("fetch", "fetch", "unreachable")).toBe("pending");
  });
});
