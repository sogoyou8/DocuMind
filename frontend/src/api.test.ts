import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, api } from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
});

function jsonResponse(payload: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => "application/json" },
    json: async () => payload,
  } as unknown as Response;
}

describe("D5 HTTP client", () => {
  it("keeps cookies and session CSRF for mutation", async () => {
    const mock = vi.fn().mockResolvedValue(jsonResponse({ authenticated: true }));
    vi.stubGlobal("fetch", mock);
    await api.login("documind-local", "secret", "csrf-token");
    const [path, init] = mock.mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/api/v1/session/login/");
    expect(init.credentials).toBe("same-origin");
    expect((init.headers as Record<string, string>)["X-CSRFToken"]).toBe("csrf-token");
    expect((init.body as string)).toContain("documind-local");
  });
  it("never fabricates a success from API errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ detail: "Interdit." }, 403)));
    await expect(api.analytics()).rejects.toMatchObject({
      status: 403, message: "Interdit.",
    });
  });
  it("does not set a multipart Content-Type for browser uploads", async () => {
    const mock = vi.fn().mockResolvedValue(jsonResponse({ id: "123" }, 201));
    vi.stubGlobal("fetch", mock);
    await api.upload(new File(["a,b\n1,2\n"], "test.csv"), "csrf");
    const [, init] = mock.mock.calls[0] as [string, RequestInit];
    const headers = init.headers as Record<string, string>;
    expect(headers["Content-Type"]).toBeUndefined();
    expect(init.body).toBeInstanceOf(FormData);
  });
  it("preserves exact API error type and status", () => {
    const error = new ApiError("Erreur réelle.", 500);
    expect(error.status).toBe(500);
    expect(error.message).toBe("Erreur réelle.");
  });
});
