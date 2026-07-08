import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { MediaCard, mediaCardInitials } from "@/features/ui/media-card";

// renderToStaticMarkup covers the render-time branches (image vs initials,
// selected classes, link vs div). The onError -> initials fallback is browser
// behaviour and stays untested here (would need jsdom + a failing image load).
describe("mediaCardInitials", () => {
  it("takes the first letter of the first two words, uppercased", () => {
    expect(mediaCardInitials("Circle Energy")).toBe("CE");
    expect(mediaCardInitials("acme")).toBe("A");
    expect(mediaCardInitials("uno dos tres")).toBe("UD");
  });

  it("falls back to ? for blank names", () => {
    expect(mediaCardInitials("   ")).toBe("?");
  });
});

describe("MediaCard", () => {
  it("renders the initials placeholder on brand-100 when there is no image", () => {
    const html = renderToStaticMarkup(
      <MediaCard title="Circle Energy" subtitle="circle.energy" />,
    );
    expect(html).toContain("CE");
    expect(html).toContain("bg-brand-100");
    expect(html).not.toContain("<img");
  });

  it("renders a cover image when imageUrl is set", () => {
    const html = renderToStaticMarkup(
      <MediaCard title="Acme" imageUrl="https://cdn.example.com/logo.png" />,
    );
    expect(html).toContain("<img");
    expect(html).toContain("https://cdn.example.com/logo.png");
    expect(html).toContain("object-cover");
  });

  it("clips content to the pronounced corner radius", () => {
    const html = renderToStaticMarkup(<MediaCard title="Acme" />);
    expect(html).toContain("overflow-hidden");
    expect(html).toContain("rounded-2xl");
  });

  it("applies the elevated shadow + 2px brand ring when selected", () => {
    const html = renderToStaticMarkup(<MediaCard title="Acme" selected />);
    expect(html).toContain("ring-brand-600");
    expect(html).toContain("shadow-xl");
  });

  it("renders as a link when href is given", () => {
    const html = renderToStaticMarkup(<MediaCard title="Acme" href="/leads/1" />);
    expect(html).toContain('href="/leads/1"');
  });
});
