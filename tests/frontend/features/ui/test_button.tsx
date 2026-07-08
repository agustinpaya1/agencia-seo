import { describe, expect, it } from "vitest";
import { buttonClasses } from "@/features/ui/button";

// buttonClasses is the pure variant-map resolver behind <Button> (and behind
// styled <a> elements like the PDF download link), so asserting on it covers
// the component's class logic without rendering.
describe("buttonClasses", () => {
  it("defaults to the primary variant at md size", () => {
    const classes = buttonClasses();
    expect(classes).toContain("bg-brand-600");
    expect(classes).toContain("h-11");
  });

  it("resolves each variant to its map entry, never interpolating names", () => {
    expect(buttonClasses("secondary", "sm")).toContain("border-border");
    expect(buttonClasses("secondary", "sm")).not.toContain("bg-brand-600");
    expect(buttonClasses("ghost")).toContain("text-muted-foreground");
    expect(buttonClasses("danger")).toContain("bg-danger-600");
  });

  it("applies the size map", () => {
    expect(buttonClasses("primary", "sm")).toContain("h-9");
    expect(buttonClasses("primary", "md")).toContain("h-11");
  });

  it("appends the caller's className last so it can extend the recipe", () => {
    expect(buttonClasses("primary", "md", "w-full")).toMatch(/ w-full$/);
  });
});
