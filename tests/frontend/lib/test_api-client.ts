import { afterEach, describe, expect, it, vi } from "vitest";
import {
  API_BASE_URL,
  ApiError,
  apiUrl,
  fetchLeads,
  isPrerenderInterrupt,
  leadPdfUrl,
  request,
  updateLeadStatusRequest,
} from "@/lib/api-client";

function stubFetch(response: Response) {
  const fetchMock = vi.fn(async () => response);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("URL builders", () => {
  it("prefixes paths with the API base URL", () => {
    expect(apiUrl("/api/leads")).toBe(`${API_BASE_URL}/api/leads`);
  });

  it("builds the browser-followable PDF URL for a lead", () => {
    expect(leadPdfUrl("abc123")).toBe(`${API_BASE_URL}/api/leads/abc123/pdf`);
  });
});

describe("request (via fetchLeads)", () => {
  it("hits /api/leads with no query string when there are no params", async () => {
    const fetchMock = stubFetch(jsonResponse({ leads: [] }));

    await fetchLeads();

    const [url] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(`${API_BASE_URL}/api/leads`);
  });

  it("serialises status and sort as query params", async () => {
    const fetchMock = stubFetch(jsonResponse({ leads: [] }));

    await fetchLeads({ status: "active", sort: "score" });

    const [url] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(`${API_BASE_URL}/api/leads?status=active&sort=score`);
  });

  it("always sends uncached JSON requests", async () => {
    const fetchMock = stubFetch(jsonResponse({ leads: [] }));

    await fetchLeads();

    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(init.cache).toBe("no-store");
    expect(init.headers).toMatchObject({ "Content-Type": "application/json" });
  });

  it("resolves with the parsed JSON body", async () => {
    const payload = { leads: [{ id: "x" }], stats: { total: 1 } };
    stubFetch(jsonResponse(payload));

    await expect(fetchLeads()).resolves.toEqual(payload);
  });

  it("maps a JSON error body to an ApiError carrying detail and status", async () => {
    stubFetch(jsonResponse({ detail: "lead no encontrado" }, 404));

    const error = await fetchLeads().catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).message).toBe("lead no encontrado");
    expect((error as ApiError).status).toBe(404);
    expect((error as ApiError).name).toBe("ApiError");
  });

  it("falls back to the HTTP status text when the error body is not JSON", async () => {
    stubFetch(
      new Response("<html>boom</html>", {
        status: 503,
        statusText: "Service Unavailable",
      }),
    );

    const error = await fetchLeads().catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).message).toBe("Service Unavailable");
    expect((error as ApiError).status).toBe(503);
  });
});

describe("request with caller-supplied init", () => {
  it("merges custom headers without losing the JSON Content-Type", async () => {
    const fetchMock = stubFetch(jsonResponse({ ok: true }));

    await request("/api/audit", {
      method: "POST",
      body: JSON.stringify({ url: "https://example.com" }),
      headers: { Authorization: "Bearer token-123" },
    });

    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(init.headers).toMatchObject({
      "Content-Type": "application/json",
      Authorization: "Bearer token-123",
    });
  });

  it("stays uncached even if a caller passes a cache mode", async () => {
    const fetchMock = stubFetch(jsonResponse({ ok: true }));

    await request("/api/leads", { cache: "force-cache" });

    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(init.cache).toBe("no-store");
  });
});

describe("mutators", () => {
  it("updateLeadStatusRequest PUTs the new status as JSON", async () => {
    const fetchMock = stubFetch(jsonResponse({ ok: true }));

    await updateLeadStatusRequest("abc123", "proposal");

    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(`${API_BASE_URL}/api/leads/abc123/status`);
    expect(init.method).toBe("PUT");
    expect(JSON.parse(init.body as string)).toEqual({ status: "proposal" });
  });
});

describe("isPrerenderInterrupt", () => {
  it("recognises the prerender fetch-rejection error by message", () => {
    const error = new Error(
      "During prerendering, fetch() rejects when the prerender is complete.",
    );
    expect(isPrerenderInterrupt(error)).toBe(true);
  });

  it("recognises the hanging-promise digest", () => {
    expect(isPrerenderInterrupt({ digest: "HANGING_PROMISE_REJECTION" })).toBe(true);
  });

  it("lets genuine runtime failures through", () => {
    expect(isPrerenderInterrupt(new Error("fetch failed"))).toBe(false);
    expect(isPrerenderInterrupt({ digest: "SOMETHING_ELSE" })).toBe(false);
    expect(isPrerenderInterrupt(null)).toBe(false);
    expect(isPrerenderInterrupt("string error")).toBe(false);
  });
});
