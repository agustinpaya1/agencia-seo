import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { Badge } from "@/features/ui/badge";

// The tone map is Badge's only logic. renderToStaticMarkup keeps this a pure
// function check (tone in → classes out) with no DOM environment needed.
describe("Badge", () => {
  it("defaults to the neutral tone", () => {
    const html = renderToStaticMarkup(<Badge>Cliente potencial</Badge>);
    expect(html).toContain("bg-muted");
    expect(html).toContain("Cliente potencial");
  });

  it("resolves each tone to its class-map entry", () => {
    expect(renderToStaticMarkup(<Badge tone="success">x</Badge>)).toContain(
      "text-success-700",
    );
    expect(renderToStaticMarkup(<Badge tone="warning">x</Badge>)).toContain(
      "text-warning-700",
    );
    expect(renderToStaticMarkup(<Badge tone="danger">x</Badge>)).toContain(
      "text-danger-700",
    );
    expect(renderToStaticMarkup(<Badge tone="brand">x</Badge>)).toContain(
      "text-brand-700",
    );
  });

  it("merges a caller className after the tone classes", () => {
    const html = renderToStaticMarkup(<Badge className="ml-2">x</Badge>);
    expect(html).toMatch(/class="[^"]*ml-2/);
  });
});
