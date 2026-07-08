import { describe, expect, it } from "vitest";
import { cn } from "@/lib/cn";

describe("cn", () => {
  it("joins truthy classes with single spaces", () => {
    expect(cn("a", "b", "c")).toBe("a b c");
  });

  it("drops falsy values so conditionals can be written inline", () => {
    expect(cn("base", false && "active", null, undefined, "")).toBe("base");
  });

  it("returns an empty string when nothing survives", () => {
    expect(cn()).toBe("");
    expect(cn(false, null, undefined)).toBe("");
  });
});
